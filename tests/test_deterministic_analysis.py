from stock_news.deterministic_analysis import generate_python_report


def test_generate_python_report_is_deterministic_and_signal_driven() -> None:
    item = {
        "symbol": "SPIR",
        "company_name": "Spire Global Inc",
        "selection_bucket": "entry_ready",
        "selection_reason": "setup+breakout",
        "entry_ready": True,
        "metrics": {
            "close": 21.56,
            "hh20_prev": 20.50,
            "vol_anom": 3.35,
            "atr14": 1.77,
        },
        "source_rows": [
            {
                "ema20": 14.68,
                "ema50": 12.44,
                "ema200": 10.87,
                "_source_url": "https://stock.sdc-fried.de/data/2026-04-11_universe_3_US_Results.txt",
                "_table_title": "Universe 3 US - ENTRY_READY",
                "_source_feed_date": "2026-04-11",
            }
        ],
    }
    news_context = {
        "symbol": "SPIR",
        "articles": [
            {
                "datetime_utc": "2026-04-09T00:00:00Z",
                "headline": "Spire Global Announces $70.0 Million Private Placement",
                "summary": "The financing adds capital but increases share count.",
                "url": "https://example.com/private-placement",
                "source": "ExampleWire",
                "provider": "fixture",
                "sentiment": -0.1,
            },
            {
                "datetime_utc": "2026-03-30T00:00:00Z",
                "headline": "Spire Global Successfully Launches Ten Satellites on SpaceX Mission",
                "summary": "The launch expands the company's data constellation.",
                "url": "https://example.com/launch",
                "source": "ExampleWire",
                "provider": "fixture",
                "sentiment": 0.2,
            },
        ],
        "daily_sentiment": [
            {"date": "2026-04-09", "sentiment_mean": 0.15, "n_articles": 1},
            {"date": "2026-04-08", "sentiment_mean": 0.10, "n_articles": 1},
            {"date": "2026-04-07", "sentiment_mean": 0.08, "n_articles": 1},
            {"date": "2026-04-04", "sentiment_mean": -0.05, "n_articles": 1},
        ],
        "market_articles": [
            {
                "datetime_utc": "2026-04-10T00:00:00Z",
                "headline": "Iran conflict lifts oil prices and defense stocks",
                "summary": "Broader geopolitical tension boosts defense sentiment.",
                "url": "https://example.com/macro",
                "source": "Example Macro",
                "provider": "fixture",
                "sentiment": 0.05,
            }
        ],
        "company_profile": {"sector": "Technology", "industry": "Aerospace & Defense", "provider": "fixture"},
    }

    report = generate_python_report(item, news_context, analysis_date="2026-04-12")

    assert report["analysis_mode"] == "python"
    assert report["analysis_error"] is None
    assert report["breakout_stance"]["score_0_to_100"] >= 55
    assert any("private placement" in entry["point"].lower() for entry in report["recent_weakness"] + report["risks"])
    assert any("launches ten satellites" in entry["point"].lower() for entry in report["recovery_signals"] + report["catalysts"])
    assert report["evidence"]["news"]["positive_signal_count"] >= 1
    assert report["evidence"]["news"]["negative_signal_count"] >= 1
    assert report["market_overlay"]["supportive_effects"] >= 1
    assert report["coverage"]["quality"] == "thin"
    assert report["market_overlay"]["effective_supportive_effects"] >= 1


def test_generic_war_headline_does_not_count_as_energy_tailwind_without_oil_signal() -> None:
    item = {
        "symbol": "AKVA",
        "company_name": "Akva Group",
        "selection_bucket": "entry_ready",
        "selection_reason": "setup+breakout",
        "entry_ready": True,
        "metrics": {
            "close": 113.5,
            "hh20_prev": 110.0,
            "vol_anom": 2.65,
            "atr14": 3.27,
        },
        "source_rows": [
            {
                "ema20": 105.28,
                "ema50": 100.20,
                "ema200": 90.62,
                "_source_url": "https://stock.sdc-fried.de/data/2026-04-11_universe_5_EU_Results.txt",
                "_table_title": "Universe 5 EU - ENTRY_READY",
                "_source_feed_date": "2026-04-11",
            }
        ],
    }
    news_context = {
        "symbol": "AKVA",
        "articles": [],
        "daily_sentiment": [],
        "market_articles": [
            {
                "datetime_utc": "2026-04-12T00:00:00Z",
                "headline": "Israeli strike kills infant girl in south Lebanon during father's funeral - Reuters",
                "summary": "A humanitarian tragedy in south Lebanon.",
                "url": "https://example.com/lebanon",
                "source": "Example Macro",
                "provider": "fixture",
                "sentiment": 0.0,
            },
            {
                "datetime_utc": "2026-04-12T01:00:00Z",
                "headline": "Two Supertankers U-Turn in Hormuz as US-Iran Talks Break Down",
                "summary": "Oil supply risk rises as tanker traffic is disrupted.",
                "url": "https://example.com/hormuz",
                "source": "Example Macro",
                "provider": "fixture",
                "sentiment": 0.0,
            },
            {
                "datetime_utc": "2026-04-12T02:00:00Z",
                "headline": "It feels awkward: I gave my friend's daughter cash for her wedding. Silence. Do I say something?",
                "summary": "A personal finance advice column unrelated to geopolitics.",
                "url": "https://example.com/awkward",
                "source": "Example Macro",
                "provider": "fixture",
                "sentiment": 0.0,
            },
        ],
        "company_profile": {"sector": "Energy", "industry": "Oil & Gas", "provider": "fixture"},
    }

    report = generate_python_report(item, news_context, analysis_date="2026-04-12")
    market_articles = report["evidence"]["market"]["classified_articles"]

    lebanon_article = next(article for article in market_articles if "south Lebanon" in article["headline"])
    hormuz_article = next(article for article in market_articles if "Hormuz" in article["headline"])
    awkward_article = next(article for article in market_articles if "awkward" in article["headline"].lower())

    assert not lebanon_article["matched_effects"]
    assert hormuz_article["matched_effects"]
    assert not awkward_article["matched_effects"]
    assert report["coverage"]["quality"] == "none"
    assert report["market_overlay"]["supportive_effects"] == 1
    assert report["market_overlay"]["effective_supportive_effects"] == 0
    assert report["breakout_stance"]["confidence"] == "low"
