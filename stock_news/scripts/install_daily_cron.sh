#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
JOB='CRON_TZ=Europe/Vienna
15 11 * * * cd '"$ROOT"' && /bin/bash '"$ROOT"'/stock_news/scripts/run_daily_and_push.sh'

CURRENT="$(crontab -l 2>/dev/null || true)"
FILTERED="$(printf "%s\n" "$CURRENT" | grep -v 'stock_news/scripts/run_daily_and_push.sh' || true)"

{
  printf "%s\n" "$FILTERED"
  printf "%s\n" "$JOB"
} | awk 'NF' | crontab -

echo "Installed daily cron job for stock_news_sentiments at 11:15 Europe/Vienna."
