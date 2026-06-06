# stock_news_sentiments

Auto-generated breakout monitoring dashboard for the latest committed regional runs.

- Regions available: `EU, US`
- Feed dates: `2026-06-05, 2026-06-06`
- Symbols analyzed: `8`

Quick links:
- [Regional best candidates](latest/best_candidates.md)
- [Regional dashboard](latest/dashboard.md)
- [Operational notes](docs/OPERATIONS.md)

## EU Best Candidates by Actionability and Score

- Run ID: `2026-06-06_eu_4785b88e`
- Prior regional run: `2026-06-05_eu_605c6471`
- Feed dates: `2026-06-06`
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

- Run ID: `2026-06-05_us_d694bb46`
- Prior regional run: `2026-06-04_us_4fd36561`
- Feed dates: `2026-06-05`
- Symbols analyzed: `8`
- Sort mode: sections `Entry Ready Near Trigger -> Entry Ready But Already Spiked -> Candidates`; in-section rank = `score desc -> confidence desc -> abs(distance to entry) asc -> symbol asc`; near-trigger cutoff = `5%`
- Rows shown: `8` of `8`

### Entry Ready Near Trigger

No names from this section landed inside the current top-`15` cutoff.

### Entry Ready But Already Spiked

| Rank | Symbol | Company | Distance to entry | Bucket | Score | Confidence | Breakout stance | News stance | Coverage |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | [TOELY](<latest/us/analysis/markdown/TOELY.md>) | Tokyo Electron Ltd PK | $\color{#cf222e}{\textsf{+5.03\%}}$ | $\color{#1a7f37}{\textsf{entry ready}}$ | $\color{#1a7f37}{\textsf{78}}$ | $\color{#cf222e}{\textsf{low}}$ | $\color{#1a7f37}{\textsf{constructive bullish}}$ | $\color{#9a6700}{\textsf{mixed}}$ | $\color{#cf222e}{\textsf{none(0)}}$ |

### Candidates

| Rank | Symbol | Company | Distance to entry | Bucket | Score | Confidence | Breakout stance | News stance | Coverage |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | [ESTA](<latest/us/analysis/markdown/ESTA.md>) | Establishment Labs Holdings Inc | n/a | $\color{#bc4c00}{\textsf{candidate}}$ | $\color{#9a6700}{\textsf{61}}$ | $\color{#1a7f37}{\textsf{high}}$ | $\color{#2da44e}{\textsf{constructive watch}}$ | $\color{#1a7f37}{\textsf{supportive}}$ | $\color{#1a7f37}{\textsf{strong(15)}}$ |
| 2 | [AIN](<latest/us/analysis/markdown/AIN.md>) | Albany International Corporation | n/a | $\color{#bc4c00}{\textsf{candidate}}$ | $\color{#bc4c00}{\textsf{59}}$ | $\color{#1a7f37}{\textsf{high}}$ | $\color{#9a6700}{\textsf{mixed watch}}$ | $\color{#1a7f37}{\textsf{supportive}}$ | $\color{#1a7f37}{\textsf{strong(15)}}$ |
| 3 | [M](<latest/us/analysis/markdown/M.md>) | Macy’s Inc | n/a | $\color{#bc4c00}{\textsf{candidate}}$ | $\color{#bc4c00}{\textsf{54}}$ | $\color{#1a7f37}{\textsf{high}}$ | $\color{#9a6700}{\textsf{mixed watch}}$ | $\color{#9a6700}{\textsf{mixed}}$ | $\color{#1a7f37}{\textsf{strong(15)}}$ |
| 4 | [CDNA](<latest/us/analysis/markdown/CDNA.md>) | CareDx Inc | n/a | $\color{#bc4c00}{\textsf{candidate}}$ | $\color{#bc4c00}{\textsf{47}}$ | $\color{#1a7f37}{\textsf{high}}$ | $\color{#9a6700}{\textsf{mixed watch}}$ | $\color{#1a7f37}{\textsf{supportive}}$ | $\color{#1a7f37}{\textsf{strong(13)}}$ |
| 5 | [AUPH](<latest/us/analysis/markdown/AUPH.md>) | Aurinia Pharmaceuticals Inc | n/a | $\color{#bc4c00}{\textsf{candidate}}$ | $\color{#bc4c00}{\textsf{46}}$ | $\color{#1a7f37}{\textsf{high}}$ | $\color{#9a6700}{\textsf{mixed watch}}$ | $\color{#cf222e}{\textsf{conflicting}}$ | $\color{#1a7f37}{\textsf{strong(15)}}$ |
| 6 | [IX](<latest/us/analysis/markdown/IX.md>) | Orix Corp Ads | n/a | $\color{#bc4c00}{\textsf{candidate}}$ | $\color{#bc4c00}{\textsf{45}}$ | $\color{#9a6700}{\textsf{medium}}$ | $\color{#9a6700}{\textsf{mixed watch}}$ | $\color{#9a6700}{\textsf{mixed}}$ | $\color{#9a6700}{\textsf{thin(1)}}$ |
| 7 | [HBNC](<latest/us/analysis/markdown/HBNC.md>) | Horizon Bancorp | n/a | $\color{#bc4c00}{\textsf{candidate}}$ | $\color{#cf222e}{\textsf{43}}$ | $\color{#1a7f37}{\textsf{high}}$ | $\color{#bc4c00}{\textsf{fragile watch}}$ | $\color{#9a6700}{\textsf{mixed}}$ | $\color{#1a7f37}{\textsf{strong(5)}}$ |



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
