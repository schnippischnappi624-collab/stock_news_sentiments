#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

REGION="${1:-}"
TAG="${2:-}"

if [[ -z "$REGION" || -z "$TAG" ]]; then
  echo "usage: $0 <EU|US> <cron-tag>" >&2
  exit 2
fi

REGION="$(printf "%s" "$REGION" | tr '[:lower:]' '[:upper:]')"
case "$REGION" in
  EU|US) ;;
  *)
    echo "usage: $0 <EU|US> <cron-tag>" >&2
    exit 2
    ;;
esac

/bin/bash "$ROOT/stock_news/scripts/run_daily_and_push.sh" "$REGION"

CURRENT="$(crontab -l 2>/dev/null || true)"
FILTERED="$(printf "%s\n" "$CURRENT" | grep -v "$TAG" || true)"
printf "%s\n" "$FILTERED" | awk 'NF' | crontab -
