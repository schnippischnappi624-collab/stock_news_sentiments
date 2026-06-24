# stock_news_sentiments

Auto-generated breakout monitoring dashboard for the latest committed regional runs.

- Regions available: `EU, US`
- Feed dates: `2026-06-23, 2026-06-24`
- Symbols analyzed: `2`

Quick links:
- [Regional best candidates](latest/best_candidates.md)
- [Regional dashboard](latest/dashboard.md)
- [Operational notes](docs/OPERATIONS.md)

## EU Best Candidates by Actionability and Score

- Run ID: `2026-06-24_eu_54adaf65`
- Prior regional run: `2026-06-23_eu_11590e10`
- Feed dates: `2026-06-24`
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

- Run ID: `2026-06-23_us_6ea84d87`
- Prior regional run: `2026-06-22_us_0025eab3`
- Feed dates: `2026-06-23`
- Symbols analyzed: `2`
- Sort mode: sections `Entry Ready Near Trigger -> Entry Ready But Already Spiked -> Candidates`; in-section rank = `score desc -> confidence desc -> abs(distance to entry) asc -> symbol asc`; near-trigger cutoff = `5%`
- Rows shown: `2` of `2`

### Entry Ready Near Trigger

| Rank | Symbol | Company | Distance to entry | Bucket | Score | Confidence | Breakout stance | News stance | Coverage |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | [GALDY](<latest/us/analysis/markdown/GALDY.md>) | GALDERMA GROUP AG | $\color{#1a7f37}{\textsf{+0.05\%}}$ | $\color{#1a7f37}{\textsf{entry ready}}$ | $\color{#1a7f37}{\textsf{81}}$ | $\color{#1a7f37}{\textsf{high}}$ | $\color{#1a7f37}{\textsf{constructive bullish}}$ | $\color{#1a7f37}{\textsf{supportive}}$ | $\color{#2da44e}{\textsf{good(3)}}$ |

### Entry Ready But Already Spiked

| Rank | Symbol | Company | Distance to entry | Bucket | Score | Confidence | Breakout stance | News stance | Coverage |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | [ROKU](<latest/us/analysis/markdown/ROKU.md>) | Roku Inc | $\color{#cf222e}{\textsf{+7.64\%}}$ | $\color{#1a7f37}{\textsf{entry ready}}$ | $\color{#1a7f37}{\textsf{84}}$ | $\color{#1a7f37}{\textsf{high}}$ | $\color{#1a7f37}{\textsf{constructive bullish}}$ | $\color{#1a7f37}{\textsf{supportive}}$ | $\color{#1a7f37}{\textsf{strong(15)}}$ |

### Candidates

No names from this section landed inside the current top-`15` cutoff.



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
