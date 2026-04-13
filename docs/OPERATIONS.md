# stock_news_sentiments Operations

Daily breakout-oriented stock analysis pipeline for the feeds published at `https://stock.sdc-fried.de/`.

The workflow is designed to run once per day on this machine. It:

- discovers the newest US and EU `Results.txt` and `Results_CANDIDATES.txt` files
- archives the raw source files and parses the box-drawing tables into normalized artifacts
- builds a shortlist that always includes `ENTRY_READY` names and then adds the top remaining candidates
- updates a local news cache for shortlisted symbols plus market-wide macro headlines and cached company profiles
- computes per-symbol evidence and scoring in Python first, then optionally asks Codex only for compact synthesis text
- renders comparable Markdown reports plus a latest dashboard
- optionally commits and pushes the generated outputs

## Install

```bash
poetry install
```

Optional news source:

- set `FINNHUB_API_KEY`
- or create `secrets/finnhub_key.txt`

## Main Commands

Run the full workflow:

```bash
poetry run stock-news daily-run
```

Run only one region, for separate scheduled pipelines:

```bash
poetry run stock-news daily-run --region EU
poetry run stock-news daily-run --region US
```

Individual steps:

```bash
poetry run stock-news fetch-feeds
poetry run stock-news parse-feeds
poetry run stock-news build-shortlist
poetry run stock-news update-news-cache
poetry run stock-news run-analysis
poetry run stock-news run-codex-analysis
```

Each step also accepts `--region EU` or `--region US` when you want to work against the region-specific active manifest.

Analysis mode options:

- `python`: deterministic evidence, scoring, and report text only
- `hybrid`: Python evidence and scoring plus a small Codex synthesis step for summary text
- `codex-full`: legacy full-report Codex generation

## Outputs

Historical daily runs are written under:

- `artifacts/daily_runs/<run_id>/feeds`
- `artifacts/daily_runs/<run_id>/parsed`
- `artifacts/daily_runs/<run_id>/shortlist`
- `artifacts/daily_runs/<run_id>/analysis`

Stable latest outputs are refreshed under:

- `latest/eu/*`
- `latest/us/*`
- `latest/dashboard.md`
- `latest/best_candidates.md`

The root `latest/dashboard.md`, root `latest/best_candidates.md`, and root `README.md` are combined regional landing pages. They render separate EU and US tables from the newest available regional snapshots.

Reusable news caches live under:

- `news/headlines`
- `news/daily_sentiment`
- `news/market`
- `news/company_profiles`

## Daily Scheduling

The wrapper script for scheduled execution and GitHub push is:

```bash
stock_news/scripts/run_daily_and_push.sh
```

For separate pipelines:

```bash
stock_news/scripts/run_daily_and_push.sh EU
stock_news/scripts/run_daily_and_push.sh US
```

An idempotent cron installer is also included:

```bash
stock_news/scripts/install_daily_cron.sh
```

Or install region-specific jobs:

```bash
stock_news/scripts/install_daily_cron.sh EU
stock_news/scripts/install_daily_cron.sh US
```

Default daily schedule for separate pipelines:

- `EU`: `06:00 Europe/Vienna`
- `US`: `11:15 Europe/Vienna`

Installed cron entries:

```cron
CRON_TZ=Europe/Vienna
0 6 * * * cd /home/mothe-server/python/stock_news_sentiments/stock_news_sentiments && /bin/bash /home/mothe-server/python/stock_news_sentiments/stock_news_sentiments/stock_news/scripts/run_daily_and_push.sh EU
CRON_TZ=Europe/Vienna
15 11 * * * cd /home/mothe-server/python/stock_news_sentiments/stock_news_sentiments && /bin/bash /home/mothe-server/python/stock_news_sentiments/stock_news_sentiments/stock_news/scripts/run_daily_and_push.sh US
```

## Notes

- `daily-run` defaults to `--analysis-mode hybrid`.
- Python-first evidence snapshots are written under `analysis/evidence`.
- Python-first scoring blends stock-specific headlines with a market overlay that maps macro themes like war, rates, shipping stress, and commodity moves onto inferred sector exposures.
- The optional Codex synthesis step uses `codex --search exec` with the checked-in schema at `schemas/breakout_summary.schema.json`.
- Legacy `codex-full` mode still uses `schemas/breakout_analysis.schema.json`.
- If the newest remote feed set has already been processed successfully, `daily-run` exits early without regenerating artifacts.
- The push wrapper commits generated changes in `artifacts`, `latest`, `news`, and the generated root `README.md`, then pushes `HEAD` to `origin/main` by default.
- If only one region has run so far, the combined landing pages show that region and leave the other region empty until its pipeline produces a snapshot.
