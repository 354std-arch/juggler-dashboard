#!/bin/bash
# juggler-dashboard daily pipeline (runs locally to bypass Cloudflare IP block)
set -e

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_FILE="$REPO_DIR/run_daily.log"
LOCK_DIR="$REPO_DIR/.run_daily.lock"
STATUS_FILE="$REPO_DIR/run_daily_status.txt"
MODE="${JUGGLER_DAILY_MODE:-run}"
SMART_SLOT_BACKFILL_DAYS="${SMART_SLOT_BACKFILL_DAYS:-30}"
SMART_SLOT_BACKFILL_TASKS="${SMART_SLOT_BACKFILL_TASKS:-4}"
SMART_SLOT_BACKFILL_INTERVAL_SEC="${SMART_SLOT_BACKFILL_INTERVAL_SEC:-0.5}"
DATA_SIZE_WARN_MB="${DATA_SIZE_WARN_MB:-50}"
case "$SMART_SLOT_BACKFILL_DAYS" in ''|*[!0-9]*) SMART_SLOT_BACKFILL_DAYS=30 ;; esac
case "$SMART_SLOT_BACKFILL_TASKS" in ''|*[!0-9]*) SMART_SLOT_BACKFILL_TASKS=4 ;; esac
case "$DATA_SIZE_WARN_MB" in ''|*[!0-9]*) DATA_SIZE_WARN_MB=50 ;; esac

cd "$REPO_DIR"

now_jst() {
  date '+%Y-%m-%d %H:%M:%S JST'
}

log() {
  echo "[$(now_jst)] $*" >> "$LOG_FILE"
}

write_status() {
  printf '%s\t%s\n' "$(now_jst)" "$*" > "$STATUS_FILE"
}

cleanup_lock() {
  rmdir "$LOCK_DIR" 2>/dev/null || true
}

fail() {
  local code="$?"
  log "FAILED exit=$code line=${BASH_LINENO[0]} command=${BASH_COMMAND}"
  write_status "FAILED exit=$code"
  cleanup_lock
  exit "$code"
}

trap fail ERR INT TERM

if ! mkdir "$LOCK_DIR" 2>/dev/null; then
  log "SKIP another run is already active: $LOCK_DIR"
  write_status "SKIPPED locked"
  exit 0
fi
trap cleanup_lock EXIT

log "=== START mode=$MODE pid=$$ ==="
write_status "RUNNING mode=$MODE pid=$$"

if [ "$MODE" = "healthcheck" ]; then
  log "healthcheck repo=$REPO_DIR"
  log "healthcheck bash=$BASH_VERSION python=$(command -v python3 || true) git=$(command -v git || true)"
  log "healthcheck git-status=$(git status --short | wc -l | tr -d ' ') changed paths"
  write_status "OK healthcheck"
  log "=== DONE healthcheck ==="
  exit 0
fi

abort_if_conflicts() {
  local unmerged_files
  local conflict_pattern
  conflict_pattern='^([<]{7}|[=]{7}|[>]{7})'
  unmerged_files="$(git diff --name-only --diff-filter=U)"
  if [ -n "$unmerged_files" ]; then
    log "Unmerged git paths detected; aborting daily run."
    echo "$unmerged_files" >> "$LOG_FILE"
    exit 1
  fi

  if grep -n -E "$conflict_pattern" app.js index.html style.css compute.py morning_compute.py candidate_compute.py run_daily.sh >> "$LOG_FILE" 2>&1; then
    log "Conflict markers detected in source files; aborting daily run."
    exit 1
  fi
}

git_pull_latest() {
  local label="$1"
  local attempt
  for attempt in 1 2 3; do
    log "$label git pull --rebase --autostash attempt $attempt/3"
    if git pull --rebase --autostash >> "$LOG_FILE" 2>&1; then
      log "$label git pull succeeded"
      return 0
    fi
    log "$label git pull --rebase --autostash failed (attempt $attempt/3)."
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
    log "warning: $file is ${size_mb}MB; GitHub recommends keeping regular git files below 50MB."
  fi
}

fingerprint_scrape_inputs() {
  cksum raw_data.csv store_freshness.json store_model_summary.csv store_list.json hall_layouts.json 2>/dev/null || true
}

abort_if_conflicts

# Pull latest changes first
if ! git_pull_latest "startup"; then
  log "startup git pull failed after retries; continuing data refresh with current worktree."
  abort_if_conflicts
fi

abort_if_conflicts

# Run pipeline
SCRAPE_INPUTS_BEFORE="$(fingerprint_scrape_inputs)"
log "scrape_juggler.py start"
python3 scrape_juggler.py >> "$LOG_FILE" 2>&1
log "scrape_juggler.py done"
if [ "$SMART_SLOT_BACKFILL_TASKS" -gt 0 ]; then
  BACKFILL_START="$(date -v-"$SMART_SLOT_BACKFILL_DAYS"d '+%Y-%m-%d')"
  BACKFILL_END="$(date -v-1d '+%Y-%m-%d')"
  log "smart slot backfill: $BACKFILL_START to $BACKFILL_END / max $SMART_SLOT_BACKFILL_TASKS tasks"
  python3 scrape_juggler.py \
    --start-date "$BACKFILL_START" \
    --end-date "$BACKFILL_END" \
    --backfill-smart-slots \
    --backfill-latest-first \
    --max-backfill-tasks "$SMART_SLOT_BACKFILL_TASKS" \
    --store-interval-sec "$SMART_SLOT_BACKFILL_INTERVAL_SEC" >> "$LOG_FILE" 2>&1
  log "smart slot backfill done"
fi
SCRAPE_INPUTS_AFTER="$(fingerprint_scrape_inputs)"
if [ "$SCRAPE_INPUTS_BEFORE" = "$SCRAPE_INPUTS_AFTER" ] && [ "${ALLOW_EMPTY_DAILY_COMPUTE:-0}" != "1" ]; then
  log "no scraped data changes detected; skipping compute, commit, and push"
  write_status "OK no scraped changes"
  log "=== DONE no changes ==="
  exit 0
fi
log "compute.py start"
python3 compute.py >> "$LOG_FILE" 2>&1
log "compute.py done"
log "morning_compute.py start"
python3 morning_compute.py >> "$LOG_FILE" 2>&1
log "morning_compute.py done"
log "candidate_compute.py start"
python3 candidate_compute.py >> "$LOG_FILE" 2>&1
log "candidate_compute.py done"

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
  log "git push failed; pulling latest and retrying once."
  if git_pull_latest "pre-push"; then
    git push >> "$LOG_FILE" 2>&1
  else
    log "pre-push pull failed; leaving local data commit for manual push."
    exit 1
  fi
fi

write_status "OK run"
log "=== DONE ==="
