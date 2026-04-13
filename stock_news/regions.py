from __future__ import annotations

from typing import Any


REGION_ORDER: tuple[str, str] = ("EU", "US")


def normalize_region(value: Any) -> str | None:
    text = str(value or "").strip().upper()
    if text in REGION_ORDER:
        return text
    return None


def region_slug(value: Any) -> str:
    normalized = normalize_region(value)
    return normalized.lower() if normalized else "global"
