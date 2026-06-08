# stock_news_sentiments

Auto-generated breakout monitoring dashboard for the latest committed regional runs.

- Regions available: `EU, US`
- Feed dates: `2026-06-07, 2026-06-08`
- Symbols analyzed: `5`

Quick links:
- [Regional best candidates](latest/best_candidates.md)
- [Regional dashboard](latest/dashboard.md)
- [Operational notes](docs/OPERATIONS.md)

## EU Best Candidates by Actionability and Score

- Run ID: `2026-06-08_eu_8ca50e75`
- Prior regional run: `2026-06-07_eu_8c1e88b1`
- Feed dates: `2026-06-08`
- Symbols analyzed: `0`
- Sort mode: sections `Entry Ready Near Trigger -> Entry Ready But Already Spiked -> Candidates`; in-section rank = `score desc -> confidence desc -> abs(distance to entry) asc -> symbol asc`; near-trigger cutoff = `5%`
- Rows shown: `0` of `0`

### Entry Ready Near Trigger

No names from this section landed inside the current top-`15` cutoff.

### Entry Ready But Already Spiked

No names from this section landed inside the current top-`15` cutoff.

### Candidates

No names from this section landed inside the current top-`15` cutoff.


## US Best Candidates by Actionability and Score

- Run ID: `2026-06-07_us_e6aad026`
- Prior regional run: `2026-06-06_us_c4d97bd0`
- Feed dates: `2026-06-07`
- Symbols analyzed: `5`
- Sort mode: sections `Entry Ready Near Trigger -> Entry Ready But Already Spiked -> Candidates`; in-section rank = `score desc -> confidence desc -> abs(distance to entry) asc -> symbol asc`; near-trigger cutoff = `5%`
- Rows shown: `5` of `5`

### Entry Ready Near Trigger

No names from this section landed inside the current top-`15` cutoff.

### Entry Ready But Already Spiked

No names from this section landed inside the current top-`15` cutoff.

### Candidates

| Rank | Symbol | Company | Distance to entry | Bucket | Score | Confidence | Breakout stance | News stance | Coverage |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | [ARGX](<latest/us/analysis/markdown/ARGX.md>) | argenx NV ADR | n/a | $\color{#bc4c00}{\textsf{candidate}}$ | $\color{#9a6700}{\textsf{66}}$ | $\color{#1a7f37}{\textsf{high}}$ | $\color{#2da44e}{\textsf{constructive watch}}$ | $\color{#1a7f37}{\textsf{supportive}}$ | $\color{#1a7f37}{\textsf{strong(6)}}$ |
| 2 | [GIII](<latest/us/analysis/markdown/GIII.md>) | G-III Apparel Group Ltd | n/a | $\color{#bc4c00}{\textsf{candidate}}$ | $\color{#9a6700}{\textsf{64}}$ | $\color{#1a7f37}{\textsf{high}}$ | $\color{#2da44e}{\textsf{constructive watch}}$ | $\color{#1a7f37}{\textsf{supportive}}$ | $\color{#1a7f37}{\textsf{strong(15)}}$ |
| 3 | [AMG](<latest/us/analysis/markdown/AMG.md>) | Affiliated Managers Group Inc | n/a | $\color{#bc4c00}{\textsf{candidate}}$ | $\color{#bc4c00}{\textsf{57}}$ | $\color{#1a7f37}{\textsf{high}}$ | $\color{#9a6700}{\textsf{mixed watch}}$ | $\color{#1a7f37}{\textsf{supportive}}$ | $\color{#1a7f37}{\textsf{strong(15)}}$ |
| 4 | [PSMT](<latest/us/analysis/markdown/PSMT.md>) | PriceSmart Inc | n/a | $\color{#bc4c00}{\textsf{candidate}}$ | $\color{#cf222e}{\textsf{39}}$ | $\color{#1a7f37}{\textsf{high}}$ | $\color{#bc4c00}{\textsf{fragile watch}}$ | $\color{#9a6700}{\textsf{mixed}}$ | $\color{#1a7f37}{\textsf{strong(15)}}$ |
| 5 | [HBNC](<latest/us/analysis/markdown/HBNC.md>) | Horizon Bancorp | n/a | $\color{#bc4c00}{\textsf{candidate}}$ | $\color{#cf222e}{\textsf{37}}$ | $\color{#1a7f37}{\textsf{high}}$ | $\color{#bc4c00}{\textsf{fragile watch}}$ | $\color{#9a6700}{\textsf{mixed}}$ | $\color{#1a7f37}{\textsf{strong(5)}}$ |



## Column Guide

- `Rank`: rank resets inside each section and uses `score desc -> confidence desc -> abs(distance to entry) asc -> symbol asc`.
- `Breakout stance`: normalized final investing view after blending feed, technical, stock-news, and market-overlay evidence.
  Worst to best: `avoid` -> `fragile watch` -> `mixed watch` -> `constructive watch` -> `constructive bullish`
- `Confidence`: evidence strength behind the current stance.
  Worst to best: `low` -> `medium` -> `high`
- `Bucket`: source-feed setup status.
  Worst to best: `candidate` -> `entry ready`
- `News stance`: whether recent company and matched market news support, conflict with, or mix around the setup.
- `Coverage`: company-specific news quality in the local cache, with stock-article count in brackets such as `strong(15)`.
  Worst to best: `none` -> `thin` -> `good` -> `strong`

## Temporarily Omitted Penny Stocks

The repo currently hides symbols with a current price below `1.00 EUR` as a temporary workaround until the upstream source filter is fixed.

No symbols were filtered out by the temporary penny-stock rule in the latest runs.
