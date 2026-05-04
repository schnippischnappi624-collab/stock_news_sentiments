# stock_news_sentiments

Auto-generated breakout monitoring dashboard for the latest committed regional runs.

- Regions available: `EU, US`
- Feed dates: `2026-05-01, 2026-05-03, 2026-05-04`
- Symbols analyzed: `7`

Quick links:
- [Regional best candidates](latest/best_candidates.md)
- [Regional dashboard](latest/dashboard.md)
- [Operational notes](docs/OPERATIONS.md)

## EU Best Candidates by Actionability and Score

- Run ID: `2026-05-04_eu_0e6c5be9`
- Prior regional run: `2026-05-03_eu_8d67b97a`
- Feed dates: `2026-05-01, 2026-05-04`
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

- Run ID: `2026-05-03_us_eaeef75a`
- Prior regional run: `2026-05-02_us_e9c9a9c4`
- Feed dates: `2026-05-03`
- Symbols analyzed: `7`
- Sort mode: sections `Entry Ready Near Trigger -> Entry Ready But Already Spiked -> Candidates`; in-section rank = `score desc -> confidence desc -> abs(distance to entry) asc -> symbol asc`; near-trigger cutoff = `5%`
- Rows shown: `7` of `7`

### Entry Ready Near Trigger

| Rank | Symbol | Company | Distance to entry | Bucket | Score | Confidence | Breakout stance | News stance | Coverage |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | [PDFS](<latest/us/analysis/markdown/PDFS.md>) | PDF Solutions Inc | $\color{#9a6700}{\textsf{+2.63\%}}$ | $\color{#1a7f37}{\textsf{entry ready}}$ | $\color{#1a7f37}{\textsf{82}}$ | $\color{#1a7f37}{\textsf{high}}$ | $\color{#1a7f37}{\textsf{constructive bullish}}$ | $\color{#1a7f37}{\textsf{supportive}}$ | $\color{#1a7f37}{\textsf{strong(15)}}$ |
| 2 | [COHU](<latest/us/analysis/markdown/COHU.md>) | Cohu Inc | $\color{#1a7f37}{\textsf{+0.47\%}}$ | $\color{#1a7f37}{\textsf{entry ready}}$ | $\color{#1a7f37}{\textsf{81}}$ | $\color{#1a7f37}{\textsf{high}}$ | $\color{#1a7f37}{\textsf{constructive bullish}}$ | $\color{#1a7f37}{\textsf{supportive}}$ | $\color{#1a7f37}{\textsf{strong(15)}}$ |

### Entry Ready But Already Spiked

| Rank | Symbol | Company | Distance to entry | Bucket | Score | Confidence | Breakout stance | News stance | Coverage |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | [MRAM](<latest/us/analysis/markdown/MRAM.md>) | Everspin Technologies Inc | $\color{#cf222e}{\textsf{+6.43\%}}$ | $\color{#1a7f37}{\textsf{entry ready}}$ | $\color{#1a7f37}{\textsf{86}}$ | $\color{#1a7f37}{\textsf{high}}$ | $\color{#1a7f37}{\textsf{constructive bullish}}$ | $\color{#1a7f37}{\textsf{supportive}}$ | $\color{#1a7f37}{\textsf{strong(15)}}$ |
| 2 | [MXL](<latest/us/analysis/markdown/MXL.md>) | MaxLinear Inc | $\color{#cf222e}{\textsf{+61.41\%}}$ | $\color{#1a7f37}{\textsf{entry ready}}$ | $\color{#1a7f37}{\textsf{86}}$ | $\color{#1a7f37}{\textsf{high}}$ | $\color{#1a7f37}{\textsf{constructive bullish}}$ | $\color{#1a7f37}{\textsf{supportive}}$ | $\color{#1a7f37}{\textsf{strong(15)}}$ |
| 3 | [SXT](<latest/us/analysis/markdown/SXT.md>) | Sensient Technologies Corporation | $\color{#cf222e}{\textsf{+20.74\%}}$ | $\color{#1a7f37}{\textsf{entry ready}}$ | $\color{#1a7f37}{\textsf{84}}$ | $\color{#1a7f37}{\textsf{high}}$ | $\color{#1a7f37}{\textsf{constructive bullish}}$ | $\color{#1a7f37}{\textsf{supportive}}$ | $\color{#1a7f37}{\textsf{strong(15)}}$ |
| 4 | [UVE](<latest/us/analysis/markdown/UVE.md>) | Universal Insurance Holdings Inc | $\color{#cf222e}{\textsf{+8.28\%}}$ | $\color{#1a7f37}{\textsf{entry ready}}$ | $\color{#1a7f37}{\textsf{77}}$ | $\color{#1a7f37}{\textsf{high}}$ | $\color{#1a7f37}{\textsf{constructive bullish}}$ | $\color{#cf222e}{\textsf{conflicting}}$ | $\color{#1a7f37}{\textsf{strong(15)}}$ |
| 5 | [POET](<latest/us/analysis/markdown/POET.md>) | POET Technologies Inc | $\color{#cf222e}{\textsf{+16.60\%}}$ | $\color{#1a7f37}{\textsf{entry ready}}$ | $\color{#9a6700}{\textsf{69}}$ | $\color{#1a7f37}{\textsf{high}}$ | $\color{#2da44e}{\textsf{constructive watch}}$ | $\color{#cf222e}{\textsf{conflicting}}$ | $\color{#1a7f37}{\textsf{strong(15)}}$ |

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
