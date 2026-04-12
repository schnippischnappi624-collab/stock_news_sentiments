from __future__ import annotations

import re
from urllib.parse import urljoin

import requests

from stock_news.models import FeedFile

INDEX_TIMEOUT_S = 30
FILE_RE = re.compile(
    r"(?P<feed_date>\d{4}-\d{2}-\d{2})_universe_(?P<universe>\d+)_(?P<region>[A-Z]+)_(?P<kind>Results(?:_CANDIDATES)?)\.txt$"
)


def parse_index_html(html: str, *, base_url: str) -> list[FeedFile]:
    feeds: dict[str, FeedFile] = {}
    for match in re.finditer(r'href="([^"]+\.txt)"', html, flags=re.IGNORECASE):
        href = match.group(1)
        filename = href.rsplit("/", 1)[-1]
        parsed = FILE_RE.match(filename)
        if not parsed:
            continue
        feed = FeedFile(
            filename=filename,
            url=urljoin(base_url, href),
            feed_date=parsed.group("feed_date"),
            region=parsed.group("region"),
            universe=parsed.group("universe"),
            kind=parsed.group("kind"),
        )
        feeds[feed.filename] = feed
    return sorted(feeds.values(), key=lambda item: item.filename)


def select_latest_feeds(feeds: list[FeedFile]) -> list[FeedFile]:
    selected: dict[tuple[str, str], FeedFile] = {}
    for feed in sorted(feeds, key=lambda item: (item.feed_date, item.filename)):
        selected[feed.manifest_key] = feed
    return sorted(selected.values(), key=lambda item: (item.region, item.kind))


def discover_latest_feeds(base_url: str) -> list[FeedFile]:
    response = requests.get(base_url, timeout=INDEX_TIMEOUT_S)
    response.raise_for_status()
    feeds = parse_index_html(response.text, base_url=base_url)
    return select_latest_feeds(feeds)


def download_feed_text(url: str) -> str:
    response = requests.get(url, timeout=INDEX_TIMEOUT_S)
    response.raise_for_status()
    return response.text
