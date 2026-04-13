#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
REGION="${1:-}"

build_job() {
  local region="$1"
  local minute="$2"
  local hour="$3"
  printf 'CRON_TZ=Europe/Vienna\n%s %s * * * cd %s && /bin/bash %s/stock_news/scripts/run_daily_and_push.sh %s\n' \
    "$minute" "$hour" "$ROOT" "$ROOT" "$region"
}

CURRENT="$(crontab -l 2>/dev/null || true)"

case "$(printf "%s" "$REGION" | tr '[:lower:]' '[:upper:]')" in
  "")
    FILTERED="$(printf "%s\n" "$CURRENT" \
      | grep -v 'stock_news/scripts/run_daily_and_push.sh EU' \
      | grep -v 'stock_news/scripts/run_daily_and_push.sh US' \
      | grep -v 'stock_news/scripts/run_daily_and_push.sh$' \
      || true)"
    JOBS="$(build_job EU 0 6)
$(build_job US 15 11)"
    MESSAGE="Installed daily EU cron at 06:00 and US cron at 11:15 Europe/Vienna."
    ;;
  EU)
    FILTERED="$(printf "%s\n" "$CURRENT" \
      | grep -v 'stock_news/scripts/run_daily_and_push.sh EU' \
      | grep -v 'stock_news/scripts/run_daily_and_push.sh$' \
      || true)"
    JOBS="$(build_job EU 0 6)"
    MESSAGE="Installed daily EU cron job for stock_news_sentiments at 06:00 Europe/Vienna."
    ;;
  US)
    FILTERED="$(printf "%s\n" "$CURRENT" \
      | grep -v 'stock_news/scripts/run_daily_and_push.sh US' \
      | grep -v 'stock_news/scripts/run_daily_and_push.sh$' \
      || true)"
    JOBS="$(build_job US 15 11)"
    MESSAGE="Installed daily US cron job for stock_news_sentiments at 11:15 Europe/Vienna."
    ;;
  *)
    echo "usage: $0 [EU|US]" >&2
    exit 2
    ;;
esac

{
  printf "%s\n" "$FILTERED"
  printf "%s\n" "$JOBS"
} | awk 'NF' | crontab -

echo "$MESSAGE"
