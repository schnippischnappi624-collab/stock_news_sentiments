from __future__ import annotations

from typing import Any
from urllib.parse import quote

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


def _code_html(value: Any) -> str:
    return f"`{value}`"


def _escape_tex_text(value: Any) -> str:
    escaped = str(value)
    replacements = {
        "\\": r"\backslash{}",
        "{": r"\{",
        "}": r"\}",
        "_": r"\_",
        "%": r"\%",
        "&": r"\&",
        "#": r"\#",
        "$": r"\$",
    }
    for src, dest in replacements.items():
        escaped = escaped.replace(src, dest)
    return escaped


def _md_text(value: Any, *, table: bool = False) -> str:
    text = str(value)
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\n", " ")
    text = text.replace("$", "&#36;")
    if table:
        text = text.replace("|", "&#124;")
    return text


def _md_link_label(value: Any) -> str:
    label = _md_text(value)
    return label.replace("[", r"\[").replace("]", r"\]")


def _md_link(label: Any, url: str) -> str:
    safe_label = _md_link_label(label)
    safe_url = str(url or "").strip()
    if not safe_url:
        return safe_label
    return f"[{safe_label}](<{safe_url}>)"


def _yahoo_finance_quote_symbol(item: dict[str, Any], news_context: dict[str, Any] | None = None) -> str | None:
    profile = ((news_context or {}).get("company_profile") or {}) if isinstance(news_context, dict) else {}
    for candidate in (profile.get("query_symbol"), profile.get("symbol"), item.get("symbol")):
        value = str(candidate or "").strip()
        if value:
            return value
    return None


def _yahoo_finance_quote_url(item: dict[str, Any], news_context: dict[str, Any] | None = None) -> str | None:
    quote_symbol = _yahoo_finance_quote_symbol(item, news_context)
    if not quote_symbol:
        return None
    encoded_symbol = quote(quote_symbol, safe=".-_")
    return f"https://finance.yahoo.com/quote/{encoded_symbol}"


def _colorize(
    value: Any,
    *,
    color: str,
    code: bool = False,
) -> str:
    command = r"\texttt" if code else r"\textsf"
    inner = _escape_tex_text(value)
    return f"$\\color{{{color}}}{{{command}{{{inner}}}}}$"


def _bucket_display_label(bucket: Any) -> str:
    normalized = str(bucket or "").strip().lower()
    lookup = {
        "entry_ready": "entry ready",
        "candidate": "candidate",
    }
    return lookup.get(normalized, normalized.replace("_", " ") or "n/a")


def _stance_display_label(stance: Any) -> str:
    normalized = str(stance or "").strip().lower()
    lookup = {
        "constructive_bullish": "constructive bullish",
        "constructive_watch": "constructive watch",
        "mixed_watch": "mixed watch",
        "fragile_watch": "fragile watch",
        "avoid": "avoid",
    }
    return lookup.get(normalized, normalized.replace("_", " ") or "unknown")


def _score_color(score: Any) -> str:
    try:
        numeric = float(score)
    except (TypeError, ValueError):
        return "#57606a"
    if numeric >= 75:
        return "#1a7f37"
    if numeric >= 60:
        return "#9a6700"
    if numeric >= 45:
        return "#bc4c00"
    return "#cf222e"


def _confidence_color(confidence: Any) -> str:
    lookup = {
        "high": "#1a7f37",
        "medium": "#9a6700",
        "low": "#cf222e",
    }
    return lookup.get(str(confidence or "").strip().lower(), "#57606a")


def _bucket_color(bucket: Any) -> str:
    lookup = {
        "entry_ready": "#1a7f37",
        "candidate": "#bc4c00",
    }
    return lookup.get(str(bucket or "").strip().lower(), "#57606a")


def _stance_color(stance: Any) -> str:
    normalized = str(stance or "").strip().lower()
    lookup = {
        "constructive_bullish": "#1a7f37",
        "constructive_watch": "#2da44e",
        "mixed_watch": "#9a6700",
        "fragile_watch": "#bc4c00",
        "avoid": "#cf222e",
    }
    if normalized in lookup:
        return lookup[normalized]
    if normalized.startswith("constructive"):
        return "#2da44e"
    if normalized.startswith("mixed"):
        return "#9a6700"
    if normalized.startswith("fragile"):
        return "#bc4c00"
    if normalized.startswith("avoid"):
        return "#cf222e"
    return "#57606a"


def _distance_to_entry_color(close: Any, entry_limit: Any) -> str:
    try:
        close_value = float(close)
        entry_value = float(entry_limit)
    except (TypeError, ValueError):
        return "#57606a"
    if entry_value == 0:
        return "#57606a"
    pct_distance = abs((close_value - entry_value) / entry_value * 100.0)
    if pct_distance <= 1.0:
        return "#1a7f37"
    if pct_distance <= 3.0:
        return "#9a6700"
    if pct_distance <= 5.0:
        return "#bc4c00"
    return "#cf222e"


def _distance_to_entry_label(close: Any, entry_limit: Any) -> str | None:
    try:
        close_value = float(close)
        entry_value = float(entry_limit)
    except (TypeError, ValueError):
        return None
    if entry_value == 0:
        return None
    pct_distance = (close_value - entry_value) / entry_value * 100.0
    if abs(pct_distance) < 0.005:
        return "at limit"
    return f"{pct_distance:+.2f}%"


def _format_money_with_eur(
    value: Any,
    *,
    currency: str,
    eur_rates_context: dict[str, Any] | None = None,
    digits: int = 2,
) -> str | None:
    text = _metric_num(value, digits=digits)
    if text is None:
        return None
    label = f"{text} {currency}".strip()
    eur_value = convert_to_eur(value, currency, eur_rates_context)
    if currency.upper() != "EUR" and eur_value is not None:
        label += f" ({eur_value:,.{digits}f} EUR)"
    return label


def _execution_rows(
    item: dict[str, Any],
    *,
    eur_rates_context: dict[str, Any] | None = None,
) -> list[tuple[str, str]]:
    metrics = item.get("metrics", {}) or {}
    currency = str(item.get("currency") or "").strip()

    rows: list[tuple[str, str]] = []

    current_price = _format_money_with_eur(
        metrics.get("close"),
        currency=currency,
        eur_rates_context=eur_rates_context,
    )
    if current_price:
        rows.append(("Current price", _code_html(current_price)))

    entry_limit = _format_money_with_eur(
        metrics.get("entry_limit"),
        currency=currency,
        eur_rates_context=eur_rates_context,
    )
    if entry_limit:
        rows.append(("Entry limit", _code_html(entry_limit)))

    close_value = metrics.get("close")
    entry_limit_value = metrics.get("entry_limit")
    if close_value not in {None, ""} and entry_limit_value not in {None, ""}:
        try:
            distance_abs = float(close_value) - float(entry_limit_value)
            distance_pct = (distance_abs / float(entry_limit_value) * 100.0) if float(entry_limit_value) else None
        except (TypeError, ValueError, ZeroDivisionError):
            distance_abs = None
            distance_pct = None
        if distance_abs is not None and distance_pct is not None:
            distance_label = _format_money_with_eur(
                distance_abs,
                currency=currency,
                eur_rates_context=eur_rates_context,
            )
            if distance_label:
                pct_text = f"{distance_pct:+.2f}%"
                rows.append(
                    (
                        "Distance to entry limit",
                        _colorize(
                            f"{distance_label} / {pct_text}",
                            color=_distance_to_entry_color(close_value, entry_limit_value),
                            code=True,
                        ),
                    )
                )

    stop_init = _format_money_with_eur(
        metrics.get("stop_init"),
        currency=currency,
        eur_rates_context=eur_rates_context,
    )
    if stop_init:
        rows.append(("Initial stop", _code_html(stop_init)))

    hh20_prev = _format_money_with_eur(
        metrics.get("hh20_prev"),
        currency=currency,
        eur_rates_context=eur_rates_context,
    )
    if hh20_prev:
        rows.append(("Prior 20d high trigger", _code_html(hh20_prev)))

    tp_2r = _format_money_with_eur(
        metrics.get("tp_2r"),
        currency=currency,
        eur_rates_context=eur_rates_context,
    )
    if tp_2r:
        rows.append(("2R target", _code_html(tp_2r)))

    tp_3r = _format_money_with_eur(
        metrics.get("tp_3r"),
        currency=currency,
        eur_rates_context=eur_rates_context,
    )
    if tp_3r:
        rows.append(("3R target", _code_html(tp_3r)))

    r_dist = _format_money_with_eur(
        metrics.get("r_dist"),
        currency=currency,
        eur_rates_context=eur_rates_context,
    )
    if r_dist:
        rows.append(("Risk distance", _code_html(r_dist)))

    return rows


def _summary_table_lines(
    item: dict[str, Any],
    stance: dict[str, Any],
    *,
    eur_rates_context: dict[str, Any] | None = None,
) -> list[str]:
    score = stance.get("score_0_to_100", "n/a")
    confidence = stance.get("confidence", "n/a")
    rows: list[tuple[str, str]] = [
        (
            "Breakout stance",
            _colorize(
                _stance_display_label(stance.get("label", "unknown")),
                color=_stance_color(stance.get("label")),
                code=True,
            ),
        ),
        (
            "Score",
            _colorize(
                score,
                color=_score_color(score),
                code=True,
            ),
        ),
        (
            "Confidence",
            _colorize(
                confidence,
                color=_confidence_color(confidence),
                code=True,
            ),
        ),
        (
            "Bucket",
            _colorize(
                _bucket_display_label(item.get("selection_bucket")),
                color=_bucket_color(item.get("selection_bucket")),
                code=True,
            ),
        ),
    ]
    rows.extend(_execution_rows(item, eur_rates_context=eur_rates_context))

    lines = ["|  |  |", "| --- | --- |"]
    for label, value in rows:
        lines.append(f"| **{label}** | {value} |")
    return lines


def _section_points(items: list[dict[str, Any]], *, default_message: str) -> list[str]:
    if not items:
        return [f"- {_md_text(default_message)}"]
    lines = []
    for item in items:
        point = item.get("point") or item.get("name") or item.get("summary") or str(item)
        confidence = item.get("confidence")
        if confidence:
            lines.append(f"- {_md_text(point)} ({_md_text(confidence)})")
        else:
            lines.append(f"- {_md_text(point)}")
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


def _distance_to_entry_cell(
    close: Any,
    entry_limit: Any,
) -> str:
    label = _distance_to_entry_label(close, entry_limit)
    if not label:
        return "n/a"
    return _colorize(label, color=_distance_to_entry_color(close, entry_limit))


def _bucket_cell(bucket: Any) -> str:
    return _colorize(_bucket_display_label(bucket), color=_bucket_color(bucket))


def _score_cell(score: Any) -> str:
    return _colorize(score if score not in {None, ""} else "n/a", color=_score_color(score))


def _confidence_cell(confidence: Any) -> str:
    return _colorize(confidence or "n/a", color=_confidence_color(confidence))


def _stance_cell(stance: Any) -> str:
    return _colorize(_stance_display_label(stance), color=_stance_color(stance))


def _ranked_candidate_rows(shortlist: dict[str, Any], analysis_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    lookup = {row["symbol"]: row for row in analysis_rows}
    ranked_items = []
    for item in shortlist.get("symbols", []):
        symbol = item.get("symbol")
        report = lookup.get(symbol, {})
        stance = report.get("breakout_stance", {}) or {}
        metrics = item.get("metrics", {}) or {}
        ranked_items.append(
            {
                "symbol": symbol,
                "company_name": item.get("company_name"),
                "bucket": item.get("selection_bucket"),
                "display_rank": item.get("display_rank"),
                "score": stance.get("score_0_to_100", 0),
                "confidence": stance.get("confidence", "n/a"),
                "stance": stance.get("label", "unknown"),
                "close": metrics.get("close"),
                "entry_limit": metrics.get("entry_limit"),
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


def _filtered_symbol_lines(section_lookup: dict[str, dict[str, Any]]) -> list[str]:
    lines: list[str] = [
        "## Temporarily Omitted Penny Stocks",
        "",
        "The repo currently hides symbols with a current price below `1.00 EUR` as a temporary workaround until the upstream source filter is fixed.",
        "",
    ]

    entries: list[dict[str, Any]] = []
    for region in REGION_ORDER:
        section = section_lookup.get(region) or {}
        shortlist = section.get("shortlist", {}) or {}
        entries.extend(shortlist.get("filtered_out_symbols", []) or [])

    if not entries:
        lines.append("No symbols were filtered out by the temporary penny-stock rule in the latest runs.")
        return lines

    entries.sort(key=lambda entry: (str(entry.get("region") or ""), float(entry.get("current_price_eur") or 0.0), str(entry.get("symbol") or "")))
    for entry in entries:
        region = str(entry.get("region") or "n/a")
        symbol = entry.get("symbol") or "n/a"
        company = entry.get("company_name") or "Unknown Company"
        currency = str(entry.get("currency") or "").strip()
        current_price = entry.get("current_price")
        current_price_eur = entry.get("current_price_eur")
        original_label = str(current_price)
        if current_price not in {None, ""} and currency:
            original_label = f"{float(current_price):,.2f} {currency}"
        eur_label = f"{float(current_price_eur):,.2f} EUR" if current_price_eur not in {None, ""} else "n/a EUR"
        lines.append(f"- `{region}` `{symbol}` - {company} - `{original_label}` ({eur_label})")
    return lines


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
            "| Rank | Symbol | Company | Distance to entry | Bucket | Score | Confidence | Breakout stance |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )

    for idx, row in enumerate(top_items, start=1):
        symbol = row.get("symbol")
        lines.append(
            "| {rank} | [{symbol}]({report_prefix}/{file_name}.md) | {company} | {distance} | {bucket} | {score} | {confidence} | {stance} |".format(
                rank=idx,
                symbol=symbol,
                report_prefix=report_prefix,
                file_name=safe_symbol_name(symbol),
                company=_md_text(row.get("company_name") or "Unknown Company", table=True),
                distance=_distance_to_entry_cell(row.get("close"), row.get("entry_limit")),
                bucket=_bucket_cell(row.get("bucket")),
                score=_score_cell(row.get("score")),
                confidence=_confidence_cell(row.get("confidence")),
                stance=_stance_cell(row.get("stance")),
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
            "| Rank | Symbol | Distance to entry | Bucket | Breakout stance | Score | Confidence | Report |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )

    for item in shortlist.get("symbols", []):
        symbol = item.get("symbol")
        report = lookup.get(symbol, {})
        stance = report.get("breakout_stance", {}) or {}
        lines.append(
            "| {rank} | {symbol} | {distance} | {bucket} | {stance_label} | {score} | {confidence} | [report]({report_prefix}/{file_name}.md) |".format(
                rank=item.get("display_rank"),
                symbol=symbol,
                distance=_distance_to_entry_cell(
                    (item.get("metrics") or {}).get("close"),
                    (item.get("metrics") or {}).get("entry_limit"),
                ),
                bucket=_bucket_cell(item.get("selection_bucket")),
                stance_label=_stance_cell(stance.get("label", "unknown")),
                score=_score_cell(stance.get("score_0_to_100", "n/a")),
                confidence=_confidence_cell(stance.get("confidence", "n/a")),
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
    news_context: dict[str, Any] | None = None,
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
    yahoo_finance_url = _yahoo_finance_quote_url(item, news_context)
    yahoo_finance_symbol = _yahoo_finance_quote_symbol(item, news_context)

    lines = [
        f"# {_md_text(item.get('symbol'))} - {_md_text(item.get('company_name') or 'Unknown Company')}",
        "",
    ]
    if yahoo_finance_url:
        label = "Yahoo Finance"
        if yahoo_finance_symbol:
            label = f"Yahoo Finance ({yahoo_finance_symbol})"
        lines.extend([f"- Quote: {_md_link(label, yahoo_finance_url)}", ""])
    lines.extend(_summary_table_lines(item, stance, eur_rates_context=eur_rates_context))

    lines.extend(
        [
            "",
            "## Investment View",
            _md_text(report.get("summary", "No summary generated.")),
            "",
            f"- Thesis: {_md_text(thesis)}",
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
            f"- Stance: `{_md_text(news_support.get('stance', 'unknown'))}`",
            f"- Explanation: {_md_text(news_support.get('explanation', 'No explanation generated.'))}",
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
            label = _md_text(component.get("label") or "Unnamed component")
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
            lines.append(f"- {_md_link(title, url)} - {_md_text(published)}")

    if report.get("analysis_error"):
        lines.extend(["", "## Analysis Error", f"- {_md_text(report['analysis_error'])}"])

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
        "| Rank | Symbol | Distance to entry | Bucket | Stance | Score | Confidence | Report |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]

    lookup = {row["symbol"]: row for row in analysis_rows}
    for item in shortlist.get("symbols", []):
        symbol = item.get("symbol")
        report = lookup.get(symbol, {})
        stance = report.get("breakout_stance", {}) or {}
        report_name = f"{report_prefix}/{safe_symbol_name(symbol)}.md"
        lines.append(
            "| {rank} | {symbol} | {distance} | {bucket} | {stance_label} | {score} | {confidence} | [report]({report_name}) |".format(
                rank=item.get("display_rank"),
                symbol=symbol,
                distance=_distance_to_entry_cell((item.get("metrics") or {}).get("close"), (item.get("metrics") or {}).get("entry_limit")),
                bucket=_bucket_cell(item.get("selection_bucket")),
                stance_label=_stance_cell(stance.get("label", "unknown")),
                score=_score_cell(stance.get("score_0_to_100", "n/a")),
                confidence=_confidence_cell(stance.get("confidence", "n/a")),
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
        "| Rank | Symbol | Company | Distance to entry | Bucket | Score | Confidence | Breakout stance |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]

    for idx, row in enumerate(top_items, start=1):
        symbol = row.get("symbol")
        report_name = f"{report_prefix}/{safe_symbol_name(symbol)}.md"
        lines.append(
            "| {rank} | [{symbol}]({report_name}) | {company} | {distance} | {bucket} | {score} | {confidence} | {stance} |".format(
                rank=idx,
                symbol=symbol,
                report_name=report_name,
                company=_md_text(row.get("company_name") or "Unknown Company", table=True),
                distance=_distance_to_entry_cell(row.get("close"), row.get("entry_limit")),
                bucket=_bucket_cell(row.get("bucket")),
                score=_score_cell(row.get("score")),
                confidence=_confidence_cell(row.get("confidence")),
                stance=_stance_cell(row.get("stance")),
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
        "| Rank | Symbol | Company | Distance to entry | Bucket | Score | Confidence | Breakout stance |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]

    for idx, row in enumerate(top_items, start=1):
        symbol = row.get("symbol")
        lines.append(
            "| {rank} | [{symbol}](latest/analysis/markdown/{file_name}.md) | {company} | {distance} | {bucket} | {score} | {confidence} | {stance} |".format(
                rank=idx,
                symbol=symbol,
                file_name=safe_symbol_name(symbol),
                company=_md_text(row.get("company_name") or "Unknown Company", table=True),
                distance=_distance_to_entry_cell(row.get("close"), row.get("entry_limit")),
                bucket=_bucket_cell(row.get("bucket")),
                score=_score_cell(row.get("score")),
                confidence=_confidence_cell(row.get("confidence")),
                stance=_stance_cell(row.get("stance")),
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
            "  Worst to best: `avoid` -> `fragile watch` -> `mixed watch` -> `constructive watch` -> `constructive bullish`",
            "- `Confidence`: how much usable evidence supports the current stance.",
            "  Worst to best: `low` -> `medium` -> `high`",
            "- `Bucket`: where the symbol sits in the shortlist built from the source website feeds.",
            "  Worst to best: `candidate` -> `entry ready`",
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
            "  Worst to best: `avoid` -> `fragile watch` -> `mixed watch` -> `constructive watch` -> `constructive bullish`",
            "- `Confidence`: how much usable evidence supports the current stance.",
            "  Worst to best: `low` -> `medium` -> `high`",
            "- `Bucket`: where the symbol sits in the shortlist built from the source website feeds.",
            "  Worst to best: `candidate` -> `entry ready`",
            "",
            *_filtered_symbol_lines(section_lookup),
        ]
    )

    return "\n".join(lines).strip() + "\n"
