import json
from pathlib import Path


def test_breakout_schema_is_codex_compatible() -> None:
    schema = json.loads(Path("schemas/breakout_analysis.schema.json").read_text(encoding="utf-8"))

    assert schema["additionalProperties"] is False
    assert "analysis_error" in schema["required"]
    assert schema["properties"]["news_support"]["additionalProperties"] is False
    assert schema["properties"]["breakout_stance"]["additionalProperties"] is False
    assert schema["$defs"]["pointItem"]["additionalProperties"] is False
    assert schema["$defs"]["sourceItem"]["additionalProperties"] is False
    assert set(schema["$defs"]["sourceItem"]["required"]) == {"title", "url", "publisher", "published_at"}


def test_breakout_summary_schema_is_codex_compatible() -> None:
    schema = json.loads(Path("schemas/breakout_summary.schema.json").read_text(encoding="utf-8"))

    assert schema["additionalProperties"] is False
    assert set(schema["required"]) == {"summary", "news_support_explanation", "breakout_thesis", "analysis_error"}
