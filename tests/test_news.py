from pathlib import Path

import pandas as pd
from pandas import Timestamp

from stock_news import news as news_module


def test_news_history_falls_back_to_yfinance_and_reuses_cooldown(monkeypatch, tmp_path: Path) -> None:
    headlines_dir = tmp_path / "news" / "headlines"
    sentiment_dir = tmp_path / "news" / "daily_sentiment"

    calls = {"yfinance": 0}

    def fake_finnhub_fetch(symbol: str, start: str, end: str, api_key: str) -> list[dict]:
        raise RuntimeError("finnhub unavailable")

    def fake_yfinance_fetch(symbol: str) -> list[dict]:
        calls["yfinance"] += 1
        return [
            {
                "providerPublishTime": int(Timestamp.now(tz="UTC").timestamp()),
                "title": f"{symbol} rebounds on stronger outlook",
                "link": f"https://example.com/{symbol.lower()}",
                "publisher": "Example News",
            }
        ]

    monkeypatch.setattr(news_module, "finnhub_fetch", fake_finnhub_fetch)
    monkeypatch.setattr(news_module, "yfinance_fetch_news", fake_yfinance_fetch)

    summary_one = news_module.update_news_history(
        ["AXIA"],
        headlines_dir=headlines_dir,
        sentiment_dir=sentiment_dir,
        provider="auto",
        min_fetch_minutes=60,
        sleep_s=0.0,
    )
    summary_two = news_module.update_news_history(
        ["AXIA"],
        headlines_dir=headlines_dir,
        sentiment_dir=sentiment_dir,
        provider="auto",
        min_fetch_minutes=60,
        sleep_s=0.0,
    )

    assert summary_one["ok"] is True
    assert summary_two["ok"] is True
    assert calls["yfinance"] == 1

    headlines = pd.read_parquet(headlines_dir / "AXIA.parquet")
    assert len(headlines) == 1


def test_market_news_history_uses_rss_and_loads_context(monkeypatch, tmp_path: Path) -> None:
    market_dir = tmp_path / "news" / "market"

    def fake_rss_fetch(feed_name: str, url: str) -> list[dict]:
        return [
            {
                "headline": f"{feed_name} Iran conflict pushes oil prices higher",
                "summary": "Energy and defense shares react while airlines wobble.",
                "url": f"https://example.com/{feed_name}",
                "source": feed_name,
                "provider": "rss",
                "published_at": "Sat, 12 Apr 2026 10:00:00 GMT",
            }
        ]

    monkeypatch.setattr(news_module, "rss_fetch_news", fake_rss_fetch)

    summary = news_module.update_market_news_history(
        headlines_path=market_dir / "headlines.parquet",
        sentiment_path=market_dir / "daily_sentiment.parquet",
        min_fetch_minutes=0,
        sleep_s=0.0,
    )
    context = news_module.load_news_context(
        "AXIA",
        headlines_dir=tmp_path / "news" / "headlines",
        sentiment_dir=tmp_path / "news" / "daily_sentiment",
        market_headlines_path=market_dir / "headlines.parquet",
        market_sentiment_path=market_dir / "daily_sentiment.parquet",
        max_articles=10,
    )

    assert summary["ok"] is True
    assert context["market_articles"]


def test_company_profiles_are_cached(monkeypatch, tmp_path: Path) -> None:
    profiles_dir = tmp_path / "news" / "company_profiles"
    calls = {"profiles": 0}

    def fake_profile(symbol: str) -> dict:
        calls["profiles"] += 1
        return {"symbol": symbol, "sector": "Financial Services", "industry": "Insurance"}

    monkeypatch.setattr(news_module, "yfinance_fetch_profile", fake_profile)

    summary_one = news_module.update_company_profiles(["0QMG"], profiles_dir=profiles_dir, min_refresh_hours=999, sleep_s=0.0)
    summary_two = news_module.update_company_profiles(["0QMG"], profiles_dir=profiles_dir, min_refresh_hours=999, sleep_s=0.0)

    assert summary_one["ok"] is True
    assert summary_two["ok"] is True
    assert calls["profiles"] == 1
