from __future__ import annotations

import hashlib
import json
import re
import shutil
from pathlib import Path
from typing import Any


def safe_symbol_name(symbol: str) -> str:
    return str(symbol).replace("/", "_").replace("\\", "_")


def slugify(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]+", "_", str(value).strip().lower())
    return cleaned.strip("_") or "item"


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def manifest_hash(items: list[dict]) -> str:
    canonical = json.dumps(sorted(items, key=lambda item: item["filename"]), sort_keys=True)
    return hashlib.sha1(canonical.encode("utf-8")).hexdigest()


def replace_dir_contents(src: Path, dest: Path) -> None:
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(src, dest)


def coerce_scalar(value: str) -> Any:
    text = str(value).strip()
    if not text or text.upper() == "NULL":
        return None
    if re.fullmatch(r"-?\d+", text):
        try:
            return int(text)
        except ValueError:
            return text
    if re.fullmatch(r"-?\d*\.\d+(?:[eE][+-]?\d+)?", text) or re.fullmatch(r"-?\d+(?:[eE][+-]?\d+)", text):
        try:
            return float(text)
        except ValueError:
            return text
    return text
