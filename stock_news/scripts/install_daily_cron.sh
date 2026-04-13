#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
REGION="${1:-}"

if [[ -n "$REGION" ]]; then
  REGION="$(printf "%s" "$REGION" | tr '[:lower:]' '[:upper:]')"
  case "$REGION" in
    EU) MINUTE=15 ;;
    US) MINUTE=25 ;;
    *)
      echo "usage: $0 [EU|US]" >&2
      exit 2
      ;;
  esac
  JOB='CRON_TZ=Europe/Vienna
'$MINUTE' 11 * * * cd '"$ROOT"' && /bin/bash '"$ROOT"'/stock_news/scripts/run_daily_and_push.sh '"$REGION"
  FILTER_EXPR='stock_news/scripts/run_daily_and_push.sh '"$REGION"
else
  JOB='CRON_TZ=Europe/Vienna
15 11 * * * cd '"$ROOT"' && /bin/bash '"$ROOT"'/stock_news/scripts/run_daily_and_push.sh'
  FILTER_EXPR='stock_news/scripts/run_daily_and_push.sh'
fi

CURRENT="$(crontab -l 2>/dev/null || true)"
FILTERED="$(printf "%s\n" "$CURRENT" | grep -v "$FILTER_EXPR" || true)"

{
  printf "%s\n" "$FILTERED"
  printf "%s\n" "$JOB"
} | awk 'NF' | crontab -

if [[ -n "$REGION" ]]; then
  echo "Installed daily ${REGION} cron job for stock_news_sentiments at 11:${MINUTE} Europe/Vienna."
else
  echo "Installed daily combined cron job for stock_news_sentiments at 11:15 Europe/Vienna."
fi
