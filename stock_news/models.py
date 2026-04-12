from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass(frozen=True)
class FeedFile:
    filename: str
    url: str
    feed_date: str
    region: str
    universe: str
    kind: str

    @property
    def manifest_key(self) -> tuple[str, str]:
        return (self.region, self.kind)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class RunContext:
    run_id: str
    manifest_hash: str
    feed_dates: list[str]
    feeds: list[FeedFile] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "manifest_hash": self.manifest_hash,
            "feed_dates": self.feed_dates,
            "feeds": [feed.to_dict() for feed in self.feeds],
        }
