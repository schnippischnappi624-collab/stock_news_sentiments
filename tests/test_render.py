from stock_news.render import render_analysis_markdown, render_dashboard, render_regional_project_readme


def test_render_analysis_markdown_includes_sections() -> None:
    item = {
        "symbol": "SPIR",
        "company_name": "Spire Global Inc",
        "currency": "USD",
        "selection_bucket": "entry_ready",
        "selection_reason": "setup+breakout",
        "metrics": {
            "invest_score": 5.2,
            "state_score": 2.1,
            "vol_anom": 3.3,
            "close": 21.56,
            "atr14": 1.77,
            "entry_limit": 20.50,
            "stop_init": 17.83,
            "tp_2r": 25.84,
            "tp_3r": 28.51,
        },
    }
    report = {
        "symbol": "SPIR",
        "company_name": "Spire Global Inc",
        "analysis_date": "2026-04-12",
        "analysis_mode": "python",
        "summary": "Momentum improved after a sharp drawdown and a $14.00 follow-on reference.",
        "recent_weakness": [{"point": "The stock sold off after a weak guidance reset.", "confidence": "medium"}],
        "recovery_signals": [{"point": "Volume expanded on the latest breakout attempt.", "confidence": "high"}],
        "catalysts": [{"point": "Next earnings call is within three weeks.", "confidence": "medium"}],
        "risks": [{"point": "A failed retest of the breakout level would weaken the setup.", "confidence": "high"}],
        "news_support": {"stance": "supportive", "explanation": "Recent headlines are improving."},
        "breakout_stance": {"label": "constructive", "score_0_to_100": 72, "confidence": "medium", "thesis": "The setup is improving."},
        "investing_technical": {
            "provider": "investing.com",
            "timeframe": "1h",
            "timeframe_label": "Stündlich",
            "technical_page_url": "https://de.investing.com/equities/spire-global-inc-technical",
            "overview": "Strong Buy",
            "technical_indicators": "Buy",
            "moving_averages": "Strong Buy",
        },
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
        "sources": [{"title": "$14.00 Per Share - Example", "url": "https://example.com", "published_at": "2026-04-11"}],
    }

    markdown = render_analysis_markdown(
        report,
        item,
        eur_rates_context={"rate_date": "2026-04-11", "rates": {"EUR": 1.0, "USD": 2.0}},
        news_context={
            "company_profile": {"query_symbol": "SPIR"},
            "quote_links": {
                "investing_symbol": "SPIR",
                "investing_url": "https://de.investing.com/equities/spire-global-inc",
            },
        },
    )

    assert "# SPIR - Spire Global Inc" in markdown
    assert "## Investment View" in markdown
    assert "&#36;14.00" in markdown
    assert "## What Matters" in markdown
    assert "## Risks / Invalidation" in markdown
    assert "constructive" in markdown
    assert "## Why This Score" in markdown
    assert "## Market Overlay" in markdown
    assert "Stock-news coverage quality" in markdown
    assert "Macro overlay weight used in scoring" in markdown
    assert "|  |  |" in markdown
    assert r"| **Breakout stance** | $\color{#2da44e}{\texttt{constructive}}$ |" in markdown
    assert r"| **Score** | $\color{#9a6700}{\texttt{72}}$ |" in markdown
    assert r"| **Confidence** | $\color{#9a6700}{\texttt{medium}}$ |" in markdown
    assert r"| **Investing overview (1h)** | $\color{#1a7f37}{\texttt{Strong Buy}}$ |" in markdown
    assert r"| **Investing indicators (1h)** | $\color{#2da44e}{\texttt{Buy}}$ |" in markdown
    assert r"| **Investing moving averages (1h)** | $\color{#1a7f37}{\texttt{Strong Buy}}$ |" in markdown
    assert "| **Current price** | `21.56 USD (10.78 EUR)` |" in markdown
    assert "| **Entry limit** | `20.50 USD (10.25 EUR)` |" in markdown
    assert r"| **Distance to entry limit** | $\color{#cf222e}{\texttt{1.06 USD (0.53 EUR) / +5.17\%}}$ |" in markdown
    assert "| **Initial stop** | `17.83 USD (8.91 EUR)` |" in markdown
    assert "- Quote: [Investing.com (SPIR)](<https://de.investing.com/equities/spire-global-inc>)" in markdown
    assert markdown.index("| **Bucket** |") < markdown.index("| **Investing overview (1h)** |")
    assert markdown.index("| **Investing moving averages (1h)** |") < markdown.index("| **Current price** |")
    assert "[&#36;14.00 Per Share - Example](<https://example.com>) - 2026-04-11" in markdown


def test_render_dashboard_uses_sectioned_score_first_ranking() -> None:
    manifest = {"run_id": "2026-04-17_us_deadbeef", "region": "US", "feed_dates": ["2026-04-17"]}
    shortlist = {
        "symbols": [
            {
                "symbol": "LATE",
                "company_name": "Late Runner",
                "selection_bucket": "entry_ready",
                "display_rank": 1,
                "exchange_code": "NASDAQ",
                "country": "United States",
                "metrics": {"close": 134.95, "entry_limit": 100.0},
            },
            {
                "symbol": "NEARB",
                "company_name": "Near B",
                "selection_bucket": "entry_ready",
                "display_rank": 2,
                "exchange_code": "NASDAQ",
                "country": "United States",
                "metrics": {"close": 101.0, "entry_limit": 100.0},
            },
            {
                "symbol": "CAND",
                "company_name": "Candidate Name",
                "selection_bucket": "candidate",
                "display_rank": 3,
                "exchange_code": "NYSE",
                "country": "United States",
                "metrics": {},
            },
            {
                "symbol": "NEARA",
                "company_name": "Near A",
                "selection_bucket": "entry_ready",
                "display_rank": 4,
                "exchange_code": "NASDAQ",
                "country": "United States",
                "metrics": {"close": 104.0, "entry_limit": 100.0},
            },
        ]
    }
    analysis_rows = [
        {"symbol": "LATE", "breakout_stance": {"label": "constructive_watch", "score_0_to_100": 80, "confidence": "medium"}},
        {"symbol": "NEARB", "breakout_stance": {"label": "constructive_watch", "score_0_to_100": 70, "confidence": "medium"}},
        {"symbol": "CAND", "breakout_stance": {"label": "mixed_watch", "score_0_to_100": 90, "confidence": "high"}},
        {"symbol": "NEARA", "breakout_stance": {"label": "constructive_bullish", "score_0_to_100": 85, "confidence": "high"}},
    ]

    markdown = render_dashboard(manifest, shortlist, analysis_rows, report_prefix="analysis/markdown")

    assert "### Entry Ready Near Trigger" in markdown
    assert "### Entry Ready But Already Spiked" in markdown
    assert "### Candidates" in markdown
    assert "near-trigger cutoff = `5%`" in markdown
    assert "| Rank | Symbol | Company | Distance to entry | Bucket | Score | Confidence | Breakout stance | News stance | Coverage |" in markdown
    assert "Top catalyst / headwind" not in markdown
    assert "New this run" not in markdown
    assert "Report |" not in markdown
    assert "Listing |" not in markdown
    assert "Issuer group |" not in markdown
    assert "Δ score" not in markdown
    assert "Δ confidence" not in markdown
    assert "Prior rank" not in markdown
    assert "Stance change" not in markdown
    assert markdown.index("[NEARA](<analysis/markdown/NEARA.md>)") < markdown.index("[NEARB](<analysis/markdown/NEARB.md>)")
    assert markdown.index("### Entry Ready But Already Spiked") < markdown.index("[LATE](<analysis/markdown/LATE.md>)")
    assert markdown.index("### Candidates") < markdown.index("[CAND](<analysis/markdown/CAND.md>)")


def test_render_regional_project_readme_has_monitoring_sections_and_deltas() -> None:
    sections = [
        {
            "region": "EU",
            "report_prefix": "eu/analysis/markdown",
            "manifest": {"run_id": "2026-04-17_eu_deadbeef", "feed_dates": ["2026-04-17"]},
            "shortlist": {
                "symbols": [
                    {
                        "symbol": "RAW",
                        "company_name": "Raiffeisen Bank International AG",
                        "selection_bucket": "entry_ready",
                        "display_rank": 9,
                        "exchange_code": "WBAG",
                        "country": "Austria",
                        "metrics": {"close": 10.0, "entry_limit": 9.7},
                    },
                    {
                        "symbol": "RBI",
                        "company_name": "Raiffeisen Bank International AG",
                        "selection_bucket": "entry_ready",
                        "display_rank": 1,
                        "exchange_code": "WBAG",
                        "country": "Austria",
                        "metrics": {"close": 8.0, "entry_limit": 7.0},
                    },
                ],
                "filtered_out_symbols": [
                    {
                        "symbol": "CHEAP",
                        "company_name": "Cheap Nordic",
                        "region": "EU",
                        "currency": "SEK",
                        "current_price": 8.0,
                        "current_price_eur": 0.8,
                    }
                ],
            },
            "analysis_rows": [
                {
                    "symbol": "RAW",
                    "breakout_stance": {"label": "constructive_bullish", "score_0_to_100": 85, "confidence": "high"},
                    "news_support": {"stance": "supportive"},
                    "coverage": {"quality": "strong", "stock_articles": 9},
                    "catalysts": [{"point": "Contract award"}],
                    "risks": [{"point": "Liquidity squeeze"}],
                },
                {
                    "symbol": "RBI",
                    "breakout_stance": {"label": "constructive_watch", "score_0_to_100": 72, "confidence": "medium"},
                    "news_support": {"stance": "mixed"},
                    "coverage": {"quality": "good", "stock_articles": 3},
                    "catalysts": [{"point": "Asset sale"}],
                    "risks": [{"point": "Overhead supply"}],
                },
            ],
            "profiles_by_symbol": {
                "RAW": {
                    "long_name": "Raiffeisen Bank International AG",
                    "exchange": "WBAG",
                    "country": "Austria",
                },
                "RBI": {
                    "short_name": "Raiffeisen Bank International AG",
                    "exchange": "WBAG",
                    "country": "Austria",
                },
            },
            "prior_section": {
                "region": "EU",
                "manifest": {"run_id": "2026-04-16_eu_prev", "feed_dates": ["2026-04-16"]},
                "shortlist": {
                    "symbols": [
                        {
                            "symbol": "RAW",
                            "company_name": "Raiffeisen Bank International AG",
                            "selection_bucket": "entry_ready",
                            "exchange_code": "WBAG",
                            "country": "Austria",
                            "metrics": {"close": 9.8, "entry_limit": 9.7},
                        },
                        {
                            "symbol": "DROP",
                            "company_name": "Dropped Nordic",
                            "selection_bucket": "candidate",
                            "exchange_code": "XETR",
                            "country": "Germany",
                            "metrics": {},
                        },
                    ]
                },
                "analysis_rows": [
                    {
                        "symbol": "RAW",
                        "breakout_stance": {"label": "mixed_watch", "score_0_to_100": 79, "confidence": "medium"},
                    },
                    {
                        "symbol": "DROP",
                        "breakout_stance": {"label": "fragile_watch", "score_0_to_100": 49, "confidence": "low"},
                    },
                ],
                "profiles_by_symbol": {
                    "RAW": {
                        "long_name": "Raiffeisen Bank International AG",
                        "exchange": "WBAG",
                        "country": "Austria",
                    },
                    "DROP": {
                        "long_name": "Dropped Nordic AG",
                        "exchange": "XETR",
                        "country": "Germany",
                    },
                },
            },
        },
        {
            "region": "US",
            "report_prefix": "us/analysis/markdown",
            "manifest": {"run_id": "2026-04-17_us_cafebabe", "feed_dates": ["2026-04-17"]},
            "shortlist": {
                "symbols": [
                    {
                        "symbol": "SPIR",
                        "company_name": "Spire Global Inc",
                        "selection_bucket": "candidate",
                        "display_rank": 1,
                        "exchange_code": "NYSE",
                        "country": "United States",
                        "metrics": {},
                    }
                ]
            },
            "analysis_rows": [
                {
                    "symbol": "SPIR",
                    "breakout_stance": {"label": "mixed_watch", "score_0_to_100": 52, "confidence": "medium"},
                    "news_support": {"stance": "mixed"},
                    "coverage": {"quality": "thin", "stock_articles": 1},
                    "catalysts": [{"point": "Earnings call"}],
                    "risks": [{"point": "Failed retest"}],
                }
            ],
            "profiles_by_symbol": {
                "SPIR": {
                    "long_name": "Spire Global, Inc.",
                    "exchange": "NYSE",
                    "country": "United States",
                }
            },
        },
    ]

    markdown = render_regional_project_readme(sections, best_candidates_top_n=10)

    assert "## EU Best Candidates by Actionability and Score" in markdown
    assert "## US Best Candidates by Actionability and Score" in markdown
    assert "### Entry Ready Near Trigger" in markdown
    assert "### Entry Ready But Already Spiked" in markdown
    assert "### Candidates" in markdown
    assert "Listing |" not in markdown
    assert "Issuer group |" not in markdown
    assert "Top catalyst / headwind" not in markdown
    assert "New this run" not in markdown
    assert "Report |" not in markdown
    assert "Δ score" not in markdown
    assert "Δ confidence" not in markdown
    assert "Prior rank" not in markdown
    assert "Stance change" not in markdown
    assert "[RAW](<latest/eu/analysis/markdown/RAW.md>)" in markdown
    assert "[RBI](<latest/eu/analysis/markdown/RBI.md>)" in markdown
    assert "[SPIR](<latest/us/analysis/markdown/SPIR.md>)" in markdown
    assert r"$\color{#1a7f37}{\textsf{strong(9)}}$" in markdown
    assert r"$\color{#9a6700}{\textsf{thin(1)}}$" in markdown
    assert "Dropped Since Prior Run" not in markdown
    assert "Distance to entry" in markdown
    assert r"$\color{#1a7f37}{\textsf{entry ready}}$" in markdown
    assert r"$\color{#9a6700}{\textsf{mixed watch}}$" in markdown
    assert "## Temporarily Omitted Penny Stocks" in markdown
    assert "`EU` `CHEAP` - Cheap Nordic - `8.00 SEK` (0.80 EUR)" in markdown
