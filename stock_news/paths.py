from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from stock_news.regions import region_slug


def _find_repo_root(start: Path) -> Path:
    env = os.getenv("STOCK_NEWS_ROOT")
    if env:
        return Path(env).expanduser().resolve()

    p = start.resolve()
    for parent in [p, *p.parents]:
        if (parent / "pyproject.toml").exists() or (parent / ".git").exists():
            return parent
    return start.resolve().parents[1]


@dataclass(frozen=True)
class Paths:
    root: Path

    @property
    def artifacts_dir(self) -> Path:
        return self.root / "artifacts"

    @property
    def daily_runs_dir(self) -> Path:
        return self.artifacts_dir / "daily_runs"

    @property
    def maintenance_dir(self) -> Path:
        return self.artifacts_dir / "maintenance"

    @property
    def latest_dir(self) -> Path:
        return self.root / "latest"

    def latest_region_dir(self, region: str) -> Path:
        return self.latest_dir / region_slug(region)

    @property
    def news_root(self) -> Path:
        return self.root / "news"

    @property
    def news_headlines_dir(self) -> Path:
        return self.news_root / "headlines"

    @property
    def news_daily_sentiment_dir(self) -> Path:
        return self.news_root / "daily_sentiment"

    @property
    def news_market_dir(self) -> Path:
        return self.news_root / "market"

    @property
    def market_headlines_path(self) -> Path:
        return self.news_market_dir / "headlines.parquet"

    @property
    def market_daily_sentiment_path(self) -> Path:
        return self.news_market_dir / "daily_sentiment.parquet"

    @property
    def company_profiles_dir(self) -> Path:
        return self.news_root / "company_profiles"

    @property
    def fx_cache_dir(self) -> Path:
        return self.maintenance_dir / "fx"

    @property
    def ecb_fx_cache_path(self) -> Path:
        return self.fx_cache_dir / "ecb_eurofxref_hist_90d.json"

    @property
    def secrets_dir(self) -> Path:
        return self.root / "secrets"

    @property
    def finnhub_key_path(self) -> Path:
        return self.secrets_dir / "finnhub_key.txt"

    @property
    def schemas_dir(self) -> Path:
        return self.root / "schemas"

    @property
    def scripts_dir(self) -> Path:
        return self.root / "stock_news" / "scripts"

    @property
    def tests_dir(self) -> Path:
        return self.root / "tests"

    @property
    def last_manifest_path(self) -> Path:
        return self.maintenance_dir / "last_processed_manifest.json"

    @property
    def active_manifest_path(self) -> Path:
        return self.maintenance_dir / "active_manifest.json"

    @property
    def investing_quote_links_path(self) -> Path:
        return self.maintenance_dir / "investing_quote_links.json"

    def last_manifest_path_for_region(self, region: str | None = None) -> Path:
        if not region:
            return self.last_manifest_path
        return self.maintenance_dir / f"last_processed_manifest_{region_slug(region)}.json"

    def active_manifest_path_for_region(self, region: str | None = None) -> Path:
        if not region:
            return self.active_manifest_path
        return self.maintenance_dir / f"active_manifest_{region_slug(region)}.json"

    def daily_run_dir(self, run_id: str) -> Path:
        return self.daily_runs_dir / run_id

    def ensure_base_dirs(self) -> None:
        for path in [
            self.artifacts_dir,
            self.daily_runs_dir,
            self.maintenance_dir,
            self.latest_dir,
            self.news_root,
            self.news_headlines_dir,
            self.news_daily_sentiment_dir,
            self.news_market_dir,
            self.company_profiles_dir,
            self.fx_cache_dir,
            self.schemas_dir,
            self.scripts_dir,
        ]:
            path.mkdir(parents=True, exist_ok=True)


def get_paths() -> Paths:
    return Paths(root=_find_repo_root(Path(__file__).parent))
