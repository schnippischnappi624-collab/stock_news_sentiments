from __future__ import annotations

import json
import os
import pty
import re
import select
import subprocess
import tempfile
import time
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
    match = re.match(
        r"^https://(?:[a-z]+\.)?investing\.com/equities/([a-z0-9.-]+)/?(?:[?#].*)?$",
        value,
        flags=re.IGNORECASE,
    )
    if not match:
        return None
    return f"https://de.investing.com/equities/{match.group(1).lower()}"


def _canonical_investing_technical_url(url: Any) -> str | None:
    value = str(url or "").strip()
    if not value:
        return None
    match = re.match(
        r"^https://(?:[a-z]+\.)?investing\.com/equities/([a-z0-9.-]+)-technical/?(?:[?#].*)?$",
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
    profile_long_name = " ".join(str(normalized_profile.get("long_name") or "").split()).strip()
    profile_short_name = " ".join(str(normalized_profile.get("short_name") or "").split()).strip()
    item_company_name = " ".join(str(item.get("company_name") or "").split()).strip()
    aliases: list[str] = []
    for candidate in (profile_long_name, profile_short_name, item_company_name):
        if candidate and candidate not in aliases:
            aliases.append(candidate)
    return {
        "symbol": str(item.get("symbol") or "").strip(),
        "company_name": profile_long_name or profile_short_name or item_company_name,
        "aliases": aliases,
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
- If needed, verify the exact technical page using the `quote_url`, symbol, company name, exchange, country, region, and `aliases`.
- Locale variants like `https://www.investing.com/equities/...-technical` are allowed and will be normalized later.
- If the dedicated `-technical` page is unavailable, you may extract the same hourly values from the quote page's `Charttechnik` section.
- Read only the `Stündlich` / hourly view.
- Return the three summary labels exactly as one of: `Strong Buy`, `Buy`, `Neutral`, `Sell`, `Strong Sell`.
- Use `null` when a field is unavailable or cannot be verified.
- Do not infer hourly values from daily, weekly, monthly, 30-minute, or 5-hour tabs.
- Prefer exact issuer matches. Ignore unrelated issuers with similar names or tickers.

Requests:
{json.dumps(payload, indent=2, default=str)}
""".strip()


def _codex_targeted_prompt(request: dict[str, Any]) -> str:
    return f"""
You are extracting hourly Charttechnik summary signals from Investing.com for one exact stock.

Return JSON only matching the provided schema.

Use these exact pages first:
- {request.get("technical_url")}
- {request.get("quote_url")}

Need only the current `Stündlich` / hourly values for:
- `overview`
- `technical_indicators`
- `moving_averages`

Rules:
- You may use either the dedicated `-technical` page or the quote page's `Charttechnik` section.
- Locale variants like `https://www.investing.com/...` are allowed and will be normalized later.
- Use aliases when issuer punctuation differs, for example `J.B.` vs `JB`.
- Return labels exactly as one of: `Strong Buy`, `Buy`, `Neutral`, `Sell`, `Strong Sell`.
- If a field cannot be verified, return `null`.

Request:
{json.dumps(request, indent=2, default=str)}
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


def _run_codex_targeted_request(
    request: dict[str, Any],
    *,
    schema_path: Path,
    repo_root: Path,
    output_path: Path,
    timeout_s: float = 75.0,
) -> dict[str, dict[str, Any]]:
    prompt = _codex_targeted_prompt(request)
    cmd = [
        "codex",
        "--search",
        "exec",
        "--sandbox",
        "read-only",
        "--color",
        "never",
        "--ephemeral",
        "-",
    ]

    master_fd: int | None = None
    slave_fd: int | None = None
    try:
        master_fd, slave_fd = pty.openpty()
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=slave_fd,
            stderr=slave_fd,
            cwd=str(repo_root),
        )
        assert process.stdin is not None
        process.stdin.write(prompt.encode("utf-8"))
        process.stdin.close()

        chunks: list[str] = []
        deadline = time.monotonic() + timeout_s
        while True:
            if process.poll() is not None:
                try:
                    data = os.read(master_fd, 4096) if master_fd is not None else b""
                except OSError:
                    data = b""
                if data:
                    chunks.append(data.decode("utf-8", errors="replace"))
                    continue
                break

            remaining = deadline - time.monotonic()
            if remaining <= 0:
                process.kill()
                process.wait(timeout=5)
                return {}

            ready, _, _ = select.select([master_fd], [], [], min(1.0, remaining)) if master_fd is not None else ([], [], [])
            if master_fd in ready:
                try:
                    data = os.read(master_fd, 4096)
                except OSError:
                    data = b""
                if data:
                    chunks.append(data.decode("utf-8", errors="replace"))

        returncode = process.wait(timeout=5)
    except Exception:
        return {}
    finally:
        if slave_fd is not None:
            try:
                os.close(slave_fd)
            except OSError:
                pass
        if master_fd is not None:
            try:
                os.close(master_fd)
            except OSError:
                pass

    if returncode != 0:
        return {}

    try:
        payload = _extract_json_object("".join(chunks))
    except Exception:
        return {}
    if not isinstance(payload, dict):
        return {}

    results: dict[str, dict[str, Any]] = {}
    source_url = payload.get("source_url")
    results[str(request.get("lookup_key") or "")] = {
        "technical_page_url": _canonical_investing_technical_url(source_url) or request.get("technical_url"),
        "timeframe": _normalize_timeframe(payload.get("timeframe")) or "1h",
        "overview": _normalize_signal(payload.get("overview")),
        "technical_indicators": _normalize_signal(payload.get("technical_indicators")),
        "moving_averages": _normalize_signal(payload.get("moving_averages")),
    }
    return results


def _extract_json_object(text: str) -> dict[str, Any] | None:
    decoder = json.JSONDecoder()
    for index, char in enumerate(str(text or "")):
        if char != "{":
            continue
        try:
            payload, _ = decoder.raw_decode(text[index:])
        except ValueError:
            continue
        if isinstance(payload, dict):
            return payload
    return None


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
        unresolved_batch = []
        for request in batch:
            payload = batch_results.get(str(request.get("lookup_key") or "")) or {}
            if not any(
                (
                    _normalize_signal(payload.get("overview")),
                    _normalize_signal(payload.get("technical_indicators")),
                    _normalize_signal(payload.get("moving_averages")),
                )
            ):
                unresolved_batch.append(request)
        if len(batch) > 1 and unresolved_batch:
            for retry_index, request in enumerate(unresolved_batch, start=1):
                retry_output_path = Path(tempfile.gettempdir()) / f"stock_news_investing_technical_batch_{batch_index}_{retry_index}.json"
                batch_results.update(
                    _run_codex_batch(
                        [request],
                        schema_path=schema_path,
                        repo_root=repo_root,
                        output_path=retry_output_path,
                    )
                )
        remaining_unresolved_batch = []
        for request in batch:
            payload = batch_results.get(str(request.get("lookup_key") or "")) or {}
            if not any(
                (
                    _normalize_signal(payload.get("overview")),
                    _normalize_signal(payload.get("technical_indicators")),
                    _normalize_signal(payload.get("moving_averages")),
                )
            ):
                remaining_unresolved_batch.append(request)
        for retry_index, request in enumerate(remaining_unresolved_batch, start=1):
            targeted_output_path = Path(tempfile.gettempdir()) / f"stock_news_investing_technical_targeted_{batch_index}_{retry_index}.json"
            batch_results.update(
                _run_codex_targeted_request(
                    request,
                    schema_path=schema_path,
                    repo_root=repo_root,
                    output_path=targeted_output_path,
                )
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
