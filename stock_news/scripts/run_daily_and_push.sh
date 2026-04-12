#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

LOCKFILE="$ROOT/.daily_run.lock"
exec 9>"$LOCKFILE"
flock -n 9 || exit 0

poetry run stock-news daily-run

PATHS=(artifacts latest news README.md)

if [[ -z "$(git status --porcelain -- "${PATHS[@]}")" ]]; then
  exit 0
fi

git add -A -- "${PATHS[@]}"
git diff --cached --quiet && exit 0

TS="$(TZ=Europe/Vienna date +"%Y-%m-%dT%H:%M:%S%:z")"
git commit -m "data: daily breakout analysis ${TS}"
git push
