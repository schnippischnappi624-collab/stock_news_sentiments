from pathlib import Path

from stock_news.feed_parser import parse_feed_text
from stock_news.models import FeedFile


def test_parse_candidate_table_with_wrapped_company_name() -> None:
    text = Path("tests/fixtures/2026-04-11_universe_3_US_Results_CANDIDATES.txt").read_text(encoding="utf-8")
    feed = FeedFile(
        filename="2026-04-11_universe_3_US_Results_CANDIDATES.txt",
        url="https://stock.sdc-fried.de/data/2026-04-11_universe_3_US_Results_CANDIDATES.txt",
        feed_date="2026-04-11",
        region="US",
        universe="3",
        kind="Results_CANDIDATES",
    )

    parsed = parse_feed_text(feed, text)

    assert parsed["run_date"] == "2026-04-11"
    assert parsed["table_count"] == 1
    rows = parsed["tables"][0]["rows"]
    assert rows[1]["company_name"] == "Lionsgate Studios Holding Corp. (to be renamed Lionsgate Studios Corp.)"
    assert rows[0]["invest_score"] == 4.34


def test_parse_results_file_with_multiple_tables() -> None:
    text = Path("tests/fixtures/2026-04-11_universe_3_US_Results.txt").read_text(encoding="utf-8")
    feed = FeedFile(
        filename="2026-04-11_universe_3_US_Results.txt",
        url="https://stock.sdc-fried.de/data/2026-04-11_universe_3_US_Results.txt",
        feed_date="2026-04-11",
        region="US",
        universe="3",
        kind="Results",
    )

    parsed = parse_feed_text(feed, text)

    assert parsed["table_count"] == 2
    assert parsed["tables"][0]["table_key"] == "universe_3_us_entry_ready_neu_heute"
    assert parsed["tables"][1]["table_key"] == "universe_3_us_entry_stop_targets_neu_heute"
    assert parsed["tables"][0]["rows"][0]["state"] == "ENTRY_READY"


def test_parse_eu_style_results_without_row_separators() -> None:
    text = """============================================================
Universe 5 EU - ENTRY_READY (neu, heute)
RUN_DATE=2026-04-11 TZ=Europe/Berlin
============================================================
┌───────────┬───────────────┬────────┬────────────────────┬─────────────┐
│ asof_date │ exchange_code │ symbol │ company_name       │ state       │
├───────────┼───────────────┼────────┼────────────────────┼─────────────┤
│ 20260408  │ ST            │ LOYAL  │ Loyal Solutions AS │ ENTRY_READY │
│ 20260408  │ PA            │ ALRIB  │ Riber S.A          │ ENTRY_READY │
└───────────┴───────────────┴────────┴────────────────────┴─────────────┘
"""
    feed = FeedFile(
        filename="2026-04-11_universe_5_EU_Results.txt",
        url="https://stock.sdc-fried.de/data/2026-04-11_universe_5_EU_Results.txt",
        feed_date="2026-04-11",
        region="EU",
        universe="5",
        kind="Results",
    )

    parsed = parse_feed_text(feed, text)

    assert parsed["table_count"] == 1
    rows = parsed["tables"][0]["rows"]
    assert len(rows) == 2
    assert rows[0]["symbol"] == "LOYAL"
    assert rows[1]["symbol"] == "ALRIB"
