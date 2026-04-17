from __future__ import annotations

import json
import re
import subprocess
import tempfile
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from stock_news.utils import read_json, write_json


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


def _new_lookup_payload() -> dict[str, Any]:
    return {
        "version": 1,
        "updated_at_utc": None,
        "entries": {},
    }


def _load_lookup_payload(path: Path) -> dict[str, Any]:
    if not path.exists():
        return _new_lookup_payload()
    try:
        payload = read_json(path)
    except Exception:
        return _new_lookup_payload()
    if not isinstance(payload, dict):
        return _new_lookup_payload()
    entries = payload.get("entries")
    if not isinstance(entries, dict):
        payload["entries"] = {}
    if "version" not in payload:
        payload["version"] = 1
    if "updated_at_utc" not in payload:
        payload["updated_at_utc"] = None
    return payload


def _build_request(item: dict[str, Any], profile: dict[str, Any] | None) -> dict[str, Any]:
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


def _entry_match_rank(entry: dict[str, Any], request: dict[str, Any]) -> int:
    if str(entry.get("symbol") or "").strip().upper() != str(request.get("symbol") or "").strip().upper():
        return -1

    score = 1
    if str(entry.get("exchange_code") or "").strip().upper() == str(request.get("exchange_code") or "").strip().upper():
        score += 2
    if str(entry.get("region") or "").strip().upper() == str(request.get("region") or "").strip().upper():
        score += 1
    if _normalize_company_name(entry.get("company_name") or "") == _normalize_company_name(request.get("company_name") or ""):
        score += 1
    return score


def _lookup_cached_url(payload: dict[str, Any], request: dict[str, Any]) -> str | None:
    entries = payload.get("entries", {}) or {}
    direct = entries.get(_lookup_key(request))
    direct_url = _canonical_investing_quote_url((direct or {}).get("resolved_url"))
    if direct_url:
        return direct_url

    best_match: tuple[int, str | None] = (-1, None)
    for entry in entries.values():
        if not isinstance(entry, dict):
            continue
        candidate_url = _canonical_investing_quote_url(entry.get("resolved_url"))
        if not candidate_url:
            continue
        rank = _entry_match_rank(entry, request)
        if rank > best_match[0]:
            best_match = (rank, candidate_url)
    return best_match[1]


def _store_lookup_entry(payload: dict[str, Any], request: dict[str, Any], resolved_url: str, *, provider: str) -> None:
    key = _lookup_key(request)
    payload.setdefault("entries", {})[key] = {
        "symbol": request.get("symbol"),
        "company_name": request.get("company_name"),
        "exchange_code": request.get("exchange_code"),
        "country": request.get("country"),
        "region": request.get("region"),
        "resolved_url": resolved_url,
        "provider": provider,
        "resolved_at_utc": _now_utc(),
    }


def _chunked(items: list[dict[str, Any]], size: int) -> list[list[dict[str, Any]]]:
    return [items[idx : idx + size] for idx in range(0, len(items), size)]


def _codex_lookup_prompt(requests_batch: list[dict[str, Any]]) -> str:
    payload = {"requests": requests_batch}
    return f"""
You are resolving exact stock quote pages on de.investing.com.

Return JSON only matching the provided schema.

Rules:
- Find the exact canonical stock quote page URL for each request.
- The URL must be on `https://de.investing.com/equities/...`.
- Do not return search pages, news, transcripts, forums, ownership pages, estimates pages, or any other subpages.
- Prefer an exact issuer and market match using symbol, company name, exchange, country, and region.
- If you cannot verify an exact quote page, return `null` for `resolved_url`.

Requests:
{json.dumps(payload, indent=2, default=str)}
""".strip()


def _run_codex_lookup_batch(
    requests_batch: list[dict[str, Any]],
    *,
    schema_path: Path,
    repo_root: Path,
    output_path: Path,
    timeout_s: float = 60.0,
) -> dict[str, str | None]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    prompt = _codex_lookup_prompt(requests_batch)
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

    results: dict[str, str | None] = {}
    for entry in payload.get("results", []) or []:
        if not isinstance(entry, dict):
            continue
        lookup_key = str(entry.get("lookup_key") or "").strip()
        canonical_url = _canonical_investing_quote_url(entry.get("resolved_url"))
        if lookup_key:
            results[lookup_key] = canonical_url
    return results


def ensure_investing_quote_urls(
    shortlist_items: list[dict[str, Any]],
    *,
    profiles_by_symbol: dict[str, dict[str, Any]] | None,
    lookup_path: Path,
    schema_path: Path,
    repo_root: Path,
    batch_size: int = 4,
) -> dict[str, Any]:
    payload = _load_lookup_payload(lookup_path)
    resolved_urls: dict[str, str] = {}
    requests_to_resolve: list[dict[str, Any]] = []
    cache_hits = 0

    for item in shortlist_items:
        symbol = str(item.get("symbol") or "").strip()
        if not symbol:
            continue
        request = _build_request(item, (profiles_by_symbol or {}).get(symbol) or {})
        request["lookup_key"] = _lookup_key(request)
        cached_url = _lookup_cached_url(payload, request)
        if cached_url:
            resolved_urls[symbol] = cached_url
            cache_hits += 1
            continue
        requests_to_resolve.append(request)

    resolved_with_codex = 0
    changed = False
    for batch_index, batch in enumerate(_chunked(requests_to_resolve, max(1, int(batch_size))), start=1):
        if not batch:
            continue
        output_path = Path(tempfile.gettempdir()) / f"stock_news_investing_quote_lookup_batch_{batch_index}.json"
        batch_results = _run_codex_lookup_batch(
            batch,
            schema_path=schema_path,
            repo_root=repo_root,
            output_path=output_path,
        )
        unresolved_batch = [request for request in batch if not _canonical_investing_quote_url(batch_results.get(str(request.get("lookup_key") or "")))]
        if len(batch) > 1 and unresolved_batch:
            for retry_index, request in enumerate(unresolved_batch, start=1):
                retry_output_path = Path(tempfile.gettempdir()) / f"stock_news_investing_quote_lookup_batch_{batch_index}_{retry_index}.json"
                batch_results.update(
                    _run_codex_lookup_batch(
                        [request],
                        schema_path=schema_path,
                        repo_root=repo_root,
                        output_path=retry_output_path,
                    )
                )
        batch_changed = False
        for request in batch:
            lookup_key = str(request.get("lookup_key") or _lookup_key(request))
            resolved_url = _canonical_investing_quote_url(batch_results.get(lookup_key))
            if not resolved_url:
                continue
            resolved_urls[str(request.get("symbol") or "")] = resolved_url
            _store_lookup_entry(payload, request, resolved_url, provider="codex_search")
            resolved_with_codex += 1
            changed = True
            batch_changed = True
        if batch_changed or (changed and not lookup_path.exists()):
            payload["updated_at_utc"] = _now_utc()
            write_json(lookup_path, payload)

    if (changed or not lookup_path.exists()) and not payload.get("updated_at_utc"):
        payload["updated_at_utc"] = _now_utc()
        write_json(lookup_path, payload)

    unresolved = sorted(
        str(item.get("symbol") or "")
        for item in shortlist_items
        if item.get("symbol") and str(item.get("symbol")) not in resolved_urls
    )
    return {
        "ok": not unresolved,
        "cache_hits": cache_hits,
        "resolved_with_codex": resolved_with_codex,
        "resolved_urls": resolved_urls,
        "unresolved_symbols": unresolved,
        "lookup_path": str(lookup_path),
    }
