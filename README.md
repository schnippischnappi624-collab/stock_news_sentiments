# stock_news_sentiments

Auto-generated breakout monitoring dashboard for the latest committed regional runs.

- Regions available: `EU, US`
- Feed dates: `2026-06-04, 2026-06-05`
- Symbols analyzed: `4`

Quick links:
- [Regional best candidates](latest/best_candidates.md)
- [Regional dashboard](latest/dashboard.md)
- [Operational notes](docs/OPERATIONS.md)

## EU Best Candidates by Actionability and Score

- Run ID: `2026-06-05_eu_605c6471`
- Prior regional run: `2026-06-04_eu_32d22780`
- Feed dates: `2026-06-05`
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

- Run ID: `2026-06-04_us_4fd36561`
- Prior regional run: `2026-06-03_us_a43b5132`
- Feed dates: `2026-06-04`
- Symbols analyzed: `4`
- Sort mode: sections `Entry Ready Near Trigger -> Entry Ready But Already Spiked -> Candidates`; in-section rank = `score desc -> confidence desc -> abs(distance to entry) asc -> symbol asc`; near-trigger cutoff = `5%`
- Rows shown: `4` of `4`

### Entry Ready Near Trigger

No names from this section landed inside the current top-`15` cutoff.

### Entry Ready But Already Spiked

No names from this section landed inside the current top-`15` cutoff.

### Candidates

| Rank | Symbol | Company | Distance to entry | Bucket | Score | Confidence | Breakout stance | News stance | Coverage |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | [PLXS](<latest/us/analysis/markdown/PLXS.md>) | Plexus Corp | n/a | $\color{#bc4c00}{\textsf{candidate}}$ | $\color{#9a6700}{\textsf{61}}$ | $\color{#1a7f37}{\textsf{high}}$ | $\color{#2da44e}{\textsf{constructive watch}}$ | $\color{#1a7f37}{\textsf{supportive}}$ | $\color{#1a7f37}{\textsf{strong(15)}}$ |
| 2 | [PK](<latest/us/analysis/markdown/PK.md>) | Park Hotels & Resorts Inc | n/a | $\color{#bc4c00}{\textsf{candidate}}$ | $\color{#bc4c00}{\textsf{52}}$ | $\color{#1a7f37}{\textsf{high}}$ | $\color{#9a6700}{\textsf{mixed watch}}$ | $\color{#cf222e}{\textsf{conflicting}}$ | $\color{#1a7f37}{\textsf{strong(14)}}$ |
| 3 | [PVH](<latest/us/analysis/markdown/PVH.md>) | PVH Corp | n/a | $\color{#bc4c00}{\textsf{candidate}}$ | $\color{#cf222e}{\textsf{38}}$ | $\color{#1a7f37}{\textsf{high}}$ | $\color{#bc4c00}{\textsf{fragile watch}}$ | $\color{#cf222e}{\textsf{conflicting}}$ | $\color{#1a7f37}{\textsf{strong(15)}}$ |
| 4 | [KALV](<latest/us/analysis/markdown/KALV.md>) | Kalvista Pharmaceuticals Inc | n/a | $\color{#bc4c00}{\textsf{candidate}}$ | $\color{#cf222e}{\textsf{33}}$ | $\color{#1a7f37}{\textsf{high}}$ | $\color{#bc4c00}{\textsf{fragile watch}}$ | $\color{#9a6700}{\textsf{mixed}}$ | $\color{#1a7f37}{\textsf{strong(12)}}$ |



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
