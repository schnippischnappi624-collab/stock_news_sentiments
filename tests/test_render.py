from stock_news.render import render_analysis_markdown


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
        "evidence": {
            "news": {"article_count": 3, "positive_signal_count": 2, "negative_signal_count": 1, "catalyst_signal_count": 1},
            "market": {"article_count": 12},
        },
        "market_overlay": {"sector": "Technology", "industry": "Software", "exposures": ["software"], "supportive_effects": 1, "adverse_effects": 0},
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
