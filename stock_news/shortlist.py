from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pandas as pd

from stock_news.fx import convert_to_eur


FILTER_CURRENCY_BY_EXCHANGE: dict[str, str] = {
    "US": "USD",
    "CO": "DKK",
    "HE": "EUR",
    "MC": "EUR",
    "OL": "NOK",
    "PA": "EUR",
    "ST": "SEK",
    "XETRA": "EUR",
}


def _float_or_min(value: Any) -> float:
    if value is None or value == "":
        return float("-inf")
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("-inf")


def _enrich_row(row: dict[str, Any], parsed_payload: dict[str, Any], table: dict[str, Any]) -> dict[str, Any]:
    feed = parsed_payload["feed"]
    enriched = dict(row)
    enriched["_source_filename"] = feed["filename"]
    enriched["_source_url"] = feed["url"]
    enriched["_source_kind"] = feed["kind"]
    enriched["_source_region"] = feed["region"]
    enriched["_source_universe"] = feed["universe"]
    enriched["_source_feed_date"] = feed["feed_date"]
    enriched["_table_key"] = table["table_key"]
    enriched["_table_title"] = table["title"]
    return enriched


def _base_item(row: dict[str, Any], *, bucket: str) -> dict[str, Any]:
    return {
        "symbol": row.get("symbol"),
        "company_name": row.get("company_name"),
        "exchange_code": row.get("exchange_code"),
        "country": row.get("country"),
        "currency": row.get("currency"),
        "selection_bucket": bucket,
        "entry_ready": bucket == "entry_ready",
        "selection_reason": row.get("reason") or row.get("state") or bucket,
        "metrics": {
            "state": row.get("state"),
            "invest_score": row.get("invest_score"),
            "state_score": row.get("state_score"),
            "vol_anom": row.get("vol_anom"),
            "close": row.get("close"),
            "volume": row.get("volume"),
            "hh20_prev": row.get("hh20_prev"),
            "atr14": row.get("atr14"),
            "entry_limit": row.get("entry_limit"),
            "stop_init": row.get("stop_init"),
            "r_dist": row.get("r_dist"),
            "tp_2r": row.get("tp_2r"),
            "tp_3r": row.get("tp_3r"),
            "risk_eur": row.get("risk_eur"),
            "qty_for_risk": row.get("qty_for_risk"),
        },
        "source_rows": [],
    }


def _merge_item_metrics(item: dict[str, Any], row: dict[str, Any]) -> None:
    metrics = item.setdefault("metrics", {})
    for key in (
        "state",
        "invest_score",
        "state_score",
        "vol_anom",
        "close",
        "volume",
        "hh20_prev",
        "atr14",
        "entry_limit",
        "stop_init",
        "r_dist",
        "tp_2r",
        "tp_3r",
        "risk_eur",
        "qty_for_risk",
    ):
        value = row.get(key)
        if value is None or value == "":
            continue
        if metrics.get(key) in {None, ""}:
            metrics[key] = value


def _filter_currency(item: dict[str, Any]) -> str | None:
    currency = str(item.get("currency") or "").strip().upper()
    if currency:
        return currency
    exchange_code = str(item.get("exchange_code") or "").strip().upper()
    return FILTER_CURRENCY_BY_EXCHANGE.get(exchange_code)


def _item_region(item: dict[str, Any]) -> str | None:
    for row in item.get("source_rows", []) or []:
        region = str(row.get("_source_region") or "").strip().upper()
        if region:
            return region
    return None


def apply_min_price_eur_filter(
    shortlist: dict[str, Any],
    *,
    eur_rates_context: dict[str, Any] | None,
    min_price_eur: float = 1.0,
) -> dict[str, Any]:
    items = list(shortlist.get("symbols", []) or [])
    kept_items: list[dict[str, Any]] = []
    filtered_items: list[dict[str, Any]] = []

    for item in items:
        metrics = item.get("metrics", {}) or {}
        close = metrics.get("close")
        currency = _filter_currency(item)
        close_eur = convert_to_eur(close, currency, eur_rates_context)

        if close_eur is not None and float(close_eur) < float(min_price_eur):
            filtered_items.append(
                {
                    "symbol": item.get("symbol"),
                    "company_name": item.get("company_name"),
                    "region": _item_region(item),
                    "selection_bucket": item.get("selection_bucket"),
                    "currency": currency,
                    "current_price": close,
                    "current_price_eur": round(float(close_eur), 6),
                }
            )
            continue

        if currency and not item.get("currency"):
            item = dict(item)
            item["currency"] = currency
        kept_items.append(item)

    for idx, item in enumerate(kept_items, start=1):
        item["display_rank"] = idx

    updated = dict(shortlist)
    updated["symbols"] = kept_items
    updated["entry_ready_count"] = sum(1 for item in kept_items if item.get("entry_ready"))
    updated["candidate_count"] = sum(1 for item in kept_items if not item.get("entry_ready"))
    updated["filtered_out_symbols"] = filtered_items
    updated["temporary_filters"] = {
        "min_price_eur": float(min_price_eur),
        "rate_date": (eur_rates_context or {}).get("rate_date"),
        "filtered_count": len(filtered_items),
        "kind": "min_price_eur",
    }
    return updated


def build_shortlist(parsed_payloads: list[dict[str, Any]], *, extra_candidates: int = 10) -> dict[str, Any]:
    entry_ready_rows: list[dict[str, Any]] = []
    entry_stop_target_rows: list[dict[str, Any]] = []
    candidate_rows: list[dict[str, Any]] = []

    for parsed in parsed_payloads:
        feed_kind = parsed["feed"]["kind"]
        for table in parsed["tables"]:
            for row in table["rows"]:
                symbol = row.get("symbol")
                if not symbol:
                    continue
                enriched = _enrich_row(row, parsed, table)
                state = str(row.get("state") or "").upper()
                if feed_kind == "Results" and (state == "ENTRY_READY" or "entry_ready" in table["table_key"]):
                    entry_ready_rows.append(enriched)
                if feed_kind == "Results" and "entry_stop_targets" in str(table.get("table_key") or ""):
                    entry_stop_target_rows.append(enriched)
                if feed_kind == "Results_CANDIDATES":
                    candidate_rows.append(enriched)

    selected: dict[str, dict[str, Any]] = {}
    for row in sorted(entry_ready_rows, key=lambda item: (str(item.get("_source_region")), str(item.get("symbol")))):
        symbol = str(row["symbol"])
        item = selected.setdefault(symbol, _base_item(row, bucket="entry_ready"))
        _merge_item_metrics(item, row)
        item["source_rows"].append(row)

    for row in sorted(entry_stop_target_rows, key=lambda item: (str(item.get("_source_region")), str(item.get("symbol")))):
        symbol = str(row["symbol"])
        item = selected.get(symbol)
        if item is None:
            continue
        _merge_item_metrics(item, row)
        item["source_rows"].append(row)

    ranked_candidates = sorted(
        candidate_rows,
        key=lambda row: (
            _float_or_min(row.get("invest_score")),
            _float_or_min(row.get("state_score")),
            _float_or_min(row.get("vol_anom")),
            str(row.get("symbol") or ""),
        ),
        reverse=True,
    )

    additional_added = 0
    for rank, row in enumerate(ranked_candidates, start=1):
        symbol = str(row["symbol"])
        if symbol in selected:
            selected[symbol]["source_rows"].append(row)
            continue
        if additional_added >= int(extra_candidates):
            continue
        item = _base_item(row, bucket="candidate")
        _merge_item_metrics(item, row)
        item["candidate_rank"] = rank
        item["source_rows"].append(row)
        selected[symbol] = item
        additional_added += 1

    items = list(selected.values())
    items.sort(
        key=lambda item: (
            0 if item["entry_ready"] else 1,
            -_float_or_min(item["metrics"].get("invest_score")),
            -_float_or_min(item["metrics"].get("state_score")),
            str(item["symbol"]),
        )
    )
    for idx, item in enumerate(items, start=1):
        item["display_rank"] = idx

    shortlist = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "entry_ready_count": sum(1 for item in items if item["entry_ready"]),
        "candidate_count": sum(1 for item in items if not item["entry_ready"]),
        "extra_candidate_limit": int(extra_candidates),
        "symbols": items,
    }
    return shortlist


def shortlist_to_frame(shortlist: dict[str, Any]) -> pd.DataFrame:
    rows = []
    for item in shortlist.get("symbols", []):
        row = {
            "display_rank": item.get("display_rank"),
            "symbol": item.get("symbol"),
            "company_name": item.get("company_name"),
            "selection_bucket": item.get("selection_bucket"),
            "entry_ready": item.get("entry_ready"),
            "candidate_rank": item.get("candidate_rank"),
            "selection_reason": item.get("selection_reason"),
        }
        row.update({f"metric_{k}": v for k, v in item.get("metrics", {}).items()})
        rows.append(row)
    return pd.DataFrame(rows)
