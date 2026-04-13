from pathlib import Path

from stock_news.feed_parser import parse_feed_text
from stock_news.models import FeedFile
from stock_news.shortlist import apply_min_price_eur_filter, build_shortlist


def _load_parsed_payloads() -> list[dict]:
    candidate_text = Path("tests/fixtures/2026-04-11_universe_3_US_Results_CANDIDATES.txt").read_text(encoding="utf-8")
    results_text = Path("tests/fixtures/2026-04-11_universe_3_US_Results.txt").read_text(encoding="utf-8")

    candidate_feed = FeedFile(
        filename="2026-04-11_universe_3_US_Results_CANDIDATES.txt",
        url="https://stock.sdc-fried.de/data/2026-04-11_universe_3_US_Results_CANDIDATES.txt",
        feed_date="2026-04-11",
        region="US",
        universe="3",
        kind="Results_CANDIDATES",
    )
    results_feed = FeedFile(
        filename="2026-04-11_universe_3_US_Results.txt",
        url="https://stock.sdc-fried.de/data/2026-04-11_universe_3_US_Results.txt",
        feed_date="2026-04-11",
        region="US",
        universe="3",
        kind="Results",
    )

    return [
        parse_feed_text(results_feed, results_text),
        parse_feed_text(candidate_feed, candidate_text),
    ]


def test_shortlist_keeps_entry_ready_and_top_candidates() -> None:
    shortlist = build_shortlist(_load_parsed_payloads(), extra_candidates=1)

    assert shortlist["entry_ready_count"] == 1
    assert shortlist["candidate_count"] == 1
    assert shortlist["symbols"][0]["symbol"] == "SPIR"
    assert shortlist["symbols"][1]["symbol"] == "AXIA"
    assert shortlist["symbols"][0]["metrics"]["entry_limit"] == 20.5
    assert shortlist["symbols"][0]["metrics"]["stop_init"] == 17.833519


def test_shortlist_filters_sub_eur_names_using_eur_conversion() -> None:
    shortlist = {
        "symbols": [
            {
                "symbol": "CHEAP",
                "company_name": "Cheap Nordic",
                "currency": "SEK",
                "exchange_code": "ST",
                "selection_bucket": "entry_ready",
                "entry_ready": True,
                "display_rank": 1,
                "metrics": {"close": 8.0},
                "source_rows": [{"_source_region": "EU"}],
            },
            {
                "symbol": "SAFE",
                "company_name": "Safe Nordic",
                "currency": "SEK",
                "exchange_code": "ST",
                "selection_bucket": "candidate",
                "entry_ready": False,
                "display_rank": 2,
                "metrics": {"close": 20.0},
                "source_rows": [{"_source_region": "EU"}],
            },
        ],
        "entry_ready_count": 1,
        "candidate_count": 1,
    }

    filtered = apply_min_price_eur_filter(
        shortlist,
        eur_rates_context={"rate_date": "2026-04-10", "rates": {"EUR": 1.0, "SEK": 10.0}},
        min_price_eur=1.0,
    )

    assert [item["symbol"] for item in filtered["symbols"]] == ["SAFE"]
    assert filtered["symbols"][0]["display_rank"] == 1
    assert filtered["entry_ready_count"] == 0
    assert filtered["candidate_count"] == 1
    assert filtered["temporary_filters"]["filtered_count"] == 1
    assert filtered["filtered_out_symbols"][0]["symbol"] == "CHEAP"
    assert filtered["filtered_out_symbols"][0]["current_price_eur"] == 0.8
