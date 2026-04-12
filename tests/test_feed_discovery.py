from pathlib import Path

from stock_news.feed_discovery import parse_index_html, select_latest_feeds


def test_parse_index_html_and_select_latest() -> None:
    html = Path("tests/fixtures/source_index.html").read_text(encoding="utf-8")
    feeds = parse_index_html(html, base_url="https://stock.sdc-fried.de/")
    latest = select_latest_feeds(feeds)

    assert len(feeds) == 6
    assert len(latest) == 4
    names = [feed.filename for feed in latest]
    assert "2026-04-11_universe_3_US_Results.txt" in names
    assert "2026-04-11_universe_3_US_Results_CANDIDATES.txt" in names
    assert "2026-04-11_universe_5_EU_Results.txt" in names
    assert "2026-04-11_universe_5_EU_Results_CANDIDATES.txt" in names
