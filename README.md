# stock_news_sentiments

Auto-generated daily breakout dashboard for the latest committed regional runs.

- Regions available: `EU, US`
- Feed dates: `2026-04-11`
- Symbols analyzed: `24`

Quick links:
- [Regional best candidates](latest/best_candidates.md)
- [Regional dashboard](latest/dashboard.md)
- [Operational notes](docs/OPERATIONS.md)

## EU Best Scoring Candidates

- Run ID: `2026-04-11_2cc47b69`
- Feed dates: `2026-04-11`
- Symbols analyzed: `18`

| Rank | Symbol | Company | Bucket | Score | Confidence | Breakout stance |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | [ALRIB](latest/analysis/markdown/ALRIB.md) | Riber S.A | entry_ready | 87 | high | constructive_bullish |
| 2 | [QH9](latest/analysis/markdown/QH9.md) | ADTRAN Holdings Inc. | entry_ready | 83 | high | constructive_bullish |
| 3 | [ALNSE](latest/analysis/markdown/ALNSE.md) | NSE SA | entry_ready | 82 | high | constructive_bullish |
| 4 | [ALNT](latest/analysis/markdown/ALNT.md) | Alantra Partners S.A. | entry_ready | 79 | medium | constructive_bullish |
| 5 | [0QMG](latest/analysis/markdown/0QMG.md) | Swiss Life Holding AG | entry_ready | 77 | medium | constructive_bullish |
| 6 | [AKVA](latest/analysis/markdown/AKVA.md) | Akva Group | entry_ready | 77 | high | constructive_bullish |
| 7 | [ARVOSK](latest/analysis/markdown/ARVOSK.md) | Pohjanmaan Arvo Sijoitusosuuskunta | entry_ready | 77 | medium | constructive_bullish |
| 8 | [0AA9](latest/analysis/markdown/0AA9.md) | Storskogen Group AB Series B | entry_ready | 75 | low | constructive_bullish |
| 9 | [BOHO-PREF](latest/analysis/markdown/BOHO-PREF.md) | Boho Group AB | entry_ready | 75 | high | constructive_bullish |
| 10 | [RIO1](latest/analysis/markdown/RIO1.md) | Rio Tinto Group | entry_ready | 75 | high | constructive_bullish |
| 11 | [LOUP](latest/analysis/markdown/LOUP.md) | Societe LDC SA | entry_ready | 74 | low | constructive_watch |
| 12 | [KREATE](latest/analysis/markdown/KREATE.md) | Kreate Group Oyj | entry_ready | 72 | high | constructive_watch |
| 13 | [LOIHDE](latest/analysis/markdown/LOIHDE.md) | Loihde Oyj | entry_ready | 70 | medium | constructive_watch |
| 14 | [BIJ](latest/analysis/markdown/BIJ.md) | Bijou Brigitte modische Accessoires Aktiengesellschaft | entry_ready | 69 | medium | constructive_watch |
| 15 | [WMA](latest/analysis/markdown/WMA.md) | WindowMaster International AS | entry_ready | 66 | medium | constructive_watch |

## US Best Scoring Candidates

- Run ID: `2026-04-11_2cc47b69`
- Feed dates: `2026-04-11`
- Symbols analyzed: `6`

| Rank | Symbol | Company | Bucket | Score | Confidence | Breakout stance |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | [SPIR](latest/analysis/markdown/SPIR.md) | Spire Global Inc | entry_ready | 66 | high | constructive_watch |
| 2 | [FRT](latest/analysis/markdown/FRT.md) | Federal Realty Investment Trust | candidate | 63 | high | constructive_watch |
| 3 | [MRVL](latest/analysis/markdown/MRVL.md) | Marvell Technology Group Ltd | candidate | 61 | high | constructive_watch |
| 4 | [AXIA](latest/analysis/markdown/AXIA.md) | AXIA Energia | candidate | 57 | high | mixed_watch |
| 5 | [LION](latest/analysis/markdown/LION.md) | Lionsgate Studios Holding Corp. (to be renamed Lionsgate Stu dios Corp.) | candidate | 52 | low | mixed_watch |
| 6 | [TIMB](latest/analysis/markdown/TIMB.md) | TIM Participacoes SA | candidate | 50 | high | mixed_watch |

## Column Guide

- `Breakout stance`: the repo's normalized final investing view for the setup after blending feed/technical evidence with any matched news and macro overlay.
  Worst to best: `avoid` -> `fragile_watch` -> `mixed_watch` -> `constructive_watch` -> `constructive_bullish`
- `Confidence`: how much usable evidence supports the current stance.
  Worst to best: `low` -> `medium` -> `high`
- `Bucket`: where the symbol sits in the shortlist built from the source website feeds.
  Worst to best: `candidate` -> `entry_ready`

## Temporarily Omitted Penny Stocks

The repo currently hides symbols with a current price below `1.00 EUR` as a temporary workaround until the upstream source filter is fixed.

- `EU` `NEWCAP` - Newcap Holding A/S - `0.14 DKK` (0.02 EUR)
- `EU` `0DNW` - Austevoll Seafood ASA - `1.06 NOK` (0.09 EUR)
- `EU` `LOYAL` - Loyal Solutions AS - `5.36 SEK` (0.49 EUR)
- `EU` `BALYO` - Balyo SA - `0.60 EUR` (0.60 EUR)
