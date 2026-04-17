from pathlib import Path

from stock_news import investing_technical


def test_fetch_investing_technical_signals_normalizes_and_maps_results(monkeypatch, tmp_path: Path) -> None:
    def fake_run_codex(requests_batch, **kwargs) -> dict:
        request = requests_batch[0]
        return {
            request["lookup_key"]: {
                "technical_page_url": "https://de.investing.com/equities/burkhalter-holding-ag-technical",
                "timeframe": "Stündlich",
                "overview": "strong buy",
                "technical_indicators": "buy",
                "moving_averages": "neutral",
            }
        }

    monkeypatch.setattr(investing_technical, "_run_codex_batch", fake_run_codex)

    summary = investing_technical.fetch_investing_technical_signals(
        [
            {
                "symbol": "BRKN",
                "company_name": "Burkhalter Holding AG",
                "exchange_code": "SW",
                "country": "Switzerland",
                "region": "EU",
            }
        ],
        profiles_by_symbol={"BRKN": {"long_name": "Burkhalter Holding AG", "country": "Switzerland"}},
        resolved_quote_urls={"BRKN": "https://de.investing.com/equities/burkhalter-holding-ag"},
        schema_path=tmp_path / "investing_technical.schema.json",
        repo_root=tmp_path,
    )

    assert summary["resolved_symbols"] == 1
    assert summary["unresolved_symbols"] == []
    assert summary["signals_by_symbol"]["BRKN"]["timeframe"] == "1h"
    assert summary["signals_by_symbol"]["BRKN"]["overview"] == "Strong Buy"
    assert summary["signals_by_symbol"]["BRKN"]["technical_indicators"] == "Buy"
    assert summary["signals_by_symbol"]["BRKN"]["moving_averages"] == "Neutral"
    assert summary["signals_by_symbol"]["BRKN"]["technical_page_url"] == "https://de.investing.com/equities/burkhalter-holding-ag-technical"


def test_fetch_investing_technical_signals_marks_missing_quote_urls_unresolved(tmp_path: Path) -> None:
    summary = investing_technical.fetch_investing_technical_signals(
        [
            {
                "symbol": "MISS",
                "company_name": "Missing Corp",
                "exchange_code": "NASDAQ",
                "country": "United States",
                "region": "US",
            }
        ],
        profiles_by_symbol={},
        resolved_quote_urls={},
        schema_path=tmp_path / "investing_technical.schema.json",
        repo_root=tmp_path,
    )

    assert summary["resolved_symbols"] == 0
    assert summary["signals_by_symbol"] == {}
    assert summary["unresolved_symbols"] == ["MISS"]
