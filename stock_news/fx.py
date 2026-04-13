from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

ECB_90D_URL = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist-90d.xml"
ECB_NS = {
    "gesmes": "http://www.gesmes.org/xml/2002-08-01",
    "ecb": "http://www.ecb.int/vocabulary/2002-08-01/eurofxref",
}


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_ecb_rates_xml(payload: bytes | str) -> dict[str, Any]:
    root = ET.fromstring(payload)
    rates_by_date: dict[str, dict[str, float]] = {}

    for daily_cube in root.findall(".//ecb:Cube[@time]", ECB_NS):
        date = str(daily_cube.attrib.get("time") or "").strip()
        if not date:
            continue
        rates = {"EUR": 1.0}
        for rate_cube in daily_cube.findall("ecb:Cube[@currency]", ECB_NS):
            currency = str(rate_cube.attrib.get("currency") or "").strip().upper()
            rate = rate_cube.attrib.get("rate")
            if not currency or rate in {None, ""}:
                continue
            try:
                rates[currency] = float(rate)
            except (TypeError, ValueError):
                continue
        rates_by_date[date] = rates

    latest_date = max(rates_by_date) if rates_by_date else None
    return {
        "provider": "ecb",
        "base_currency": "EUR",
        "latest_date": latest_date,
        "fetched_at_utc": _now_utc(),
        "rates_by_date": rates_by_date,
    }


def fetch_ecb_rates(*, url: str = ECB_90D_URL, timeout: float = 30.0) -> dict[str, Any]:
    response = requests.get(url, timeout=timeout, headers={"User-Agent": "stock-news/0.1"})
    response.raise_for_status()
    return parse_ecb_rates_xml(response.content)


def load_or_update_ecb_rates(
    *,
    cache_path: Path,
    min_refresh_hours: int = 12,
    timeout: float = 30.0,
) -> dict[str, Any]:
    cache_path.parent.mkdir(parents=True, exist_ok=True)

    cached_payload: dict[str, Any] | None = None
    if cache_path.exists():
        try:
            payload = json.loads(cache_path.read_text(encoding="utf-8"))
            if isinstance(payload, dict):
                cached_payload = payload
        except Exception:
            cached_payload = None

    if cached_payload:
        fetched_at = str(cached_payload.get("fetched_at_utc") or "").strip()
        if fetched_at:
            try:
                age_hours = (datetime.now(timezone.utc) - datetime.fromisoformat(fetched_at)).total_seconds() / 3600.0
                if age_hours < float(max(1, min_refresh_hours)):
                    return cached_payload
            except ValueError:
                pass

    try:
        payload = fetch_ecb_rates(timeout=timeout)
        cache_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        return payload
    except Exception:
        if cached_payload:
            return cached_payload
        return {}


def select_eur_rates(payload: dict[str, Any], *, target_date: str | None = None) -> dict[str, Any]:
    rates_by_date = payload.get("rates_by_date") if isinstance(payload, dict) else None
    if not isinstance(rates_by_date, dict) or not rates_by_date:
        return {}

    selected_date = None
    if target_date:
        eligible_dates = [date for date in rates_by_date if date <= str(target_date)]
        if eligible_dates:
            selected_date = max(eligible_dates)

    if selected_date is None:
        selected_date = str(payload.get("latest_date") or max(rates_by_date))

    rates = rates_by_date.get(selected_date) or {}
    if not isinstance(rates, dict) or not rates:
        return {}

    return {
        "provider": payload.get("provider") or "ecb",
        "base_currency": "EUR",
        "rate_date": selected_date,
        "rates": rates,
    }


def convert_to_eur(amount: Any, currency: str | None, eur_rates_context: dict[str, Any] | None) -> float | None:
    if amount in {None, ""}:
        return None
    try:
        numeric_amount = float(amount)
    except (TypeError, ValueError):
        return None

    normalized_currency = str(currency or "").strip().upper()
    if not normalized_currency or normalized_currency == "EUR":
        return numeric_amount

    if not isinstance(eur_rates_context, dict):
        return None
    rates = eur_rates_context.get("rates")
    if not isinstance(rates, dict):
        return None
    rate = rates.get(normalized_currency)
    if rate in {None, "", 0}:
        return None
    try:
        return numeric_amount / float(rate)
    except (TypeError, ValueError, ZeroDivisionError):
        return None
