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
