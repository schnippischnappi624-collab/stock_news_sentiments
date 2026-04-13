from stock_news.render import render_analysis_markdown, render_regional_project_readme


def test_render_analysis_markdown_includes_sections() -> None:
    item = {
        "symbol": "SPIR",
        "company_name": "Spire Global Inc",
        "selection_bucket": "entry_ready",
        "selection_reason": "setup+breakout",
        "metrics": {"invest_score": 5.2, "state_score": 2.1, "vol_anom": 3.3, "close": 21.56, "atr14": 1.77},
    }
    report = {
        "symbol": "SPIR",
        "company_name": "Spire Global Inc",
        "analysis_date": "2026-04-12",
        "analysis_mode": "python",
        "summary": "Momentum improved after a sharp drawdown.",
        "recent_weakness": [{"point": "The stock sold off after a weak guidance reset.", "confidence": "medium"}],
        "recovery_signals": [{"point": "Volume expanded on the latest breakout attempt.", "confidence": "high"}],
        "catalysts": [{"point": "Next earnings call is within three weeks.", "confidence": "medium"}],
        "risks": [{"point": "A failed retest of the breakout level would weaken the setup.", "confidence": "high"}],
        "news_support": {"stance": "supportive", "explanation": "Recent headlines are improving."},
        "breakout_stance": {"label": "constructive", "score_0_to_100": 72, "confidence": "medium", "thesis": "The setup is improving."},
        "scorecard": {"components": [{"label": "Breakout above prior high", "points": 8}]},
        "coverage": {"quality": "good", "stock_articles": 3, "market_articles": 12, "market_overlay_weight": 0.85},
        "evidence": {
            "news": {
                "article_count": 3,
                "coverage_quality": "good",
                "positive_signal_count": 2,
                "negative_signal_count": 1,
                "catalyst_signal_count": 1,
            },
            "market": {"article_count": 12},
        },
        "market_overlay": {
            "sector": "Technology",
            "industry": "Software",
            "exposures": ["software"],
            "supportive_effects": 1,
            "adverse_effects": 0,
            "effective_supportive_effects": 1,
            "effective_adverse_effects": 0,
            "weight_scale": 0.85,
        },
        "sources": [{"title": "Example", "url": "https://example.com", "published_at": "2026-04-11"}],
    }

    markdown = render_analysis_markdown(report, item)

    assert "# SPIR - Spire Global Inc" in markdown
    assert "## Investment View" in markdown
    assert "## What Matters" in markdown
    assert "## Risks / Invalidation" in markdown
    assert "constructive" in markdown
    assert "## Why This Score" in markdown
    assert "## Market Overlay" in markdown
    assert "Stock-news coverage quality" in markdown
    assert "Macro overlay weight used in scoring" in markdown


def test_render_regional_project_readme_has_separate_eu_and_us_tables() -> None:
    sections = [
        {
            "region": "EU",
            "report_prefix": "eu/analysis/markdown",
            "manifest": {"run_id": "2026-04-13_eu_deadbeef", "feed_dates": ["2026-04-13"]},
            "shortlist": {
                "symbols": [
                    {
                        "symbol": "AKVA",
                        "company_name": "Akva Group",
                        "selection_bucket": "entry_ready",
                        "display_rank": 1,
                    }
                ]
            },
            "analysis_rows": [
                {"symbol": "AKVA", "breakout_stance": {"label": "constructive_bullish", "score_0_to_100": 81, "confidence": "high"}}
            ],
        },
        {
            "region": "US",
            "report_prefix": "us/analysis/markdown",
            "manifest": {"run_id": "2026-04-13_us_cafebabe", "feed_dates": ["2026-04-13"]},
            "shortlist": {
                "symbols": [
                    {
                        "symbol": "SPIR",
                        "company_name": "Spire Global Inc",
                        "selection_bucket": "candidate",
                        "display_rank": 1,
                    }
                ]
            },
            "analysis_rows": [
                {"symbol": "SPIR", "breakout_stance": {"label": "mixed_watch", "score_0_to_100": 52, "confidence": "medium"}}
            ],
        },
    ]

    markdown = render_regional_project_readme(sections, best_candidates_top_n=10)

    assert "## EU Best Scoring Candidates" in markdown
    assert "## US Best Scoring Candidates" in markdown
    assert "[AKVA](latest/eu/analysis/markdown/AKVA.md)" in markdown
    assert "[SPIR](latest/us/analysis/markdown/SPIR.md)" in markdown
