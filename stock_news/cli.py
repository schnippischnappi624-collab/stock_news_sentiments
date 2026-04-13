from __future__ import annotations

import argparse
from pathlib import Path

from stock_news.pipeline import (
    build_shortlist_command,
    daily_run_command,
    fetch_feeds_command,
    parse_feeds_command,
    run_analysis_command,
    run_codex_analysis_command,
    update_news_cache_command,
)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="stock-news")
    sub = ap.add_subparsers(dest="cmd", required=True)
    region_choices = ["EU", "US"]

    p_daily = sub.add_parser("daily-run", help="Run the full daily breakout analysis workflow.")
    p_daily.add_argument("--force", action="store_true")
    p_daily.add_argument("--base-url", default="https://stock.sdc-fried.de/")
    p_daily.add_argument("--region", choices=region_choices, default=None)
    p_daily.add_argument("--extra-candidates", type=int, default=10)
    p_daily.add_argument("--max-news", type=int, default=15)
    p_daily.add_argument("--analysis-mode", default="hybrid", choices=["python", "hybrid", "codex-full"])

    p_fetch = sub.add_parser("fetch-feeds", help="Discover and download the latest US and EU feeds.")
    p_fetch.add_argument("--force", action="store_true")
    p_fetch.add_argument("--base-url", default="https://stock.sdc-fried.de/")
    p_fetch.add_argument("--region", choices=region_choices, default=None)

    p_parse = sub.add_parser("parse-feeds", help="Parse downloaded feed files into normalized artifacts.")
    p_parse.add_argument("--run-id", default=None)
    p_parse.add_argument("--region", choices=region_choices, default=None)

    p_shortlist = sub.add_parser("build-shortlist", help="Build the daily breakout shortlist.")
    p_shortlist.add_argument("--run-id", default=None)
    p_shortlist.add_argument("--region", choices=region_choices, default=None)
    p_shortlist.add_argument("--extra-candidates", type=int, default=10)

    p_news = sub.add_parser("update-news-cache", help="Update local news caches for the latest shortlist.")
    p_news.add_argument("--run-id", default=None)
    p_news.add_argument("--region", choices=region_choices, default=None)

    p_codex = sub.add_parser("run-codex-analysis", help="Run Codex analysis and render reports.")
    p_codex.add_argument("--run-id", default=None)
    p_codex.add_argument("--region", choices=region_choices, default=None)
    p_codex.add_argument("--max-news", type=int, default=15)
    p_codex.add_argument("--force", action="store_true")
    p_codex.add_argument("--analysis-mode", default="codex-full", choices=["python", "hybrid", "codex-full"])

    p_analysis = sub.add_parser("run-analysis", help="Run Python-first analysis with optional Codex synthesis.")
    p_analysis.add_argument("--run-id", default=None)
    p_analysis.add_argument("--region", choices=region_choices, default=None)
    p_analysis.add_argument("--max-news", type=int, default=15)
    p_analysis.add_argument("--force", action="store_true")
    p_analysis.add_argument("--analysis-mode", default="hybrid", choices=["python", "hybrid", "codex-full"])

    return ap


def main(argv: list[str] | None = None) -> int:
    ap = build_parser()
    args = ap.parse_args(argv)

    if args.cmd == "fetch-feeds":
        return fetch_feeds_command(base_url=args.base_url, force=bool(args.force), region=args.region)
    if args.cmd == "parse-feeds":
        return parse_feeds_command(run_id=args.run_id, region=args.region)
    if args.cmd == "build-shortlist":
        return build_shortlist_command(run_id=args.run_id, region=args.region, extra_candidates=int(args.extra_candidates))
    if args.cmd == "update-news-cache":
        return update_news_cache_command(run_id=args.run_id, region=args.region)
    if args.cmd == "run-analysis":
        return run_analysis_command(
            run_id=args.run_id,
            region=args.region,
            max_news=int(args.max_news),
            force=bool(args.force),
            analysis_mode=str(args.analysis_mode),
        )
    if args.cmd == "run-codex-analysis":
        return run_codex_analysis_command(
            run_id=args.run_id,
            region=args.region,
            max_news=int(args.max_news),
            force=bool(args.force),
            analysis_mode=str(args.analysis_mode),
        )
    if args.cmd == "daily-run":
        return daily_run_command(
            base_url=args.base_url,
            force=bool(args.force),
            region=args.region,
            extra_candidates=int(args.extra_candidates),
            max_news=int(args.max_news),
            analysis_mode=str(args.analysis_mode),
        )

    raise SystemExit(f"unsupported command: {args.cmd}")
