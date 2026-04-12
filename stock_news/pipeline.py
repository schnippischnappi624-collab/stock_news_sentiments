from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from stock_news.analysis import (
    analysis_report_name,
    merge_codex_summary,
    run_codex_analysis,
    run_codex_summary,
    run_python_analysis,
)
from stock_news.feed_discovery import discover_latest_feeds, download_feed_text
from stock_news.feed_parser import parse_feed_text
from stock_news.models import FeedFile
from stock_news.news import load_news_context, update_company_profiles, update_market_news_history, update_news_history
from stock_news.paths import get_paths
from stock_news.render import render_analysis_markdown, render_best_candidates, render_dashboard, render_project_readme
from stock_news.shortlist import build_shortlist, shortlist_to_frame
from stock_news.utils import manifest_hash, read_json, replace_dir_contents, safe_symbol_name, write_json


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _run_layout(run_dir: Path) -> dict[str, Path]:
    return {
        "run_dir": run_dir,
        "feeds_dir": run_dir / "feeds",
        "parsed_dir": run_dir / "parsed",
        "parsed_tables_dir": run_dir / "parsed" / "tables",
        "shortlist_dir": run_dir / "shortlist",
        "analysis_dir": run_dir / "analysis",
        "analysis_json_dir": run_dir / "analysis" / "json",
        "analysis_evidence_dir": run_dir / "analysis" / "evidence",
        "analysis_codex_dir": run_dir / "analysis" / "codex",
        "analysis_markdown_dir": run_dir / "analysis" / "markdown",
        "dashboard_path": run_dir / "dashboard.md",
        "best_candidates_path": run_dir / "best_candidates.md",
        "source_manifest_path": run_dir / "source_manifest.json",
        "run_summary_path": run_dir / "run_summary.json",
    }


def _ensure_layout(run_dir: Path) -> dict[str, Path]:
    layout = _run_layout(run_dir)
    for key, path in layout.items():
        if key.endswith("_dir"):
            path.mkdir(parents=True, exist_ok=True)
    return layout


def _load_manifest(run_id: str | None = None) -> dict[str, Any]:
    paths = get_paths()
    manifest_path = paths.active_manifest_path if run_id is None else paths.daily_run_dir(run_id) / "source_manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"missing manifest: {manifest_path}")
    return read_json(manifest_path)


def _write_table_csvs(parsed_payload: dict[str, Any], parsed_tables_dir: Path, stem: str) -> list[str]:
    written = []
    for table in parsed_payload.get("tables", []):
        df = pd.DataFrame(table.get("rows", []), columns=table.get("columns", []))
        out_path = parsed_tables_dir / f"{stem}__{table['table_key']}.csv"
        df.to_csv(out_path, index=False)
        written.append(str(out_path))
    return written


def _sync_latest_outputs(run_id: str) -> None:
    paths = get_paths()
    run_dir = paths.daily_run_dir(run_id)
    layout = _run_layout(run_dir)
    paths.latest_dir.mkdir(parents=True, exist_ok=True)

    for name in ["feeds", "parsed", "shortlist", "analysis"]:
        src = layout[f"{name}_dir"]
        dest = paths.latest_dir / name
        replace_dir_contents(src, dest)

    shutil.copy2(layout["dashboard_path"], paths.latest_dir / "dashboard.md")
    shutil.copy2(layout["best_candidates_path"], paths.latest_dir / "best_candidates.md")
    shutil.copy2(layout["source_manifest_path"], paths.latest_dir / "source_manifest.json")
    shutil.copy2(layout["run_summary_path"], paths.latest_dir / "run_summary.json")


def fetch_feeds(base_url: str, *, force: bool = False) -> dict[str, Any]:
    paths = get_paths()
    paths.ensure_base_dirs()

    feeds = discover_latest_feeds(base_url)
    if not feeds:
        raise RuntimeError("no feed files discovered from source index")

    manifest_items = [feed.to_dict() for feed in feeds]
    digest = manifest_hash(manifest_items)
    feed_dates = sorted({feed.feed_date for feed in feeds})
    primary_date = max(feed_dates)
    run_id = f"{primary_date}_{digest[:8]}"

    run_dir = paths.daily_run_dir(run_id)
    layout = _ensure_layout(run_dir)

    for feed in feeds:
        out_path = layout["feeds_dir"] / feed.filename
        if force or not out_path.exists():
            out_path.write_text(download_feed_text(feed.url), encoding="utf-8")

    manifest = {
        "run_id": run_id,
        "manifest_hash": digest,
        "base_url": base_url,
        "feed_dates": feed_dates,
        "selected_at_utc": _now_utc(),
        "feeds": manifest_items,
    }
    write_json(layout["source_manifest_path"], manifest)
    write_json(paths.active_manifest_path, manifest)
    return manifest


def parse_feeds(run_id: str | None = None) -> dict[str, Any]:
    manifest = _load_manifest(run_id)
    paths = get_paths()
    layout = _ensure_layout(paths.daily_run_dir(manifest["run_id"]))

    parsed_outputs = []
    for feed_payload in manifest["feeds"]:
        feed = FeedFile(**feed_payload)
        raw_path = layout["feeds_dir"] / feed.filename
        if not raw_path.exists():
            raise FileNotFoundError(f"missing raw feed file: {raw_path}")
        parsed = parse_feed_text(feed, raw_path.read_text(encoding="utf-8"))
        stem = Path(feed.filename).stem
        out_path = layout["parsed_dir"] / f"{stem}.json"
        write_json(out_path, parsed)
        csv_paths = _write_table_csvs(parsed, layout["parsed_tables_dir"], stem)
        parsed_outputs.append(
            {
                "feed": feed.to_dict(),
                "table_count": parsed.get("table_count", 0),
                "table_csv_paths": csv_paths,
                "parsed_json_path": str(out_path),
            }
        )

    summary = {
        "ok": True,
        "run_id": manifest["run_id"],
        "parsed_files": len(parsed_outputs),
        "outputs": parsed_outputs,
    }
    write_json(layout["parsed_dir"] / "parse_summary.json", summary)
    return summary


def _load_parsed_payloads(run_id: str) -> list[dict[str, Any]]:
    paths = get_paths()
    parsed_dir = paths.daily_run_dir(run_id) / "parsed"
    payloads = []
    for json_path in sorted(parsed_dir.glob("*.json")):
        if json_path.name == "parse_summary.json":
            continue
        payloads.append(read_json(json_path))
    return payloads


def build_shortlist_step(run_id: str | None = None, *, extra_candidates: int = 10) -> dict[str, Any]:
    manifest = _load_manifest(run_id)
    paths = get_paths()
    layout = _ensure_layout(paths.daily_run_dir(manifest["run_id"]))
    payloads = _load_parsed_payloads(manifest["run_id"])
    shortlist = build_shortlist(payloads, extra_candidates=extra_candidates)
    shortlist["run_id"] = manifest["run_id"]
    shortlist["manifest_hash"] = manifest["manifest_hash"]
    shortlist["feed_dates"] = manifest["feed_dates"]

    json_path = layout["shortlist_dir"] / "shortlist.json"
    csv_path = layout["shortlist_dir"] / "shortlist.csv"
    write_json(json_path, shortlist)
    shortlist_to_frame(shortlist).to_csv(csv_path, index=False)
    return shortlist


def update_news_cache_step(run_id: str | None = None) -> dict[str, Any]:
    manifest = _load_manifest(run_id)
    paths = get_paths()
    layout = _ensure_layout(paths.daily_run_dir(manifest["run_id"]))
    shortlist = read_json(layout["shortlist_dir"] / "shortlist.json")
    symbols = [item["symbol"] for item in shortlist.get("symbols", []) if item.get("symbol")]
    symbol_summary = update_news_history(
        symbols,
        headlines_dir=paths.news_headlines_dir,
        sentiment_dir=paths.news_daily_sentiment_dir,
        api_key_path=paths.finnhub_key_path,
        provider="auto",
        overlap_days=3,
        min_fetch_minutes=5,
        sleep_s=0.05,
    )
    market_summary = update_market_news_history(
        headlines_path=paths.market_headlines_path,
        sentiment_path=paths.market_daily_sentiment_path,
        min_fetch_minutes=30,
        sleep_s=0.05,
    )
    profile_summary = update_company_profiles(
        symbols,
        profiles_dir=paths.company_profiles_dir,
        min_refresh_hours=24 * 7,
        sleep_s=0.05,
    )
    summary = dict(symbol_summary)
    summary["ok"] = bool(symbol_summary.get("ok", False) and market_summary.get("ok", False) and profile_summary.get("ok", False))
    summary["market_news"] = market_summary
    summary["company_profiles"] = profile_summary
    write_json(layout["shortlist_dir"] / "news_cache_summary.json", summary)
    return summary


def run_analysis_step(
    run_id: str | None = None,
    *,
    max_news: int = 15,
    force: bool = False,
    analysis_mode: str = "hybrid",
) -> dict[str, Any]:
    manifest = _load_manifest(run_id)
    paths = get_paths()
    layout = _ensure_layout(paths.daily_run_dir(manifest["run_id"]))
    shortlist = read_json(layout["shortlist_dir"] / "shortlist.json")

    full_schema_path = paths.schemas_dir / "breakout_analysis.schema.json"
    summary_schema_path = paths.schemas_dir / "breakout_summary.schema.json"
    analysis_mode = str(analysis_mode or "hybrid").strip().lower()
    if analysis_mode not in {"python", "hybrid", "codex-full"}:
        analysis_mode = "hybrid"

    results = []
    for item in shortlist.get("symbols", []):
        symbol = item.get("symbol")
        if not symbol:
            continue
        item_with_run = dict(item)
        item_with_run["run_id"] = manifest["run_id"]
        news_context = load_news_context(
            symbol,
            headlines_dir=paths.news_headlines_dir,
            sentiment_dir=paths.news_daily_sentiment_dir,
            market_headlines_path=paths.market_headlines_path,
            market_sentiment_path=paths.market_daily_sentiment_path,
            profiles_dir=paths.company_profiles_dir,
            max_articles=max_news,
        )
        report_json_path = layout["analysis_json_dir"] / analysis_report_name(symbol)
        evidence_path = layout["analysis_evidence_dir"] / analysis_report_name(symbol)
        codex_path = layout["analysis_codex_dir"] / analysis_report_name(symbol)

        report = None
        if report_json_path.exists() and not force:
            cached_report = read_json(report_json_path)
            cached_mode = str(cached_report.get("analysis_mode") or "").strip().lower()
            if cached_mode == analysis_mode:
                report = cached_report

        if report is None:
            python_report = run_python_analysis(
                item_with_run,
                news_context=news_context,
                output_path=evidence_path,
                force=force,
            )

            if analysis_mode == "python":
                report = python_report
            elif analysis_mode == "hybrid":
                synthesis = run_codex_summary(
                    item_with_run,
                    news_context=news_context,
                    python_report=python_report,
                    schema_path=summary_schema_path,
                    output_path=codex_path,
                    repo_root=paths.root,
                    force=force,
                )
                report = merge_codex_summary(python_report, synthesis)
            else:
                report = run_codex_analysis(
                    item_with_run,
                    news_context=news_context,
                    schema_path=full_schema_path,
                    output_path=codex_path,
                    repo_root=paths.root,
                    force=force,
                )
                report["analysis_mode"] = "codex-full"
                report["scorecard"] = python_report.get("scorecard")
                report["evidence"] = python_report.get("evidence")

            write_json(report_json_path, report)

        markdown = render_analysis_markdown(report, item)
        markdown_path = layout["analysis_markdown_dir"] / f"{safe_symbol_name(symbol)}.md"
        markdown_path.write_text(markdown, encoding="utf-8")
        results.append(report)

    dashboard = render_dashboard(
        manifest,
        shortlist,
        results,
        report_prefix="analysis/markdown",
    )
    layout["dashboard_path"].write_text(dashboard, encoding="utf-8")
    best_candidates = render_best_candidates(
        manifest,
        shortlist,
        results,
        report_prefix="analysis/markdown",
        top_n=15,
    )
    layout["best_candidates_path"].write_text(best_candidates, encoding="utf-8")
    project_readme = render_project_readme(manifest, shortlist, results, best_candidates_top_n=15)
    (paths.root / "README.md").write_text(project_readme, encoding="utf-8")

    summary = {
        "ok": all(not report.get("analysis_error") for report in results),
        "run_id": manifest["run_id"],
        "analysis_mode": analysis_mode,
        "symbols_total": len(shortlist.get("symbols", [])),
        "reports_written": len(results),
        "reports_failed": sum(1 for report in results if report.get("analysis_error")),
        "generated_at_utc": _now_utc(),
    }
    write_json(layout["analysis_dir"] / "analysis_summary.json", summary)
    return summary


def run_codex_analysis_step(run_id: str | None = None, *, max_news: int = 15, force: bool = False) -> dict[str, Any]:
    return run_analysis_step(run_id, max_news=max_news, force=force, analysis_mode="codex-full")


def _write_run_summary(
    run_id: str,
    *,
    shortlist: dict[str, Any],
    news_summary: dict[str, Any],
    analysis_summary: dict[str, Any],
) -> dict[str, Any]:
    paths = get_paths()
    layout = _ensure_layout(paths.daily_run_dir(run_id))
    summary = {
        "ok": bool(news_summary.get("ok", False) and analysis_summary.get("ok", False)),
        "run_id": run_id,
        "generated_at_utc": _now_utc(),
        "shortlist_size": len(shortlist.get("symbols", [])),
        "entry_ready_count": shortlist.get("entry_ready_count", 0),
        "candidate_count": shortlist.get("candidate_count", 0),
        "news_summary": news_summary,
        "analysis_summary": analysis_summary,
    }
    write_json(layout["run_summary_path"], summary)
    return summary


def fetch_feeds_command(*, base_url: str, force: bool) -> int:
    manifest = fetch_feeds(base_url, force=force)
    print(json.dumps({"ok": True, "run_id": manifest["run_id"], "feeds": len(manifest["feeds"])}, indent=2))
    return 0


def parse_feeds_command(*, run_id: str | None) -> int:
    summary = parse_feeds(run_id)
    print(json.dumps(summary, indent=2))
    return 0


def build_shortlist_command(*, run_id: str | None, extra_candidates: int) -> int:
    shortlist = build_shortlist_step(run_id, extra_candidates=extra_candidates)
    print(
        json.dumps(
            {
                "ok": True,
                "run_id": shortlist["run_id"],
                "symbols": len(shortlist.get("symbols", [])),
                "entry_ready_count": shortlist.get("entry_ready_count"),
                "candidate_count": shortlist.get("candidate_count"),
            },
            indent=2,
        )
    )
    return 0


def update_news_cache_command(*, run_id: str | None) -> int:
    summary = update_news_cache_step(run_id)
    print(json.dumps(summary, indent=2))
    return 0 if summary.get("ok", False) else 1


def run_analysis_command(*, run_id: str | None, max_news: int, force: bool, analysis_mode: str) -> int:
    summary = run_analysis_step(run_id, max_news=max_news, force=force, analysis_mode=analysis_mode)
    print(json.dumps(summary, indent=2))
    return 0


def run_codex_analysis_command(*, run_id: str | None, max_news: int, force: bool, analysis_mode: str = "codex-full") -> int:
    return run_analysis_command(run_id=run_id, max_news=max_news, force=force, analysis_mode=analysis_mode)


def daily_run_command(*, base_url: str, force: bool, extra_candidates: int, max_news: int, analysis_mode: str = "hybrid") -> int:
    paths = get_paths()
    paths.ensure_base_dirs()

    manifest = fetch_feeds(base_url, force=force)
    previous = read_json(paths.last_manifest_path) if paths.last_manifest_path.exists() else {}
    if (
        not force
        and previous.get("manifest_hash") == manifest["manifest_hash"]
        and previous.get("status") == "ok"
        and (paths.daily_run_dir(previous.get("run_id", "")).exists())
    ):
        print(
            json.dumps(
                {
                    "ok": True,
                    "skipped": True,
                    "reason": "latest remote feed set already processed",
                    "run_id": previous.get("run_id"),
                },
                indent=2,
            )
        )
        return 0

    parse_feeds(manifest["run_id"])
    shortlist = build_shortlist_step(manifest["run_id"], extra_candidates=extra_candidates)
    news_summary = update_news_cache_step(manifest["run_id"])
    analysis_summary = run_analysis_step(
        manifest["run_id"],
        max_news=max_news,
        force=force,
        analysis_mode=analysis_mode,
    )
    run_summary = _write_run_summary(
        manifest["run_id"],
        shortlist=shortlist,
        news_summary=news_summary,
        analysis_summary=analysis_summary,
    )
    _sync_latest_outputs(manifest["run_id"])
    write_json(
        paths.last_manifest_path,
        {
            "run_id": manifest["run_id"],
            "manifest_hash": manifest["manifest_hash"],
            "status": "ok" if run_summary.get("ok") else "failed",
            "completed_at_utc": _now_utc(),
            "feeds": manifest["feeds"],
            "feed_dates": manifest["feed_dates"],
        },
    )
    print(json.dumps(run_summary, indent=2))
    return 0 if run_summary.get("ok") else 1
