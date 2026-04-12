from __future__ import annotations

import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from stock_news.deterministic_analysis import generate_python_report
from stock_news.utils import safe_symbol_name, write_json


def _parse_json_text(text: str) -> dict[str, Any]:
    stripped = str(text or "").strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```[a-zA-Z0-9_-]*\n", "", stripped)
        stripped = re.sub(r"\n```$", "", stripped)
    return json.loads(stripped)


def build_codex_prompt(item: dict[str, Any], news_context: dict[str, Any], *, analysis_date: str, run_id: str) -> str:
    payload = {
        "analysis_date": analysis_date,
        "run_id": run_id,
        "shortlist_item": item,
        "cached_news_context": news_context,
    }
    return f"""
You are generating a comparable daily breakout-strategy stock analysis.

Important instructions:
- Use web search to verify the recent stock-specific news and catalysts.
- Prefer concrete dates and recent sources.
- Focus on what matters for a breakout or recovery setup over the next 1 to 4 weeks.
- Return JSON only, matching the provided schema exactly.
- Set `analysis_error` to null when the analysis succeeds.
- For each source, include `title`, `url`, `publisher`, and `published_at`; use null for unknown values.
- If evidence is weak or mixed, say so explicitly instead of forcing a bullish conclusion.
- Keep each bullet concise and specific.

Structured context:
{json.dumps(payload, indent=2, default=str)}

Answer these questions in the schema:
- Why did the stock fall in the recent period?
- What signs of recovery are visible?
- Which near-term catalysts matter?
- Which risks or invalidation signals matter most?
- Does the news flow support or conflict with the breakout thesis?
- What is the overall breakout stance, with a normalized score and confidence?
""".strip()


def build_codex_summary_prompt(
    item: dict[str, Any],
    news_context: dict[str, Any],
    python_report: dict[str, Any],
    *,
    analysis_date: str,
    run_id: str,
) -> str:
    payload = {
        "analysis_date": analysis_date,
        "run_id": run_id,
        "shortlist_item": item,
        "cached_news_context": news_context,
        "python_report": python_report,
    }
    return f"""
You are refining a Python-generated breakout report.

Important instructions:
- Use the Python report as the source of truth for structure, scores, and the factual evidence already assembled.
- You may lightly improve phrasing and resolve tension between signals, but do not invent new facts or new sources.
- Prefer the local structured evidence over broad narrative.
- Keep the tone analytical and compact.
- Return JSON only, matching the provided schema exactly.
- Set `analysis_error` to null when the synthesis succeeds.

Structured context:
{json.dumps(payload, indent=2, default=str)}

Produce only:
- a concise `summary`
- a concise `news_support_explanation`
- a concise `breakout_thesis`
""".strip()


def fallback_report(item: dict[str, Any], *, analysis_date: str, error: str) -> dict[str, Any]:
    return {
        "symbol": item.get("symbol"),
        "company_name": item.get("company_name"),
        "analysis_date": analysis_date,
        "analysis_mode": "codex-full-fallback",
        "summary": f"Codex analysis was unavailable: {error}",
        "recent_weakness": [],
        "recovery_signals": [],
        "catalysts": [],
        "risks": [],
        "news_support": {
            "stance": "unknown",
            "explanation": "No structured Codex response was generated.",
        },
        "breakout_stance": {
            "label": "insufficient_data",
            "score_0_to_100": 0,
            "confidence": "low",
            "thesis": "The automated Codex step failed, so no reliable breakout stance is available.",
        },
        "sources": [],
        "analysis_error": error,
    }


def fallback_summary(*, error: str) -> dict[str, Any]:
    return {
        "summary": "",
        "news_support_explanation": "",
        "breakout_thesis": "",
        "analysis_error": error,
    }


def run_python_analysis(
    item: dict[str, Any],
    *,
    news_context: dict[str, Any],
    output_path: Path,
    force: bool = False,
) -> dict[str, Any]:
    if output_path.exists() and not force:
        return _parse_json_text(output_path.read_text(encoding="utf-8"))

    report = generate_python_report(item, news_context)
    write_json(output_path, report)
    return report


def run_codex_analysis(
    item: dict[str, Any],
    *,
    news_context: dict[str, Any],
    schema_path: Path,
    output_path: Path,
    repo_root: Path,
    force: bool = False,
) -> dict[str, Any]:
    analysis_date = datetime.now(timezone.utc).date().isoformat()
    if output_path.exists() and not force:
        return _parse_json_text(output_path.read_text(encoding="utf-8"))

    prompt = build_codex_prompt(item, news_context, analysis_date=analysis_date, run_id=str(item.get("run_id")))
    output_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "codex",
        "--search",
        "exec",
        "--sandbox",
        "read-only",
        "--color",
        "never",
        "--ephemeral",
        "--output-schema",
        str(schema_path),
        "-o",
        str(output_path),
        "-",
    ]

    try:
        completed = subprocess.run(
            cmd,
            input=prompt,
            text=True,
            capture_output=True,
            cwd=str(repo_root),
            check=False,
        )
    except Exception as exc:
        report = fallback_report(
            item,
            analysis_date=analysis_date,
            error=f"codex_invocation_failed:{type(exc).__name__}:{exc}",
        )
        write_json(output_path, report)
        return report

    if completed.returncode != 0:
        report = fallback_report(
            item,
            analysis_date=analysis_date,
            error=f"codex_exit_{completed.returncode}: {completed.stderr.strip() or completed.stdout.strip()}",
        )
        write_json(output_path, report)
        return report

    try:
        report = _parse_json_text(output_path.read_text(encoding="utf-8"))
    except Exception as exc:
        fallback = fallback_report(
            item,
            analysis_date=analysis_date,
            error=f"invalid_json:{type(exc).__name__}:{exc}",
        )
        write_json(output_path, fallback)
        return fallback

    return report


def run_codex_summary(
    item: dict[str, Any],
    *,
    news_context: dict[str, Any],
    python_report: dict[str, Any],
    schema_path: Path,
    output_path: Path,
    repo_root: Path,
    force: bool = False,
) -> dict[str, Any]:
    analysis_date = datetime.now(timezone.utc).date().isoformat()
    if output_path.exists() and not force:
        return _parse_json_text(output_path.read_text(encoding="utf-8"))

    prompt = build_codex_summary_prompt(
        item,
        news_context,
        python_report,
        analysis_date=analysis_date,
        run_id=str(item.get("run_id")),
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "codex",
        "--search",
        "exec",
        "--sandbox",
        "read-only",
        "--color",
        "never",
        "--ephemeral",
        "--output-schema",
        str(schema_path),
        "-o",
        str(output_path),
        "-",
    ]

    try:
        completed = subprocess.run(
            cmd,
            input=prompt,
            text=True,
            capture_output=True,
            cwd=str(repo_root),
            check=False,
        )
    except Exception as exc:
        summary = fallback_summary(error=f"codex_summary_invocation_failed:{type(exc).__name__}:{exc}")
        write_json(output_path, summary)
        return summary

    if completed.returncode != 0:
        summary = fallback_summary(
            error=f"codex_summary_exit_{completed.returncode}: {completed.stderr.strip() or completed.stdout.strip()}",
        )
        write_json(output_path, summary)
        return summary

    try:
        summary = _parse_json_text(output_path.read_text(encoding="utf-8"))
    except Exception as exc:
        fallback = fallback_summary(error=f"invalid_json:{type(exc).__name__}:{exc}")
        write_json(output_path, fallback)
        return fallback

    return summary


def merge_codex_summary(report: dict[str, Any], synthesis: dict[str, Any]) -> dict[str, Any]:
    merged = json.loads(json.dumps(report))
    synthesis_error = synthesis.get("analysis_error")
    if not synthesis_error:
        if synthesis.get("summary"):
            merged["summary"] = synthesis["summary"]
        if synthesis.get("news_support_explanation"):
            merged.setdefault("news_support", {})
            merged["news_support"]["explanation"] = synthesis["news_support_explanation"]
        if synthesis.get("breakout_thesis"):
            merged.setdefault("breakout_stance", {})
            merged["breakout_stance"]["thesis"] = synthesis["breakout_thesis"]
        merged["analysis_mode"] = "hybrid"
        merged["analysis_error"] = None
    else:
        merged["analysis_mode"] = "python"
        merged["codex_summary_error"] = synthesis_error
    return merged


def analysis_report_name(symbol: str) -> str:
    return f"{safe_symbol_name(symbol)}.json"
