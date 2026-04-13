from pathlib import Path

from stock_news import pipeline
from stock_news.models import FeedFile
from stock_news.utils import read_json


def test_daily_run_pipeline_with_fixtures(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("STOCK_NEWS_ROOT", str(tmp_path))
    (tmp_path / "pyproject.toml").write_text("[tool.poetry]\nname='tmp'\nversion='0.0.0'\n", encoding="utf-8")
    (tmp_path / "schemas").mkdir(parents=True, exist_ok=True)
    (tmp_path / "schemas" / "breakout_analysis.schema.json").write_text("{}", encoding="utf-8")

    us_results = Path("tests/fixtures/2026-04-11_universe_3_US_Results.txt").read_text(encoding="utf-8")
    us_candidates = Path("tests/fixtures/2026-04-11_universe_3_US_Results_CANDIDATES.txt").read_text(encoding="utf-8")
    eu_results = us_results.replace("Universe 3 US", "Universe 5 EU").replace("SPIR", "NXT").replace("US", "EU", 2)
    eu_candidates = us_candidates.replace("Universe 3 US", "Universe 5 EU").replace("AXIA", "ALV").replace("LION", "RHM").replace("US", "EU", 2)

    feeds = [
        FeedFile(
            filename="2026-04-11_universe_3_US_Results.txt",
            url="fixture://us-results",
            feed_date="2026-04-11",
            region="US",
            universe="3",
            kind="Results",
        ),
        FeedFile(
            filename="2026-04-11_universe_3_US_Results_CANDIDATES.txt",
            url="fixture://us-candidates",
            feed_date="2026-04-11",
            region="US",
            universe="3",
            kind="Results_CANDIDATES",
        ),
        FeedFile(
            filename="2026-04-11_universe_5_EU_Results.txt",
            url="fixture://eu-results",
            feed_date="2026-04-11",
            region="EU",
            universe="5",
            kind="Results",
        ),
        FeedFile(
            filename="2026-04-11_universe_5_EU_Results_CANDIDATES.txt",
            url="fixture://eu-candidates",
            feed_date="2026-04-11",
            region="EU",
            universe="5",
            kind="Results_CANDIDATES",
        ),
    ]

    download_map = {
        "fixture://us-results": us_results,
        "fixture://us-candidates": us_candidates,
        "fixture://eu-results": eu_results,
        "fixture://eu-candidates": eu_candidates,
    }

    def fake_discover(base_url: str) -> list[FeedFile]:
        return feeds

    def fake_download(url: str) -> str:
        return download_map[url]

    def fake_update_news_history(*args, **kwargs) -> dict:
        return {"ok": True, "symbols_total": 4, "symbols_ok": 4, "symbols_failed": 0, "providers": {"fixture": 4}}

    def fake_update_market_news_history(*args, **kwargs) -> dict:
        return {"ok": True, "provider": "fixture", "feeds_total": 2, "articles_appended": 3, "skipped": False}

    def fake_update_company_profiles(*args, **kwargs) -> dict:
        return {"ok": True, "symbols_total": 4, "profiles_fetched": 4, "profiles_skipped": 0, "profiles_errors": 0}

    monkeypatch.setattr(pipeline, "discover_latest_feeds", fake_discover)
    monkeypatch.setattr(pipeline, "download_feed_text", fake_download)
    monkeypatch.setattr(pipeline, "update_news_history", fake_update_news_history)
    monkeypatch.setattr(pipeline, "update_market_news_history", fake_update_market_news_history)
    monkeypatch.setattr(pipeline, "update_company_profiles", fake_update_company_profiles)

    rc_eu = pipeline.daily_run_command(
        base_url="https://stock.sdc-fried.de/",
        force=True,
        region="EU",
        extra_candidates=1,
        max_news=5,
        analysis_mode="python",
    )
    rc_us = pipeline.daily_run_command(
        base_url="https://stock.sdc-fried.de/",
        force=True,
        region="US",
        extra_candidates=1,
        max_news=5,
        analysis_mode="python",
    )
    rc_us_skip = pipeline.daily_run_command(
        base_url="https://stock.sdc-fried.de/",
        force=False,
        region="US",
        extra_candidates=1,
        max_news=5,
        analysis_mode="python",
    )

    assert rc_eu == 0
    assert rc_us == 0
    assert rc_us_skip == 0
    assert (tmp_path / "README.md").exists()
    assert (tmp_path / "latest" / "dashboard.md").exists()
    assert (tmp_path / "latest" / "best_candidates.md").exists()
    assert (tmp_path / "latest" / "eu" / "analysis" / "markdown" / "NXT.md").exists()
    assert (tmp_path / "latest" / "us" / "analysis" / "markdown" / "SPIR.md").exists()
    eu_shortlist = read_json(tmp_path / "latest" / "eu" / "shortlist" / "shortlist.json")
    us_shortlist = read_json(tmp_path / "latest" / "us" / "shortlist" / "shortlist.json")
    assert len(eu_shortlist["symbols"]) == 2
    assert len(us_shortlist["symbols"]) == 2
    spir_report = read_json(tmp_path / "latest" / "us" / "analysis" / "json" / "SPIR.json")
    assert spir_report["analysis_mode"] == "python"
    assert spir_report["analysis_error"] is None
    assert "scorecard" in spir_report
    assert (tmp_path / "latest" / "us" / "analysis" / "evidence" / "SPIR.json").exists()
    summary = read_json(tmp_path / "latest" / "us" / "run_summary.json")
    assert summary["news_summary"]["market_news"]["ok"] is True
    best_candidates = (tmp_path / "latest" / "best_candidates.md").read_text(encoding="utf-8")
    assert "## EU Best Scoring Candidates" in best_candidates
    assert "## US Best Scoring Candidates" in best_candidates
    assert "[SPIR](us/analysis/markdown/SPIR.md)" in best_candidates
    root_readme = (tmp_path / "README.md").read_text(encoding="utf-8")
    assert "## EU Best Scoring Candidates" in root_readme
    assert "## US Best Scoring Candidates" in root_readme
    assert "[SPIR](latest/us/analysis/markdown/SPIR.md)" in root_readme
    assert "[NXT](latest/eu/analysis/markdown/NXT.md)" in root_readme
    assert len(list((tmp_path / "artifacts" / "daily_runs").iterdir())) == 2
