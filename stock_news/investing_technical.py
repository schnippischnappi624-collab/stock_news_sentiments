from __future__ import annotations

import json
import re
import subprocess
import tempfile
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from stock_news.utils import read_json


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_company_name(value: Any) -> str:
    normalized = unicodedata.normalize("NFKD", str(value or ""))
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", " ", ascii_text.lower()).strip()


def _canonical_investing_quote_url(url: Any) -> str | None:
    value = str(url or "").strip()
    if not value:
        return None
    match = re.match(r"^https://de\.investing\.com/equities/([a-z0-9-]+)/?(?:[?#].*)?$", value, flags=re.IGNORECASE)
    if not match:
        return None
    return f"https://de.investing.com/equities/{match.group(1).lower()}"


def _canonical_investing_technical_url(url: Any) -> str | None:
    value = str(url or "").strip()
    if not value:
        return None
    match = re.match(
        r"^https://de\.investing\.com/equities/([a-z0-9-]+)-technical/?(?:[?#].*)?$",
        value,
        flags=re.IGNORECASE,
    )
    if not match:
        return None
    return f"https://de.investing.com/equities/{match.group(1).lower()}-technical"


def _technical_url_from_quote_url(url: Any) -> str | None:
    quote_url = _canonical_investing_quote_url(url)
    if not quote_url:
        return None
    return f"{quote_url}-technical"


def _normalize_signal(value: Any) -> str | None:
    normalized = " ".join(str(value or "").strip().lower().replace("_", " ").split())
    lookup = {
        "strong buy": "Strong Buy",
        "starker kauf": "Strong Buy",
        "buy": "Buy",
        "kauf": "Buy",
        "neutral": "Neutral",
        "sell": "Sell",
        "verkauf": "Sell",
        "strong sell": "Strong Sell",
        "starker verkauf": "Strong Sell",
    }
    return lookup.get(normalized)


def _normalize_timeframe(value: Any) -> str | None:
    normalized = " ".join(str(value or "").strip().lower().split())
    if not normalized:
        return None
    if any(token in normalized for token in ("stünd", "std", "hour", "hourly", "1h")):
        return "1h"
    return None


def _chunked(items: list[dict[str, Any]], size: int) -> list[list[dict[str, Any]]]:
    return [items[idx : idx + size] for idx in range(0, len(items), size)]


def _build_request(item: dict[str, Any], profile: dict[str, Any] | None, quote_url: str) -> dict[str, Any]:
    normalized_profile = profile or {}
    return {
        "symbol": str(item.get("symbol") or "").strip(),
        "company_name": " ".join(
            str(
                item.get("company_name")
                or normalized_profile.get("long_name")
                or normalized_profile.get("short_name")
                or ""
            ).split()
        ).strip(),
        "exchange_code": str(item.get("exchange_code") or "").strip().upper() or None,
        "country": " ".join(str(item.get("country") or normalized_profile.get("country") or "").split()).strip() or None,
        "region": (
            str(((item.get("source_rows") or [{}])[0] or {}).get("_source_region") or item.get("region") or "").strip().upper()
            or None
        ),
        "quote_url": quote_url,
        "technical_url": _technical_url_from_quote_url(quote_url),
    }


def _lookup_key(request: dict[str, Any]) -> str:
    return "|".join(
        [
            str(request.get("region") or ""),
            str(request.get("exchange_code") or ""),
            str(request.get("symbol") or ""),
            _normalize_company_name(request.get("company_name") or ""),
        ]
    )


def _codex_prompt(requests_batch: list[dict[str, Any]]) -> str:
    payload = {"requests": requests_batch}
    return f"""
You are extracting hourly Charttechnik summary signals from de.investing.com stock technical-analysis pages.

Return JSON only matching the provided schema.

Rules:
- Use the provided `technical_url` when it is valid and matches the issuer.
- If needed, verify the exact technical page using the `quote_url`, symbol, company name, exchange, country, and region.
- Read only the `Stündlich` / hourly view.
- Return the three summary labels exactly as one of: `Strong Buy`, `Buy`, `Neutral`, `Sell`, `Strong Sell`.
- Use `null` when a field is unavailable or cannot be verified.
- Do not infer hourly values from daily, weekly, monthly, 30-minute, or 5-hour tabs.
- Prefer exact issuer matches. Ignore unrelated issuers with similar names or tickers.

Requests:
{json.dumps(payload, indent=2, default=str)}
""".strip()


def _run_codex_batch(
    requests_batch: list[dict[str, Any]],
    *,
    schema_path: Path,
    repo_root: Path,
    output_path: Path,
    timeout_s: float = 75.0,
) -> dict[str, dict[str, Any]]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    prompt = _codex_prompt(requests_batch)
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
            timeout=timeout_s,
        )
    except Exception:
        return {}

    if completed.returncode != 0 or not output_path.exists():
        return {}

    try:
        payload = read_json(output_path)
    except Exception:
        return {}

    results: dict[str, dict[str, Any]] = {}
    for entry in payload.get("results", []) or []:
        if not isinstance(entry, dict):
            continue
        lookup_key = str(entry.get("lookup_key") or "").strip()
        if not lookup_key:
            continue
        results[lookup_key] = {
            "technical_page_url": _canonical_investing_technical_url(entry.get("technical_page_url")),
            "timeframe": _normalize_timeframe(entry.get("timeframe")),
            "overview": _normalize_signal(entry.get("overview")),
            "technical_indicators": _normalize_signal(entry.get("technical_indicators")),
            "moving_averages": _normalize_signal(entry.get("moving_averages")),
        }
    return results


def fetch_investing_technical_signals(
    shortlist_items: list[dict[str, Any]],
    *,
    profiles_by_symbol: dict[str, dict[str, Any]] | None,
    resolved_quote_urls: dict[str, str] | None,
    schema_path: Path,
    repo_root: Path,
    batch_size: int = 3,
) -> dict[str, Any]:
    requests_to_resolve: list[dict[str, Any]] = []
    signals_by_symbol: dict[str, dict[str, Any]] = {}
    unresolved_symbols: list[str] = []

    for item in shortlist_items:
        symbol = str(item.get("symbol") or "").strip()
        quote_url = _canonical_investing_quote_url((resolved_quote_urls or {}).get(symbol))
        if not symbol:
            continue
        if not quote_url:
            unresolved_symbols.append(symbol)
            continue
        request = _build_request(item, (profiles_by_symbol or {}).get(symbol) or {}, quote_url)
        request["lookup_key"] = _lookup_key(request)
        requests_to_resolve.append(request)

    resolved_count = 0
    for batch_index, batch in enumerate(_chunked(requests_to_resolve, max(1, int(batch_size))), start=1):
        if not batch:
            continue
        output_path = Path(tempfile.gettempdir()) / f"stock_news_investing_technical_batch_{batch_index}.json"
        batch_results = _run_codex_batch(
            batch,
            schema_path=schema_path,
            repo_root=repo_root,
            output_path=output_path,
        )
        for request in batch:
            symbol = str(request.get("symbol") or "").strip()
            if not symbol:
                continue
            payload = batch_results.get(str(request.get("lookup_key") or "")) or {}
            overview = _normalize_signal(payload.get("overview"))
            technical_indicators = _normalize_signal(payload.get("technical_indicators"))
            moving_averages = _normalize_signal(payload.get("moving_averages"))
            if not any((overview, technical_indicators, moving_averages)):
                unresolved_symbols.append(symbol)
                continue
            technical_page_url = _canonical_investing_technical_url(payload.get("technical_page_url")) or request.get("technical_url")
            signals_by_symbol[symbol] = {
                "provider": "investing.com",
                "timeframe": _normalize_timeframe(payload.get("timeframe")) or "1h",
                "timeframe_label": "Stündlich",
                "technical_page_url": technical_page_url,
                "overview": overview,
                "technical_indicators": technical_indicators,
                "moving_averages": moving_averages,
                "resolved_at_utc": _now_utc(),
            }
            resolved_count += 1

    unresolved_symbols = sorted({symbol for symbol in unresolved_symbols if symbol and symbol not in signals_by_symbol})
    return {
        "ok": True,
        "resolved_symbols": resolved_count,
        "signals_by_symbol": signals_by_symbol,
        "unresolved_symbols": unresolved_symbols,
    }
