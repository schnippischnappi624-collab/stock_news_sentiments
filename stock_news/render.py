from __future__ import annotations

from typing import Any

from stock_news.fx import convert_to_eur
from stock_news.regions import REGION_ORDER, normalize_region
from stock_news.utils import safe_symbol_name


def _metric_num(value: Any, *, digits: int = 2) -> str | None:
    if value in {None, ""}:
        return None
    try:
        return f"{float(value):,.{digits}f}"
    except (TypeError, ValueError):
        return str(value)


def _execution_lines(item: dict[str, Any], *, eur_rates_context: dict[str, Any] | None = None) -> list[str]:
    metrics = item.get("metrics", {}) or {}
    currency = str(item.get("currency") or "").strip()

    def fmt_money(value: Any, *, digits: int = 2) -> str | None:
        text = _metric_num(value, digits=digits)
        if text is None:
            return None
        label = f"{text} {currency}".strip()
        eur_value = convert_to_eur(value, currency, eur_rates_context)
        if currency.upper() != "EUR" and eur_value is not None:
            label += f" ({eur_value:,.{digits}f} EUR)"
        return label

    lines: list[str] = []

    current_price = fmt_money(metrics.get("close"))
    if current_price:
        lines.append(f"- Current price: `{current_price}`")

    entry_limit = fmt_money(metrics.get("entry_limit"))
    if entry_limit:
        lines.append(f"- Entry limit: `{entry_limit}`")

    stop_init = fmt_money(metrics.get("stop_init"))
    if stop_init:
        lines.append(f"- Initial stop: `{stop_init}`")

    hh20_prev = fmt_money(metrics.get("hh20_prev"))
    if hh20_prev:
        lines.append(f"- Prior 20d high trigger: `{hh20_prev}`")

    tp_2r = fmt_money(metrics.get("tp_2r"))
    if tp_2r:
        lines.append(f"- 2R target: `{tp_2r}`")

    tp_3r = fmt_money(metrics.get("tp_3r"))
    if tp_3r:
        lines.append(f"- 3R target: `{tp_3r}`")

    r_dist = fmt_money(metrics.get("r_dist"))
    if r_dist:
        lines.append(f"- Risk distance: `{r_dist}`")

    return lines


def _section_points(items: list[dict[str, Any]], *, default_message: str) -> list[str]:
    if not items:
        return [f"- {default_message}"]
    lines = []
    for item in items:
        point = item.get("point") or item.get("name") or item.get("summary") or str(item)
        confidence = item.get("confidence")
        if confidence:
            lines.append(f"- {point} ({confidence})")
        else:
            lines.append(f"- {point}")
    return lines


def _confidence_rank(value: Any) -> int:
    lookup = {"high": 3, "medium": 2, "low": 1}
    return lookup.get(str(value or "").strip().lower(), 0)


def _top_items(items: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    indexed = list(enumerate(items or []))
    ranked = sorted(indexed, key=lambda pair: (-_confidence_rank(pair[1].get("confidence")), pair[0]))
    return [item for _, item in ranked[:limit]]


def _compact_points(items: list[dict[str, Any]], *, limit: int, default_message: str) -> list[str]:
    return _section_points(_top_items(items, limit), default_message=default_message)


def _top_score_drivers(components: list[dict[str, Any]], *, limit: int = 4) -> list[dict[str, Any]]:
    ranked = sorted(
        components or [],
        key=lambda component: (-abs(int(component.get("points") or 0)), str(component.get("label") or "")),
    )
    return ranked[:limit]


def _ranked_candidate_rows(shortlist: dict[str, Any], analysis_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    lookup = {row["symbol"]: row for row in analysis_rows}
    ranked_items = []
    for item in shortlist.get("symbols", []):
        symbol = item.get("symbol")
        report = lookup.get(symbol, {})
        stance = report.get("breakout_stance", {}) or {}
        ranked_items.append(
            {
                "symbol": symbol,
                "company_name": item.get("company_name"),
                "bucket": item.get("selection_bucket"),
                "display_rank": item.get("display_rank"),
                "score": stance.get("score_0_to_100", 0),
                "confidence": stance.get("confidence", "n/a"),
                "stance": stance.get("label", "unknown"),
            }
        )

    ranked_items.sort(
        key=lambda row: (
            -int(row.get("score") or 0),
            0 if row.get("bucket") == "entry_ready" else 1,
            int(row.get("display_rank") or 9999),
            str(row.get("symbol") or ""),
        )
    )
    return ranked_items


def _section_lookup(sections: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    lookup: dict[str, dict[str, Any]] = {}
    for section in sections:
        region = normalize_region(section.get("region"))
        if region:
            lookup[region] = section
    return lookup


def _best_candidate_section_lines(
    section: dict[str, Any] | None,
    *,
    region: str,
    report_prefix: str,
    top_n: int,
    heading: str,
) -> list[str]:
    lines = [heading, ""]
    if section is None:
        lines.append(f"No {region} snapshot is available yet.")
        return lines

    manifest = section.get("manifest", {}) or {}
    shortlist = section.get("shortlist", {}) or {}
    analysis_rows = section.get("analysis_rows", []) or []
    report_prefix = str(section.get("report_prefix") or report_prefix)
    top_items = _ranked_candidate_rows(shortlist, analysis_rows)[: int(max(1, top_n))]

    lines.extend(
        [
            f"- Run ID: `{manifest.get('run_id', 'n/a')}`",
            f"- Feed dates: `{', '.join(manifest.get('feed_dates', [])) or 'n/a'}`",
            f"- Symbols analyzed: `{len(shortlist.get('symbols', []))}`",
            "",
            "| Rank | Symbol | Company | Bucket | Score | Confidence | Breakout stance |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
    )

    for idx, row in enumerate(top_items, start=1):
        symbol = row.get("symbol")
        lines.append(
            "| {rank} | [{symbol}]({report_prefix}/{file_name}.md) | {company} | {bucket} | {score} | {confidence} | {stance} |".format(
                rank=idx,
                symbol=symbol,
                report_prefix=report_prefix,
                file_name=safe_symbol_name(symbol),
                company=row.get("company_name") or "Unknown Company",
                bucket=row.get("bucket") or "n/a",
                score=row.get("score", "n/a"),
                confidence=row.get("confidence", "n/a"),
                stance=row.get("stance", "unknown"),
            )
        )

    if not top_items:
        lines.extend(["", f"No scored {region} candidates were available in this snapshot."])

    return lines


def _dashboard_section_lines(
    section: dict[str, Any] | None,
    *,
    region: str,
    report_prefix: str,
    heading: str,
) -> list[str]:
    lines = [heading, ""]
    if section is None:
        lines.append(f"No {region} snapshot is available yet.")
        return lines

    manifest = section.get("manifest", {}) or {}
    shortlist = section.get("shortlist", {}) or {}
    analysis_rows = section.get("analysis_rows", []) or []
    report_prefix = str(section.get("report_prefix") or report_prefix)
    lookup = {row["symbol"]: row for row in analysis_rows}

    lines.extend(
        [
            f"- Run ID: `{manifest.get('run_id', 'n/a')}`",
            f"- Feed dates: `{', '.join(manifest.get('feed_dates', [])) or 'n/a'}`",
            f"- Symbols analyzed: `{len(shortlist.get('symbols', []))}`",
            "",
            "| Rank | Symbol | Bucket | Breakout stance | Score | Confidence | Report |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
    )

    for item in shortlist.get("symbols", []):
        symbol = item.get("symbol")
        report = lookup.get(symbol, {})
        stance = report.get("breakout_stance", {}) or {}
        lines.append(
            "| {rank} | {symbol} | {bucket} | {stance_label} | {score} | {confidence} | [report]({report_prefix}/{file_name}.md) |".format(
                rank=item.get("display_rank"),
                symbol=symbol,
                bucket=item.get("selection_bucket"),
                stance_label=stance.get("label", "unknown"),
                score=stance.get("score_0_to_100", "n/a"),
                confidence=stance.get("confidence", "n/a"),
                report_prefix=report_prefix,
                file_name=safe_symbol_name(symbol),
            )
        )

    if not shortlist.get("symbols"):
        lines.extend(["", f"No {region} shortlist symbols were generated for this snapshot."])

    return lines


def render_analysis_markdown(
    report: dict[str, Any],
    item: dict[str, Any],
    *,
    eur_rates_context: dict[str, Any] | None = None,
) -> str:
    stance = report.get("breakout_stance", {}) or {}
    news_support = report.get("news_support", {}) or {}
    coverage = report.get("coverage", {}) or {}
    metrics = item.get("metrics", {}) or {}
    scorecard = report.get("scorecard", {}) or {}
    evidence = report.get("evidence", {}) or {}
    news_evidence = evidence.get("news", {}) or {}
    market_evidence = evidence.get("market", {}) or {}
    market_overlay = report.get("market_overlay", {}) or {}
    thesis = stance.get("thesis") or "No thesis generated."
    top_drivers = _top_score_drivers(scorecard.get("components", []) or [], limit=4)
    show_market_overlay = bool(
        market_overlay.get("supportive_effects")
        or market_overlay.get("adverse_effects")
        or (market_overlay.get("exposures") or [])
    )

    lines = [
        f"# {item.get('symbol')} - {item.get('company_name') or 'Unknown Company'}",
        "",
        f"- Breakout stance: `{stance.get('label', 'unknown')}`",
        f"- Score: `{stance.get('score_0_to_100', 'n/a')}`",
        f"- Confidence: `{stance.get('confidence', 'n/a')}`",
        f"- Bucket: `{item.get('selection_bucket')}`",
    ]
    execution_lines = _execution_lines(item, eur_rates_context=eur_rates_context)
    if execution_lines:
        lines.extend(execution_lines)

    lines.extend(
        [
            "",
            "## Investment View",
            report.get("summary", "No summary generated."),
            "",
            f"- Thesis: {thesis}",
            "",
            "## What Matters",
            *_compact_points(
                report.get("recovery_signals", []),
                limit=2,
                default_message="No concrete recovery signal was identified.",
            ),
            "",
            "## Risks / Invalidation",
            *_compact_points(
                report.get("risks", []),
                limit=2,
                default_message="No major risk or invalidation signal was identified.",
            ),
            "",
            "## Catalysts",
            *_compact_points(
                report.get("catalysts", []),
                limit=2,
                default_message="No near-term catalyst was identified.",
            ),
            "",
            "## News Read",
            f"- Stance: `{news_support.get('stance', 'unknown')}`",
            f"- Explanation: {news_support.get('explanation', 'No explanation generated.')}",
            "",
            "## Key Levels",
            f"- Volume anomaly: `{metrics.get('vol_anom', 'n/a')}`",
            f"- Close: `{metrics.get('close', 'n/a')}`",
            f"- Prior 20d high: `{metrics.get('hh20_prev', 'n/a')}`",
            f"- ATR14: `{metrics.get('atr14', 'n/a')}`",
            "",
            "## Why This Score",
        ]
    )

    if not top_drivers:
        lines.append("- No explicit score driver was recorded.")
    else:
        for component in top_drivers:
            label = component.get("label") or "Unnamed component"
            points = component.get("points")
            value = component.get("value")
            if value is not None:
                lines.append(f"- {label}: `{points:+}` (value: `{value}`)")
            elif points is not None:
                lines.append(f"- {label}: `{points:+}`")
            else:
                lines.append(f"- {label}")

    lines.extend(
        [
            "",
            "## Coverage",
            f"- Stock-news coverage quality: `{coverage.get('quality', news_evidence.get('coverage_quality', 'n/a'))}`",
            f"- Stock-specific articles scored: `{news_evidence.get('article_count', 0)}`",
            f"- Market headlines scanned: `{market_evidence.get('article_count', 0)}`",
        ]
    )

    market_weight = coverage.get("market_overlay_weight", market_overlay.get("weight_scale"))
    if market_weight is not None:
        lines.append(f"- Macro overlay weight used in scoring: `{market_weight}`")

    if show_market_overlay:
        lines.extend(
            [
                "",
                "## Market Overlay",
                f"- Exposures: `{', '.join(market_overlay.get('exposures', [])) or 'none'}`",
                f"- Matched supportive macro effects: `{market_overlay.get('supportive_effects', 0)}`",
                f"- Matched adverse macro effects: `{market_overlay.get('adverse_effects', 0)}`",
            ]
        )
        if market_overlay.get("effective_supportive_effects") is not None or market_overlay.get("effective_adverse_effects") is not None:
            lines.extend(
                [
                    f"- Effective supportive effects after coverage weighting: `{market_overlay.get('effective_supportive_effects', 0)}`",
                    f"- Effective adverse effects after coverage weighting: `{market_overlay.get('effective_adverse_effects', 0)}`",
                ]
            )

    lines.extend(
        [
            "",
            "## Sources",
        ]
    )

    sources = report.get("sources", []) or []
    if not sources:
        lines.append("- No explicit sources captured.")
    else:
        for source in sources:
            title = source.get("title") or source.get("url") or "Untitled source"
            url = source.get("url") or ""
            published = source.get("published_at") or source.get("date") or "unknown date"
            lines.append(f"- [{title}]({url}) - {published}")

    if report.get("analysis_error"):
        lines.extend(["", "## Analysis Error", f"- {report['analysis_error']}"])

    return "\n".join(lines).strip() + "\n"


def render_dashboard(
    manifest: dict[str, Any],
    shortlist: dict[str, Any],
    analysis_rows: list[dict[str, Any]],
    *,
    report_prefix: str,
) -> str:
    lines = [
        "# Daily Breakout News Analysis",
        "",
        f"- Run ID: `{manifest.get('run_id')}`",
        f"- Feed dates: `{', '.join(manifest.get('feed_dates', []))}`",
        f"- Symbols analyzed: `{len(shortlist.get('symbols', []))}`",
        "",
        "| Rank | Symbol | Bucket | Stance | Score | Confidence | Report |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]

    lookup = {row["symbol"]: row for row in analysis_rows}
    for item in shortlist.get("symbols", []):
        symbol = item.get("symbol")
        report = lookup.get(symbol, {})
        stance = report.get("breakout_stance", {}) or {}
        report_name = f"{report_prefix}/{safe_symbol_name(symbol)}.md"
        lines.append(
            "| {rank} | {symbol} | {bucket} | {stance_label} | {score} | {confidence} | [report]({report_name}) |".format(
                rank=item.get("display_rank"),
                symbol=symbol,
                bucket=item.get("selection_bucket"),
                stance_label=stance.get("label", "unknown"),
                score=stance.get("score_0_to_100", "n/a"),
                confidence=stance.get("confidence", "n/a"),
                report_name=report_name,
            )
        )

    if not shortlist.get("symbols"):
        lines.extend(["", "No shortlist symbols were generated for this run."])

    return "\n".join(lines).strip() + "\n"


def render_best_candidates(
    manifest: dict[str, Any],
    shortlist: dict[str, Any],
    analysis_rows: list[dict[str, Any]],
    *,
    report_prefix: str,
    top_n: int = 15,
) -> str:
    ranked_items = _ranked_candidate_rows(shortlist, analysis_rows)
    top_items = ranked_items[: int(max(1, top_n))]

    lines = [
        "# Best Scoring Candidates",
        "",
        f"- Run ID: `{manifest.get('run_id')}`",
        f"- Feed dates: `{', '.join(manifest.get('feed_dates', []))}`",
        f"- Table size: `{len(top_items)}`",
        "",
        "| Rank | Symbol | Company | Bucket | Score | Confidence | Breakout stance |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]

    for idx, row in enumerate(top_items, start=1):
        symbol = row.get("symbol")
        report_name = f"{report_prefix}/{safe_symbol_name(symbol)}.md"
        lines.append(
            "| {rank} | [{symbol}]({report_name}) | {company} | {bucket} | {score} | {confidence} | {stance} |".format(
                rank=idx,
                symbol=symbol,
                report_name=report_name,
                company=row.get("company_name") or "Unknown Company",
                bucket=row.get("bucket") or "n/a",
                score=row.get("score", "n/a"),
                confidence=row.get("confidence", "n/a"),
                stance=row.get("stance", "unknown"),
            )
        )

    if not top_items:
        lines.extend(["", "No scored candidates were available for this run."])

    return "\n".join(lines).strip() + "\n"


def render_project_readme(
    manifest: dict[str, Any],
    shortlist: dict[str, Any],
    analysis_rows: list[dict[str, Any]],
    *,
    best_candidates_top_n: int = 15,
) -> str:
    top_items = _ranked_candidate_rows(shortlist, analysis_rows)[: int(max(1, best_candidates_top_n))]

    lines = [
        "# stock_news_sentiments",
        "",
        "Auto-generated daily breakout dashboard for the latest committed run.",
        "",
        f"- Run ID: `{manifest.get('run_id')}`",
        f"- Feed dates: `{', '.join(manifest.get('feed_dates', []))}`",
        f"- Symbols analyzed: `{len(shortlist.get('symbols', []))}`",
        "",
        "Quick links:",
        "- [Best scoring candidates](latest/best_candidates.md)",
        "- [Full dashboard](latest/dashboard.md)",
        "- [Latest detailed analyses](latest/analysis/markdown/)",
        "- [Operational notes](docs/OPERATIONS.md)",
        "",
        "## Best Scoring Candidates",
        "",
        "| Rank | Symbol | Company | Bucket | Score | Confidence | Breakout stance |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]

    for idx, row in enumerate(top_items, start=1):
        symbol = row.get("symbol")
        lines.append(
            "| {rank} | [{symbol}](latest/analysis/markdown/{file_name}.md) | {company} | {bucket} | {score} | {confidence} | {stance} |".format(
                rank=idx,
                symbol=symbol,
                file_name=safe_symbol_name(symbol),
                company=row.get("company_name") or "Unknown Company",
                bucket=row.get("bucket") or "n/a",
                score=row.get("score", "n/a"),
                confidence=row.get("confidence", "n/a"),
                stance=row.get("stance", "unknown"),
            )
        )

    if not top_items:
        lines.extend(["", "No scored candidates were available for this run."])

    lines.extend(
        [
            "",
            "## Column Guide",
            "",
            "- `Breakout stance`: the repo's normalized final investing view for the setup after blending feed/technical evidence with any matched news and macro overlay.",
            "  Worst to best: `avoid` -> `fragile_watch` -> `mixed_watch` -> `constructive_watch` -> `constructive_bullish`",
            "- `Confidence`: how much usable evidence supports the current stance.",
            "  Worst to best: `low` -> `medium` -> `high`",
            "- `Bucket`: where the symbol sits in the shortlist built from the source website feeds.",
            "  Worst to best: `candidate` -> `entry_ready`",
        ]
    )

    return "\n".join(lines).strip() + "\n"


def render_regional_dashboard(sections: list[dict[str, Any]]) -> str:
    section_lookup = _section_lookup(sections)
    available_regions = [region for region in REGION_ORDER if section_lookup.get(region)]
    total_symbols = sum(len((section_lookup.get(region) or {}).get("shortlist", {}).get("symbols", [])) for region in REGION_ORDER)

    lines = [
        "# Latest Regional Breakout Dashboard",
        "",
        f"- Regions available: `{', '.join(available_regions) or 'none'}`",
        f"- Symbols analyzed: `{total_symbols}`",
    ]

    for region in REGION_ORDER:
        lines.extend(
            [
                "",
                *_dashboard_section_lines(
                    section_lookup.get(region),
                    region=region,
                    report_prefix=f"{region.lower()}/analysis/markdown",
                    heading=f"## {region} Daily Dashboard",
                ),
            ]
        )

    return "\n".join(lines).strip() + "\n"


def render_regional_best_candidates(sections: list[dict[str, Any]], *, top_n: int = 15) -> str:
    section_lookup = _section_lookup(sections)
    available_regions = [region for region in REGION_ORDER if section_lookup.get(region)]

    lines = [
        "# Latest Regional Best Candidates",
        "",
        f"- Regions available: `{', '.join(available_regions) or 'none'}`",
        "",
    ]

    for region in REGION_ORDER:
        lines.extend(
            [
                *_best_candidate_section_lines(
                    section_lookup.get(region),
                    region=region,
                    report_prefix=f"{region.lower()}/analysis/markdown",
                    top_n=top_n,
                    heading=f"## {region} Best Scoring Candidates",
                ),
                "",
            ]
        )

    return "\n".join(lines).strip() + "\n"


def render_regional_project_readme(sections: list[dict[str, Any]], *, best_candidates_top_n: int = 15) -> str:
    section_lookup = _section_lookup(sections)
    available_regions = [region for region in REGION_ORDER if section_lookup.get(region)]
    total_symbols = sum(len((section_lookup.get(region) or {}).get("shortlist", {}).get("symbols", [])) for region in REGION_ORDER)
    feed_dates = sorted(
        {
            feed_date
            for section in section_lookup.values()
            for feed_date in (section.get("manifest", {}) or {}).get("feed_dates", [])
        }
    )

    lines = [
        "# stock_news_sentiments",
        "",
        "Auto-generated daily breakout dashboard for the latest committed regional runs.",
        "",
        f"- Regions available: `{', '.join(available_regions) or 'none'}`",
        f"- Feed dates: `{', '.join(feed_dates) or 'n/a'}`",
        f"- Symbols analyzed: `{total_symbols}`",
        "",
        "Quick links:",
        "- [Regional best candidates](latest/best_candidates.md)",
        "- [Regional dashboard](latest/dashboard.md)",
        "- [Operational notes](docs/OPERATIONS.md)",
        "",
    ]

    for region in REGION_ORDER:
        section = section_lookup.get(region)
        readme_report_prefix = (
            f"latest/{section.get('report_prefix')}"
            if section and section.get("report_prefix")
            else f"latest/{region.lower()}/analysis/markdown"
        )
        readme_section = dict(section, report_prefix=readme_report_prefix) if section else None
        lines.extend(
            [
                *_best_candidate_section_lines(
                    readme_section,
                    region=region,
                    report_prefix=readme_report_prefix,
                    top_n=best_candidates_top_n,
                    heading=f"## {region} Best Scoring Candidates",
                ),
                "",
            ]
        )

    lines.extend(
        [
            "## Column Guide",
            "",
            "- `Breakout stance`: the repo's normalized final investing view for the setup after blending feed/technical evidence with any matched news and macro overlay.",
            "  Worst to best: `avoid` -> `fragile_watch` -> `mixed_watch` -> `constructive_watch` -> `constructive_bullish`",
            "- `Confidence`: how much usable evidence supports the current stance.",
            "  Worst to best: `low` -> `medium` -> `high`",
            "- `Bucket`: where the symbol sits in the shortlist built from the source website feeds.",
            "  Worst to best: `candidate` -> `entry_ready`",
        ]
    )

    return "\n".join(lines).strip() + "\n"
