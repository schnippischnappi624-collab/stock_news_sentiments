#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

REGION="${1:-}"
ARGS=()
LOCK_SUFFIX=""
PUSH_REMOTE="${STOCK_NEWS_PUSH_REMOTE:-origin}"
PUSH_BRANCH="${STOCK_NEWS_PUSH_BRANCH:-main}"

if [[ -n "$REGION" ]]; then
  REGION="$(printf "%s" "$REGION" | tr '[:lower:]' '[:upper:]')"
  case "$REGION" in
    EU|US) ;;
    *)
      echo "usage: $0 [EU|US]" >&2
      exit 2
      ;;
  esac
  ARGS=(--region "$REGION")
  LOCK_SUFFIX="_${REGION,,}"
fi

LOCKFILE="$ROOT/.daily_run${LOCK_SUFFIX}.lock"
exec 9>"$LOCKFILE"
flock -n 9 || exit 0

poetry run stock-news daily-run "${ARGS[@]}"

PATHS=(artifacts latest news README.md)

if [[ -z "$(git status --porcelain -- "${PATHS[@]}")" ]]; then
  exit 0
fi

git add -A -- "${PATHS[@]}"
git diff --cached --quiet && exit 0

TS="$(TZ=Europe/Vienna date +"%Y-%m-%dT%H:%M:%S%:z")"
if [[ -n "$REGION" ]]; then
  git commit -m "data: ${REGION} daily breakout analysis ${TS}"
else
  git commit -m "data: daily breakout analysis ${TS}"
fi
git push "$PUSH_REMOTE" "HEAD:${PUSH_BRANCH}"
