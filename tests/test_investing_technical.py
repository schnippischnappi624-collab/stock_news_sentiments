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


def test_fetch_investing_technical_signals_retries_unresolved_batch_items(monkeypatch, tmp_path: Path) -> None:
    calls: list[list[str]] = []

    def fake_run_codex(requests_batch, **kwargs) -> dict:
        calls.append([request["symbol"] for request in requests_batch])
        request = requests_batch[0]
        if len(requests_batch) > 1:
            return {
                requests_batch[0]["lookup_key"]: {
                    "technical_page_url": "https://de.investing.com/equities/first-name-technical",
                    "timeframe": "Stündlich",
                    "overview": "Buy",
                    "technical_indicators": "Buy",
                    "moving_averages": "Buy",
                }
            }
        return {
            request["lookup_key"]: {
                "technical_page_url": "https://de.investing.com/equities/second-name-technical",
                "timeframe": "Stündlich",
                "overview": "Strong Buy",
                "technical_indicators": "Strong Buy",
                "moving_averages": "Buy",
            }
        }

    monkeypatch.setattr(investing_technical, "_run_codex_batch", fake_run_codex)

    summary = investing_technical.fetch_investing_technical_signals(
        [
            {"symbol": "ONE", "company_name": "First Name", "exchange_code": "SW", "country": "Switzerland", "region": "EU"},
            {"symbol": "TWO", "company_name": "Second Name", "exchange_code": "SW", "country": "Switzerland", "region": "EU"},
        ],
        profiles_by_symbol={},
        resolved_quote_urls={
            "ONE": "https://de.investing.com/equities/first-name",
            "TWO": "https://de.investing.com/equities/second-name",
        },
        schema_path=tmp_path / "investing_technical.schema.json",
        repo_root=tmp_path,
        batch_size=2,
    )

    assert calls == [["ONE", "TWO"], ["TWO"]]
    assert summary["resolved_symbols"] == 2
    assert summary["unresolved_symbols"] == []
    assert summary["signals_by_symbol"]["TWO"]["overview"] == "Strong Buy"


def test_fetch_investing_technical_signals_uses_targeted_retry_for_remaining_unresolved(monkeypatch, tmp_path: Path) -> None:
    def fake_run_codex(requests_batch, **kwargs) -> dict:
        return {}

    def fake_run_targeted(request, **kwargs) -> dict:
        return {
            request["lookup_key"]: {
                "technical_page_url": "https://www.investing.com/equities/j.b.-hunt-transpo-technical",
                "timeframe": "Hourly",
                "overview": "Sell",
                "technical_indicators": "Strong Sell",
                "moving_averages": "Neutral",
            }
        }

    monkeypatch.setattr(investing_technical, "_run_codex_batch", fake_run_codex)
    monkeypatch.setattr(investing_technical, "_run_codex_targeted_request", fake_run_targeted)

    summary = investing_technical.fetch_investing_technical_signals(
        [
            {"symbol": "JBHT", "company_name": "JB Hunt Transport Services Inc", "exchange_code": "NASDAQ", "country": "United States", "region": "US"}
        ],
        profiles_by_symbol={"JBHT": {"long_name": "J.B. Hunt Transport Services, Inc.", "short_name": "J.B. Hunt", "country": "United States"}},
        resolved_quote_urls={"JBHT": "https://de.investing.com/equities/j.b.-hunt-transpo"},
        schema_path=tmp_path / "investing_technical.schema.json",
        repo_root=tmp_path,
    )

    assert summary["resolved_symbols"] == 1
    assert summary["unresolved_symbols"] == []
    assert summary["signals_by_symbol"]["JBHT"]["overview"] == "Sell"
    assert summary["signals_by_symbol"]["JBHT"]["technical_indicators"] == "Strong Sell"
    assert summary["signals_by_symbol"]["JBHT"]["moving_averages"] == "Neutral"
    assert summary["signals_by_symbol"]["JBHT"]["technical_page_url"] == "https://de.investing.com/equities/j.b.-hunt-transpo-technical"
