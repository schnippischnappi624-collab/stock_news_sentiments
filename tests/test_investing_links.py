from pathlib import Path

from stock_news import investing_links
from stock_news.utils import read_json


def test_ensure_investing_quote_urls_uses_lookup_cache(monkeypatch, tmp_path: Path) -> None:
    lookup_path = tmp_path / "investing_quote_links.json"
    lookup_path.write_text(
        """
        {
          "version": 1,
          "updated_at_utc": "2026-04-17T00:00:00+00:00",
          "entries": {
            "EU|SW|BRKN|burkhalter holding ag": {
              "symbol": "BRKN",
              "company_name": "Burkhalter Holding AG",
              "exchange_code": "SW",
              "country": "Switzerland",
              "region": "EU",
              "resolved_url": "https://de.investing.com/equities/burkhalter-holding-ag",
              "provider": "codex_search",
              "resolved_at_utc": "2026-04-17T00:00:00+00:00"
            }
          }
        }
        """.strip(),
        encoding="utf-8",
    )

    def fail_codex(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("codex lookup should not run on cache hit")

    monkeypatch.setattr(investing_links, "_run_codex_lookup_batch", fail_codex)

    summary = investing_links.ensure_investing_quote_urls(
        [
            {
                "symbol": "BRKN",
                "company_name": "Burkhalter Holding AG",
                "exchange_code": "SW",
                "country": "Switzerland",
                "source_rows": [{"_source_region": "EU"}],
            }
        ],
        profiles_by_symbol={},
        lookup_path=lookup_path,
        schema_path=tmp_path / "schema.json",
        repo_root=tmp_path,
    )

    assert summary["cache_hits"] == 1
    assert summary["resolved_with_codex"] == 0
    assert summary["unresolved_symbols"] == []
    assert summary["resolved_urls"]["BRKN"] == "https://de.investing.com/equities/burkhalter-holding-ag"


def test_ensure_investing_quote_urls_resolves_missing_and_updates_lookup(monkeypatch, tmp_path: Path) -> None:
    lookup_path = tmp_path / "investing_quote_links.json"

    def fake_codex(requests_batch, *, schema_path, repo_root, output_path):  # type: ignore[no-untyped-def]
        assert schema_path == tmp_path / "schema.json"
        assert repo_root == tmp_path
        return {
            investing_links._lookup_key(request): "https://de.investing.com/equities/burkhalter-holding-ag"
            for request in requests_batch
        }

    monkeypatch.setattr(investing_links, "_run_codex_lookup_batch", fake_codex)

    summary = investing_links.ensure_investing_quote_urls(
        [
            {
                "symbol": "BRKN",
                "company_name": "Burkhalter Holding AG",
                "exchange_code": "SW",
                "country": "Switzerland",
                "source_rows": [{"_source_region": "EU"}],
            }
        ],
        profiles_by_symbol={},
        lookup_path=lookup_path,
        schema_path=tmp_path / "schema.json",
        repo_root=tmp_path,
    )

    payload = read_json(lookup_path)

    assert summary["cache_hits"] == 0
    assert summary["resolved_with_codex"] == 1
    assert summary["resolved_urls"]["BRKN"] == "https://de.investing.com/equities/burkhalter-holding-ag"
    assert payload["entries"]["EU|SW|BRKN|burkhalter holding ag"]["resolved_url"] == "https://de.investing.com/equities/burkhalter-holding-ag"
