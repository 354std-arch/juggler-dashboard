#!/bin/bash
# juggler-dashboard daily pipeline (runs locally to bypass Cloudflare IP block)
set -e

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_FILE="$REPO_DIR/run_daily.log"

cd "$REPO_DIR"

echo "=== $(date '+%Y-%m-%d %H:%M:%S JST') START ===" >> "$LOG_FILE"

abort_if_conflicts() {
  local unmerged_files
  local conflict_pattern
  conflict_pattern='^([<]{7}|[=]{7}|[>]{7})'
  unmerged_files="$(git diff --name-only --diff-filter=U)"
  if [ -n "$unmerged_files" ]; then
    echo "Unmerged git paths detected; aborting daily run." >> "$LOG_FILE"
    echo "$unmerged_files" >> "$LOG_FILE"
    exit 1
  fi

  if grep -n -E "$conflict_pattern" app.js index.html style.css compute.py morning_compute.py candidate_compute.py run_daily.sh >> "$LOG_FILE" 2>&1; then
    echo "Conflict markers detected in source files; aborting daily run." >> "$LOG_FILE"
    exit 1
  fi
}

abort_if_conflicts

# Pull latest changes first
if ! git pull --rebase >> "$LOG_FILE" 2>&1; then
  echo "git pull --rebase failed; aborting daily run." >> "$LOG_FILE"
  abort_if_conflicts
  exit 1
fi

abort_if_conflicts

# Run pipeline
python3 scrape_juggler.py >> "$LOG_FILE" 2>&1
python3 compute.py >> "$LOG_FILE" 2>&1
python3 morning_compute.py >> "$LOG_FILE" 2>&1
python3 candidate_compute.py >> "$LOG_FILE" 2>&1

# Commit and push
git config user.email "action@github.com"
git config user.name "local-cron"
git add data.json morning_data.json candidate_data.json raw_data.csv store_list.json
[ -f store_model_summary.csv ] && git add store_model_summary.csv
[ -f store_freshness.json ] && git add store_freshness.json
[ -f seat_data.json ] && git add seat_data.json
[ -f hall_layouts.json ] && git add hall_layouts.json
git add seat_data_*.json 2>/dev/null || true

git diff --cached --quiet || git commit -m "auto: update data.json $(date +'%Y-%m-%d')"
git push >> "$LOG_FILE" 2>&1

echo "=== $(date '+%Y-%m-%d %H:%M:%S JST') DONE ===" >> "$LOG_FILE"
