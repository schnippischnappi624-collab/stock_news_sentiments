from pathlib import Path

from stock_news.feed_parser import parse_feed_text
from stock_news.models import FeedFile
from stock_news.shortlist import build_shortlist


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
