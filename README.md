# stock_news_sentiments

Auto-generated daily breakout dashboard for the latest committed regional runs.

- Regions available: `EU, US`
- Feed dates: `2026-04-11`
- Symbols analyzed: `28`

Quick links:
- [Regional best candidates](latest/best_candidates.md)
- [Regional dashboard](latest/dashboard.md)
- [Operational notes](docs/OPERATIONS.md)

## EU Best Scoring Candidates

- Run ID: `2026-04-11_2cc47b69`
- Feed dates: `2026-04-11`
- Symbols analyzed: `22`

| Rank | Symbol | Company | Bucket | Score | Confidence | Breakout stance |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | [NEWCAP](latest/analysis/markdown/NEWCAP.md) | Newcap Holding A/S | entry_ready | 80 | medium | constructive_bullish |
| 2 | [0QMG](latest/analysis/markdown/0QMG.md) | Swiss Life Holding AG | entry_ready | 77 | medium | constructive_bullish |
| 3 | [ALNT](latest/analysis/markdown/ALNT.md) | Alantra Partners S.A. | entry_ready | 77 | medium | constructive_bullish |
| 4 | [ARVOSK](latest/analysis/markdown/ARVOSK.md) | Pohjanmaan Arvo Sijoitusosuuskunta | entry_ready | 77 | medium | constructive_bullish |
| 5 | [ALNSE](latest/analysis/markdown/ALNSE.md) | NSE SA | entry_ready | 76 | medium | constructive_bullish |
| 6 | [ALRIB](latest/analysis/markdown/ALRIB.md) | Riber S.A | entry_ready | 76 | medium | constructive_bullish |
| 7 | [LOYAL](latest/analysis/markdown/LOYAL.md) | Loyal Solutions AS | entry_ready | 76 | medium | constructive_bullish |
| 8 | [0AA9](latest/analysis/markdown/0AA9.md) | Storskogen Group AB Series B | entry_ready | 75 | medium | constructive_bullish |
| 9 | [BOHO-PREF](latest/analysis/markdown/BOHO-PREF.md) | Boho Group AB | entry_ready | 75 | medium | constructive_bullish |
| 10 | [QH9](latest/analysis/markdown/QH9.md) | ADTRAN Holdings Inc. | entry_ready | 75 | medium | constructive_bullish |
| 11 | [KREATE](latest/analysis/markdown/KREATE.md) | Kreate Group Oyj | entry_ready | 72 | high | constructive_watch |
| 12 | [LOUP](latest/analysis/markdown/LOUP.md) | Societe LDC SA | entry_ready | 72 | high | constructive_watch |
| 13 | [LOIHDE](latest/analysis/markdown/LOIHDE.md) | Loihde Oyj | entry_ready | 70 | medium | constructive_watch |
| 14 | [0DNW](latest/analysis/markdown/0DNW.md) | Austevoll Seafood ASA | entry_ready | 69 | high | constructive_watch |
| 15 | [AKVA](latest/analysis/markdown/AKVA.md) | Akva Group | entry_ready | 69 | high | constructive_watch |

## US Best Scoring Candidates

- Run ID: `2026-04-11_2cc47b69`
- Feed dates: `2026-04-11`
- Symbols analyzed: `6`

| Rank | Symbol | Company | Bucket | Score | Confidence | Breakout stance |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | [SPIR](latest/analysis/markdown/SPIR.md) | Spire Global Inc | entry_ready | 72 | high | constructive_watch |
| 2 | [TIMB](latest/analysis/markdown/TIMB.md) | TIM Participacoes SA | candidate | 58 | medium | mixed_watch |
| 3 | [MRVL](latest/analysis/markdown/MRVL.md) | Marvell Technology Group Ltd | candidate | 53 | medium | mixed_watch |
| 4 | [AXIA](latest/analysis/markdown/AXIA.md) | AXIA Energia | candidate | 53 | medium | mixed_watch |
| 5 | [FRT](latest/analysis/markdown/FRT.md) | Federal Realty Investment Trust | candidate | 52 | high | mixed_watch |
| 6 | [LION](latest/analysis/markdown/LION.md) | Lionsgate Studios Holding Corp. (to be renamed Lionsgate Stu dios Corp.) | candidate | 52 | medium | mixed_watch |

## Column Guide

- `Breakout stance`: the repo's normalized final investing view for the setup after blending feed/technical evidence with any matched news and macro overlay.
  Worst to best: `avoid` -> `fragile_watch` -> `mixed_watch` -> `constructive_watch` -> `constructive_bullish`
- `Confidence`: how much usable evidence supports the current stance.
  Worst to best: `low` -> `medium` -> `high`
- `Bucket`: where the symbol sits in the shortlist built from the source website feeds.
  Worst to best: `candidate` -> `entry_ready`
