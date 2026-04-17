from __future__ import annotations

import re
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


def _investing_quote_symbol(item: dict[str, Any], news_context: dict[str, Any] | None = None) -> str | None:
    profile = ((news_context or {}).get("company_profile") or {}) if isinstance(news_context, dict) else {}
    for candidate in (item.get("symbol"), profile.get("requested_symbol"), profile.get("query_symbol"), profile.get("symbol")):
        value = str(candidate or "").strip()
        if value:
            return value
    return None


def _investing_quote_url(item: dict[str, Any], news_context: dict[str, Any] | None = None) -> str | None:
    symbol = _investing_quote_symbol(item, news_context)
    company_name = " ".join(str(item.get("company_name") or "").split()).strip()
    query_parts = [part for part in (symbol, company_name) if part]
    if not query_parts:
        return None
    encoded_query = quote(" ".join(query_parts), safe="")
    return f"https://de.investing.com/search/?q={encoded_query}"


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


MONITOR_SECTION_SPECS: tuple[tuple[str, str, str], ...] = (
    ("near_trigger", "Entry Ready Near Trigger", "near trigger"),
    ("extended", "Entry Ready But Already Spiked", "already spiked"),
    ("candidate", "Candidates", "candidate"),
)

MONITOR_SECTION_ORDER = {key: idx for idx, (key, _, _) in enumerate(MONITOR_SECTION_SPECS)}
MONITOR_SECTION_LABEL = {key: label for key, label, _ in MONITOR_SECTION_SPECS}
MONITOR_SECTION_SHORT_LABEL = {key: short for key, _, short in MONITOR_SECTION_SPECS}

ISSUER_SUFFIX_TOKENS = {
    "ab",
    "ag",
    "asa",
    "as",
    "co",
    "common",
    "corp",
    "corporation",
    "holding",
    "holdings",
    "inc",
    "incorporated",
    "limited",
    "ltd",
    "na",
    "nv",
    "oy",
    "oyj",
    "plc",
    "publ",
    "s",
    "sa",
    "se",
    "share",
    "shares",
    "spa",
    "stock",
}


def _float_or_none(value: Any) -> float | None:
    if value in {None, ""}:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _score_value(score: Any) -> float:
    numeric = _float_or_none(score)
    return numeric if numeric is not None else float("-inf")


def _distance_to_entry_pct(close: Any, entry_limit: Any) -> float | None:
    close_value = _float_or_none(close)
    entry_value = _float_or_none(entry_limit)
    if close_value is None or entry_value in {None, 0.0}:
        return None
    return (close_value - entry_value) / entry_value * 100.0


def _coverage_color(quality: Any) -> str:
    lookup = {
        "strong": "#1a7f37",
        "good": "#2da44e",
        "thin": "#9a6700",
        "none": "#cf222e",
    }
    return lookup.get(str(quality or "").strip().lower(), "#57606a")


def _coverage_cell(quality: Any) -> str:
    value = str(quality or "n/a").strip().lower() or "n/a"
    return _colorize(value, color=_coverage_color(value))


def _news_stance_color(stance: Any) -> str:
    lookup = {
        "supportive": "#1a7f37",
        "mixed": "#9a6700",
        "conflicting": "#cf222e",
    }
    return lookup.get(str(stance or "").strip().lower(), "#57606a")


def _news_stance_cell(stance: Any) -> str:
    value = str(stance or "n/a").strip().lower() or "n/a"
    return _colorize(value, color=_news_stance_color(value))


def _stock_article_count_color(count: Any) -> str:
    numeric = _float_or_none(count)
    if numeric is None:
        return "#57606a"
    if numeric >= 5:
        return "#1a7f37"
    if numeric >= 3:
        return "#2da44e"
    if numeric >= 1:
        return "#9a6700"
    return "#cf222e"


def _stock_article_count_cell(count: Any) -> str:
    numeric = _float_or_none(count)
    if numeric is None:
        return _colorize("n/a", color="#57606a")
    return _colorize(str(int(numeric)), color=_stock_article_count_color(numeric))


def _delta_score_cell(delta: int | None) -> str:
    if delta is None:
        return _colorize("n/a", color="#57606a")
    if delta > 0:
        color = "#1a7f37"
    elif delta < 0:
        color = "#cf222e"
    else:
        color = "#57606a"
    return _colorize(f"{delta:+d}", color=color, code=True)


def _change_cell(text: str, *, improved: bool | None) -> str:
    if improved is True:
        color = "#1a7f37"
    elif improved is False:
        color = "#cf222e"
    else:
        color = "#57606a"
    return _colorize(text, color=color, code=True)


def _new_badge() -> str:
    return _colorize("new", color="#1a7f37", code=True)


def _normalize_issuer_group_name(value: Any) -> str:
    tokens = re.sub(r"[^a-z0-9]+", " ", str(value or "").lower()).strip().split()
    while tokens and tokens[-1] in ISSUER_SUFFIX_TOKENS:
        tokens.pop()
    return " ".join(tokens).strip()


def _issuer_group_display(item: dict[str, Any], profile: dict[str, Any]) -> str:
    for candidate in (
        profile.get("long_name"),
        profile.get("short_name"),
        item.get("company_name"),
    ):
        label = " ".join(str(candidate or "").split()).strip()
        if label:
            return label
    return str(item.get("symbol") or "unknown").strip() or "unknown"


def _listing_label(item: dict[str, Any], profile: dict[str, Any]) -> str:
    exchange = str(item.get("exchange_code") or profile.get("exchange") or "n/a").strip() or "n/a"
    country = str(item.get("country") or profile.get("country") or "n/a").strip() or "n/a"
    return f"{exchange} / {country}"


def _monitor_section_key(item: dict[str, Any], metrics: dict[str, Any]) -> str:
    if str(item.get("selection_bucket") or "").strip().lower() != "entry_ready":
        return "candidate"
    distance_pct = _distance_to_entry_pct(metrics.get("close"), metrics.get("entry_limit"))
    if distance_pct is not None and abs(distance_pct) <= 5.0:
        return "near_trigger"
    return "extended"


def _top_catalyst_headwind(report: dict[str, Any]) -> str:
    catalyst = ((report.get("catalysts") or [{}])[0] or {}).get("point")
    risk = ((report.get("risks") or [{}])[0] or {}).get("point")
    parts = []
    if catalyst:
        parts.append(f"Cat: {catalyst}")
    if risk:
        parts.append(f"Risk: {risk}")
    return "; ".join(parts) if parts else "n/a"


def _build_monitor_rows(
    shortlist: dict[str, Any],
    analysis_rows: list[dict[str, Any]],
    profiles_by_symbol: dict[str, dict[str, Any]] | None,
    *,
    report_prefix: str | None,
) -> list[dict[str, Any]]:
    lookup = {row["symbol"]: row for row in analysis_rows if row.get("symbol")}
    rows: list[dict[str, Any]] = []

    for item in shortlist.get("symbols", []):
        symbol = item.get("symbol")
        if not symbol:
            continue
        report = lookup.get(symbol, {})
        profile = ((profiles_by_symbol or {}).get(symbol) or {}) if isinstance(profiles_by_symbol, dict) else {}
        stance = report.get("breakout_stance", {}) or {}
        coverage = report.get("coverage", {}) or {}
        metrics = item.get("metrics", {}) or {}
        issuer_group = _issuer_group_display(item, profile)
        issuer_group_key = _normalize_issuer_group_name(issuer_group) or _normalize_issuer_group_name(item.get("company_name")) or str(symbol).lower()
        distance_pct = _distance_to_entry_pct(metrics.get("close"), metrics.get("entry_limit"))
        rows.append(
            {
                "symbol": symbol,
                "company_name": item.get("company_name") or report.get("company_name") or issuer_group,
                "listing_label": _listing_label(item, profile),
                "issuer_group_display": issuer_group,
                "issuer_group_key": issuer_group_key,
                "distance_pct": distance_pct,
                "distance_sort_value": abs(distance_pct) if distance_pct is not None else float("inf"),
                "distance_cell": _distance_to_entry_cell(metrics.get("close"), metrics.get("entry_limit")),
                "bucket": item.get("selection_bucket"),
                "score": stance.get("score_0_to_100", "n/a"),
                "score_value": _score_value(stance.get("score_0_to_100")),
                "confidence": stance.get("confidence", "n/a"),
                "confidence_rank": _confidence_rank(stance.get("confidence", "n/a")),
                "stance": stance.get("label", "unknown"),
                "stance_rank": {
                    "avoid": 0,
                    "fragile_watch": 1,
                    "mixed_watch": 2,
                    "constructive_watch": 3,
                    "constructive_bullish": 4,
                }.get(str(stance.get("label") or "").strip().lower(), -1),
                "news_stance": (report.get("news_support", {}) or {}).get("stance", "n/a"),
                "coverage_quality": coverage.get("quality") or ((report.get("evidence", {}) or {}).get("news", {}) or {}).get("coverage_quality") or "n/a",
                "stock_articles": coverage.get("stock_articles", ((report.get("evidence", {}) or {}).get("news", {}) or {}).get("article_count", "n/a")),
                "top_driver": _top_catalyst_headwind(report),
                "section_key": _monitor_section_key(item, metrics),
                "report_path": f"{report_prefix}/{safe_symbol_name(symbol)}.md" if report_prefix else "",
            }
        )

    issuer_groups: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        issuer_groups.setdefault(row["issuer_group_key"], []).append(row)

    for members in issuer_groups.values():
        if len(members) <= 1:
            continue
        sibling_label = ", ".join(
            f"{member['symbol']} ({member['listing_label']})"
            for member in sorted(members, key=lambda member: str(member.get("symbol") or ""))
        )
        for member in members:
            member["issuer_group_display"] = f"{member['issuer_group_display']} (siblings: {sibling_label})"

    rows.sort(
        key=lambda row: (
            MONITOR_SECTION_ORDER.get(row["section_key"], 99),
            -row["score_value"],
            -row["confidence_rank"],
            row["distance_sort_value"],
            str(row.get("symbol") or ""),
        )
    )

    section_counters: dict[str, int] = {key: 0 for key, _, _ in MONITOR_SECTION_SPECS}
    for row in rows:
        section_counters[row["section_key"]] = section_counters.get(row["section_key"], 0) + 1
        row["section_rank"] = section_counters[row["section_key"]]

    return rows


def _apply_prior_deltas(
    current_rows: list[dict[str, Any]],
    prior_section: dict[str, Any] | None,
    *,
    prior_report_prefix: str | None,
) -> list[dict[str, Any]]:
    prior_rows: list[dict[str, Any]] = []
    if prior_section:
        prior_rows = _build_monitor_rows(
            prior_section.get("shortlist", {}) or {},
            prior_section.get("analysis_rows", []) or [],
            prior_section.get("profiles_by_symbol", {}) or {},
            report_prefix=prior_report_prefix,
        )

    prior_lookup = {row["symbol"]: row for row in prior_rows}
    current_symbols = {row["symbol"] for row in current_rows}

    for row in current_rows:
        prior = prior_lookup.get(row["symbol"])
        if prior is None:
            row["prior_rank_label"] = "new"
            row["delta_score"] = None
            row["delta_confidence_label"] = "new"
            row["delta_confidence_improved"] = None
            row["stance_change_label"] = "new"
            row["stance_change_improved"] = None
            row["is_new"] = True
            continue

        row["prior_rank_label"] = f"{MONITOR_SECTION_SHORT_LABEL.get(prior['section_key'], prior['section_key'])} #{prior['section_rank']}"
        row["is_new"] = False

        current_score = _float_or_none(row.get("score"))
        prior_score = _float_or_none(prior.get("score"))
        if current_score is None or prior_score is None:
            row["delta_score"] = None
        else:
            row["delta_score"] = int(round(current_score - prior_score))

        current_confidence = str(row.get("confidence") or "n/a").strip().lower()
        prior_confidence = str(prior.get("confidence") or "n/a").strip().lower()
        if current_confidence == prior_confidence:
            row["delta_confidence_label"] = "unchanged"
            row["delta_confidence_improved"] = None
        else:
            row["delta_confidence_label"] = f"{prior_confidence} -> {current_confidence}"
            row["delta_confidence_improved"] = _confidence_rank(current_confidence) > _confidence_rank(prior_confidence)

        current_stance = str(row.get("stance") or "unknown").strip().lower()
        prior_stance = str(prior.get("stance") or "unknown").strip().lower()
        if current_stance == prior_stance:
            row["stance_change_label"] = "unchanged"
            row["stance_change_improved"] = None
        else:
            row["stance_change_label"] = f"{_stance_display_label(prior_stance)} -> {_stance_display_label(current_stance)}"
            row["stance_change_improved"] = int(row.get("stance_rank", -1)) > int(prior.get("stance_rank", -1))

    dropped_rows = [row for row in prior_rows if row["symbol"] not in current_symbols]
    dropped_rows.sort(
        key=lambda row: (
            MONITOR_SECTION_ORDER.get(row["section_key"], 99),
            int(row.get("section_rank") or 9999),
            str(row.get("symbol") or ""),
        )
    )
    return dropped_rows


def _limited_monitor_rows(rows: list[dict[str, Any]], *, top_n: int | None) -> list[dict[str, Any]]:
    if top_n is None:
        return list(rows)
    return list(rows[: int(max(1, top_n))])


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
    investing_quote_url = _investing_quote_url(item, news_context)
    investing_quote_symbol = _investing_quote_symbol(item, news_context)

    lines = [
        f"# {_md_text(item.get('symbol'))} - {_md_text(item.get('company_name') or 'Unknown Company')}",
        "",
    ]
    if investing_quote_url:
        label = "Investing.com"
        if investing_quote_symbol:
            label = f"Investing.com ({investing_quote_symbol})"
        lines.extend([f"- Quote: {_md_link(label, investing_quote_url)}", ""])
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


def _monitor_table_header_lines() -> list[str]:
    return [
        "| Rank | Symbol | Company | Distance to entry | Bucket | Score | Prior rank | Confidence | Breakout stance | Stance change | News stance | Coverage | Stock articles |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]


def _monitor_row_line(row: dict[str, Any]) -> str:
    report_path = str(row.get("report_path") or "").strip()
    symbol_cell = _md_link(row.get("symbol") or "n/a", report_path) if report_path else _md_text(row.get("symbol") or "n/a", table=True)
    prior_rank = _new_badge() if row.get("is_new") else _code_html(row.get("prior_rank_label") or "n/a")
    stance_change = (
        _new_badge()
        if row.get("stance_change_label") == "new"
        else _change_cell(str(row.get("stance_change_label") or "n/a"), improved=row.get("stance_change_improved"))
    )
    return (
        "| {rank} | {symbol} | {company} | {distance} | {bucket} | {score} | {prior_rank} | {confidence} | {stance} | {stance_change} | {news_stance} | {coverage} | {stock_articles} |".format(
            rank=row.get("section_rank", "n/a"),
            symbol=symbol_cell,
            company=_md_text(row.get("company_name") or "Unknown Company", table=True),
            distance=row.get("distance_cell") or "n/a",
            bucket=_bucket_cell(row.get("bucket")),
            score=_score_cell(row.get("score")),
            prior_rank=prior_rank,
            confidence=_confidence_cell(row.get("confidence")),
            stance=_stance_cell(row.get("stance")),
            stance_change=stance_change,
            news_stance=_news_stance_cell(row.get("news_stance")),
            coverage=_coverage_cell(row.get("coverage_quality")),
            stock_articles=_stock_article_count_cell(row.get("stock_articles")),
        )
    )


def _column_guide_lines() -> list[str]:
    return [
        "## Column Guide",
        "",
        "- `Rank`: rank resets inside each section and uses `score desc -> confidence desc -> abs(distance to entry) asc -> symbol asc`.",
        "- `Breakout stance`: normalized final investing view after blending feed, technical, stock-news, and market-overlay evidence.",
        "  Worst to best: `avoid` -> `fragile watch` -> `mixed watch` -> `constructive watch` -> `constructive bullish`",
        "- `Confidence`: evidence strength behind the current stance.",
        "  Worst to best: `low` -> `medium` -> `high`",
        "- `Bucket`: source-feed setup status.",
        "  Worst to best: `candidate` -> `entry ready`",
        "- `News stance`: whether recent company and matched market news support, conflict with, or mix around the setup.",
        "- `Coverage`: company-specific news quality in the local cache.",
        "  Worst to best: `none` -> `thin` -> `good` -> `strong`",
        "- `Prior rank`, `Stance change`: run-over-run monitoring fields versus the immediately prior committed regional run.",
    ]


def _monitor_region_section_lines(
    section: dict[str, Any] | None,
    *,
    region: str,
    heading: str | None,
    report_prefix: str,
    prior_report_prefix: str | None,
    top_n: int | None = None,
) -> list[str]:
    lines: list[str] = []
    if heading:
        lines.extend([heading, ""])
    if section is None:
        lines.append(f"No {region} snapshot is available yet.")
        return lines

    manifest = section.get("manifest", {}) or {}
    shortlist = section.get("shortlist", {}) or {}
    analysis_rows = section.get("analysis_rows", []) or []
    profiles_by_symbol = section.get("profiles_by_symbol", {}) or {}
    prior_section = section.get("prior_section")
    prior_manifest = (prior_section or {}).get("manifest", {}) or {}

    rows = _build_monitor_rows(
        shortlist,
        analysis_rows,
        profiles_by_symbol,
        report_prefix=report_prefix,
    )
    _apply_prior_deltas(
        rows,
        prior_section,
        prior_report_prefix=prior_report_prefix,
    )
    shown_rows = _limited_monitor_rows(rows, top_n=top_n)

    lines.extend(
        [
            f"- Run ID: `{manifest.get('run_id', 'n/a')}`",
            f"- Prior regional run: `{prior_manifest.get('run_id', 'n/a')}`",
            f"- Feed dates: `{', '.join(manifest.get('feed_dates', [])) or 'n/a'}`",
            f"- Symbols analyzed: `{len(rows)}`",
            "- Sort mode: sections `Entry Ready Near Trigger -> Entry Ready But Already Spiked -> Candidates`; in-section rank = `score desc -> confidence desc -> abs(distance to entry) asc -> symbol asc`; near-trigger cutoff = `5%`",
        ]
    )
    if top_n is not None:
        lines.append(f"- Rows shown: `{len(shown_rows)}` of `{len(rows)}`")
    lines.append("")

    for section_key, section_label, _ in MONITOR_SECTION_SPECS:
        section_rows = [row for row in shown_rows if row.get("section_key") == section_key]
        lines.extend([f"### {section_label}", ""])
        if not section_rows:
            if top_n is None:
                lines.extend([f"No names are currently classified as `{section_label.lower()}`.", ""])
            else:
                lines.extend([f"No names from this section landed inside the current top-`{int(max(1, top_n))}` cutoff.", ""])
            continue
        lines.extend(_monitor_table_header_lines())
        for row in section_rows:
            lines.append(_monitor_row_line(row))
        lines.append("")

    return lines


def render_dashboard(
    manifest: dict[str, Any],
    shortlist: dict[str, Any],
    analysis_rows: list[dict[str, Any]],
    *,
    report_prefix: str,
    profiles_by_symbol: dict[str, dict[str, Any]] | None = None,
    prior_section: dict[str, Any] | None = None,
    prior_report_prefix: str | None = None,
) -> str:
    lines = [
        "# Daily Breakout Monitoring Dashboard",
        "",
        "Explicit monitoring view for one regional run.",
        "",
    ]
    lines.extend(
        _monitor_region_section_lines(
            {
                "region": normalize_region(manifest.get("region")),
                "manifest": manifest,
                "shortlist": shortlist,
                "analysis_rows": analysis_rows,
                "profiles_by_symbol": profiles_by_symbol or {},
                "prior_section": prior_section,
            },
            region=normalize_region(manifest.get("region")) or "run",
            heading=None,
            report_prefix=report_prefix,
            prior_report_prefix=prior_report_prefix,
            top_n=None,
        )
    )
    return "\n".join(lines).strip() + "\n"


def render_best_candidates(
    manifest: dict[str, Any],
    shortlist: dict[str, Any],
    analysis_rows: list[dict[str, Any]],
    *,
    report_prefix: str,
    top_n: int = 15,
    profiles_by_symbol: dict[str, dict[str, Any]] | None = None,
    prior_section: dict[str, Any] | None = None,
    prior_report_prefix: str | None = None,
) -> str:
    lines = [
        "# Best Candidates by Actionability and Score",
        "",
        "Top regional names using the same sectioned monitoring sort as the main dashboard.",
        "",
    ]
    lines.extend(
        _monitor_region_section_lines(
            {
                "region": normalize_region(manifest.get("region")),
                "manifest": manifest,
                "shortlist": shortlist,
                "analysis_rows": analysis_rows,
                "profiles_by_symbol": profiles_by_symbol or {},
                "prior_section": prior_section,
            },
            region=normalize_region(manifest.get("region")) or "run",
            heading=None,
            report_prefix=report_prefix,
            prior_report_prefix=prior_report_prefix,
            top_n=top_n,
        )
    )
    return "\n".join(lines).strip() + "\n"


def render_project_readme(
    manifest: dict[str, Any],
    shortlist: dict[str, Any],
    analysis_rows: list[dict[str, Any]],
    *,
    best_candidates_top_n: int = 15,
    profiles_by_symbol: dict[str, dict[str, Any]] | None = None,
    prior_section: dict[str, Any] | None = None,
    prior_report_prefix: str | None = None,
) -> str:
    lines = [
        "# stock_news_sentiments",
        "",
        "Auto-generated breakout monitoring dashboard for the latest committed run.",
        "",
        "Quick links:",
        "- [Best scoring candidates](latest/best_candidates.md)",
        "- [Full dashboard](latest/dashboard.md)",
        "- [Latest detailed analyses](latest/analysis/markdown/)",
        "- [Operational notes](docs/OPERATIONS.md)",
        "",
    ]
    lines.extend(
        _monitor_region_section_lines(
            {
                "region": normalize_region(manifest.get("region")),
                "manifest": manifest,
                "shortlist": shortlist,
                "analysis_rows": analysis_rows,
                "profiles_by_symbol": profiles_by_symbol or {},
                "prior_section": prior_section,
            },
            region=normalize_region(manifest.get("region")) or "run",
            heading="## Best Candidates by Actionability and Score",
            report_prefix="latest/analysis/markdown",
            prior_report_prefix=prior_report_prefix,
            top_n=best_candidates_top_n,
        )
    )
    lines.extend(["", *_column_guide_lines()])
    return "\n".join(lines).strip() + "\n"


def render_regional_dashboard(sections: list[dict[str, Any]]) -> str:
    section_lookup = _section_lookup(sections)
    available_regions = [region for region in REGION_ORDER if section_lookup.get(region)]
    total_symbols = sum(len((section_lookup.get(region) or {}).get("shortlist", {}).get("symbols", [])) for region in REGION_ORDER)

    lines = [
        "# Latest Regional Breakout Monitoring Dashboard",
        "",
        f"- Regions available: `{', '.join(available_regions) or 'none'}`",
        f"- Symbols analyzed: `{total_symbols}`",
    ]

    for region in REGION_ORDER:
        section = section_lookup.get(region)
        prior_run_id = (((section or {}).get("prior_section") or {}).get("manifest") or {}).get("run_id")
        lines.extend(
            [
                "",
                *_monitor_region_section_lines(
                    section,
                    region=region,
                    heading=f"## {region} Monitoring Dashboard",
                    report_prefix=f"{region.lower()}/analysis/markdown",
                    prior_report_prefix=(
                        f"../artifacts/daily_runs/{prior_run_id}/analysis/markdown"
                        if prior_run_id
                        else None
                    ),
                    top_n=None,
                ),
            ]
        )

    return "\n".join(lines).strip() + "\n"


def render_regional_best_candidates(sections: list[dict[str, Any]], *, top_n: int = 15) -> str:
    section_lookup = _section_lookup(sections)
    available_regions = [region for region in REGION_ORDER if section_lookup.get(region)]

    lines = [
        "# Latest Regional Best Candidates by Actionability and Score",
        "",
        f"- Regions available: `{', '.join(available_regions) or 'none'}`",
        "",
    ]

    for region in REGION_ORDER:
        section = section_lookup.get(region)
        prior_run_id = (((section or {}).get("prior_section") or {}).get("manifest") or {}).get("run_id")
        lines.extend(
            [
                *_monitor_region_section_lines(
                    section,
                    region=region,
                    heading=f"## {region} Best Candidates by Actionability and Score",
                    report_prefix=f"{region.lower()}/analysis/markdown",
                    prior_report_prefix=(
                        f"../artifacts/daily_runs/{prior_run_id}/analysis/markdown"
                        if prior_run_id
                        else None
                    ),
                    top_n=top_n,
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
        "Auto-generated breakout monitoring dashboard for the latest committed regional runs.",
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
        prior_run_id = (((section or {}).get("prior_section") or {}).get("manifest") or {}).get("run_id")
        lines.extend(
            [
                *_monitor_region_section_lines(
                    section,
                    region=region,
                    heading=f"## {region} Best Candidates by Actionability and Score",
                    report_prefix=f"latest/{region.lower()}/analysis/markdown",
                    prior_report_prefix=(
                        f"artifacts/daily_runs/{prior_run_id}/analysis/markdown"
                        if prior_run_id
                        else None
                    ),
                    top_n=best_candidates_top_n,
                ),
                "",
            ]
        )

    lines.extend(["", *_column_guide_lines(), "", *_filtered_symbol_lines(section_lookup)])

    return "\n".join(lines).strip() + "\n"
