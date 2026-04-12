from __future__ import annotations

import re
from typing import Any

from stock_news.models import FeedFile
from stock_news.utils import coerce_scalar, slugify

META_RE = re.compile(r"RUN_DATE=(?P<run_date>\d{4}-\d{2}-\d{2})(?:\s+TZ=(?P<timezone>\S+))?")


def normalize_column_name(name: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9]+", "_", str(name).strip().lower())
    return normalized.strip("_")


def _split_box_row(line: str) -> list[str]:
    stripped = line.rstrip("\n")
    if not stripped.startswith("│"):
        raise ValueError(f"not a table row: {line!r}")
    return [cell.rstrip() for cell in stripped.split("│")[1:-1]]


def _finalize_multiline_row(parts: list[list[str]], columns: list[str]) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for idx, column in enumerate(columns):
        values = []
        for row in parts:
            if idx >= len(row):
                continue
            value = row[idx].strip()
            if value:
                values.append(value)
        merged[column] = coerce_scalar(" ".join(values))
    return merged


def parse_box_table(lines: list[str]) -> dict[str, Any]:
    if len(lines) < 4:
        raise ValueError("box table is too short")

    header_cells = _split_box_row(lines[1])
    columns = [normalize_column_name(cell) for cell in header_cells]

    rows: list[dict[str, Any]] = []
    current: list[list[str]] = []
    for line in lines[3:]:
        if line.startswith("│"):
            cells = _split_box_row(line)
            if not current:
                current = [cells]
                continue

            # Wrapped rows keep the first cell empty, while true table rows start
            # a fresh record with a populated first column.
            if str(cells[0]).strip():
                rows.append(_finalize_multiline_row(current, columns))
                current = [cells]
            else:
                current.append(cells)
            continue
        if line.startswith("├") or line.startswith("└"):
            if current and line.startswith("└"):
                rows.append(_finalize_multiline_row(current, columns))
                current = []
            if line.startswith("└"):
                break

    return {"columns": columns, "rows": rows}


def _extract_title(preceding_lines: list[str]) -> str:
    for raw in reversed(preceding_lines):
        stripped = raw.strip()
        if not stripped:
            continue
        if stripped.startswith(("┌", "│", "├", "└")):
            continue
        if set(stripped) == {"="}:
            continue
        if META_RE.search(stripped):
            continue
        return stripped
    return "table"


def parse_feed_text(feed: FeedFile, text: str) -> dict[str, Any]:
    lines = text.splitlines()
    file_run_date = None
    file_timezone = None
    for line in lines:
        match = META_RE.search(line)
        if match:
            file_run_date = match.group("run_date")
            file_timezone = match.group("timezone")
            break

    tables: list[dict[str, Any]] = []
    idx = 0
    while idx < len(lines):
        line = lines[idx]
        if not line.startswith("┌"):
            idx += 1
            continue

        end_idx = idx
        while end_idx < len(lines) and not lines[end_idx].startswith("└"):
            end_idx += 1
        if end_idx >= len(lines):
            raise ValueError(f"unterminated table in {feed.filename}")

        table_lines = lines[idx : end_idx + 1]
        preceding = lines[max(0, idx - 6) : idx]
        title = _extract_title(preceding)
        parsed = parse_box_table(table_lines)
        table = {
            "title": title,
            "table_key": slugify(title),
            "columns": parsed["columns"],
            "rows": parsed["rows"],
            "row_count": len(parsed["rows"]),
        }
        tables.append(table)
        idx = end_idx + 1

    return {
        "feed": feed.to_dict(),
        "run_date": file_run_date,
        "timezone": file_timezone,
        "table_count": len(tables),
        "tables": tables,
    }
