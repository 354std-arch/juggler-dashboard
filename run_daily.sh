#!/bin/bash
# juggler-dashboard daily pipeline (runs locally to bypass Cloudflare IP block)
set -e

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_FILE="$REPO_DIR/run_daily.log"
SMART_SLOT_BACKFILL_DAYS="${SMART_SLOT_BACKFILL_DAYS:-30}"
SMART_SLOT_BACKFILL_TASKS="${SMART_SLOT_BACKFILL_TASKS:-4}"
SMART_SLOT_BACKFILL_INTERVAL_SEC="${SMART_SLOT_BACKFILL_INTERVAL_SEC:-0.5}"
DATA_SIZE_WARN_MB="${DATA_SIZE_WARN_MB:-50}"
case "$SMART_SLOT_BACKFILL_DAYS" in ''|*[!0-9]*) SMART_SLOT_BACKFILL_DAYS=30 ;; esac
case "$SMART_SLOT_BACKFILL_TASKS" in ''|*[!0-9]*) SMART_SLOT_BACKFILL_TASKS=4 ;; esac
case "$DATA_SIZE_WARN_MB" in ''|*[!0-9]*) DATA_SIZE_WARN_MB=50 ;; esac

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

git_pull_latest() {
  local label="$1"
  local attempt
  for attempt in 1 2 3; do
    if git pull --rebase --autostash >> "$LOG_FILE" 2>&1; then
      return 0
    fi
    echo "$label git pull --rebase --autostash failed (attempt $attempt/3)." >> "$LOG_FILE"
    abort_if_conflicts
    sleep $((attempt * 10))
  done
  return 1
}

warn_large_file() {
  local file="$1"
  local size_bytes
  local size_mb
  [ -f "$file" ] || return 0
  size_bytes="$(wc -c < "$file" | tr -d ' ')"
  size_mb=$(( (size_bytes + 1048575) / 1048576 ))
  if [ "$size_mb" -ge "$DATA_SIZE_WARN_MB" ]; then
    echo "warning: $file is ${size_mb}MB; GitHub recommends keeping regular git files below 50MB." >> "$LOG_FILE"
  fi
}

abort_if_conflicts

# Pull latest changes first
if ! git_pull_latest "startup"; then
  echo "startup git pull failed after retries; continuing data refresh with current worktree." >> "$LOG_FILE"
  abort_if_conflicts
fi

abort_if_conflicts

# Run pipeline
python3 scrape_juggler.py >> "$LOG_FILE" 2>&1
if [ "$SMART_SLOT_BACKFILL_TASKS" -gt 0 ]; then
  BACKFILL_START="$(date -v-"$SMART_SLOT_BACKFILL_DAYS"d '+%Y-%m-%d')"
  BACKFILL_END="$(date -v-1d '+%Y-%m-%d')"
  echo "smart slot backfill: $BACKFILL_START to $BACKFILL_END / max $SMART_SLOT_BACKFILL_TASKS tasks" >> "$LOG_FILE"
  python3 scrape_juggler.py \
    --start-date "$BACKFILL_START" \
    --end-date "$BACKFILL_END" \
    --backfill-smart-slots \
    --backfill-latest-first \
    --max-backfill-tasks "$SMART_SLOT_BACKFILL_TASKS" \
    --store-interval-sec "$SMART_SLOT_BACKFILL_INTERVAL_SEC" >> "$LOG_FILE" 2>&1
fi
python3 compute.py >> "$LOG_FILE" 2>&1
python3 morning_compute.py >> "$LOG_FILE" 2>&1
python3 candidate_compute.py >> "$LOG_FILE" 2>&1

warn_large_file raw_data.csv
warn_large_file data.json
warn_large_file seat_data.json

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
if ! git push >> "$LOG_FILE" 2>&1; then
  echo "git push failed; pulling latest and retrying once." >> "$LOG_FILE"
  if git_pull_latest "pre-push"; then
    git push >> "$LOG_FILE" 2>&1
  else
    echo "pre-push pull failed; leaving local data commit for manual push." >> "$LOG_FILE"
    exit 1
  fi
fi

echo "=== $(date '+%Y-%m-%d %H:%M:%S JST') DONE ===" >> "$LOG_FILE"
