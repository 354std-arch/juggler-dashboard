#!/bin/bash
# juggler-dashboard daily pipeline (runs locally to bypass Cloudflare IP block)
set -e

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_FILE="$REPO_DIR/run_daily.log"
LOCK_DIR="$REPO_DIR/.run_daily.lock"
STATUS_FILE="$REPO_DIR/run_daily_status.txt"
STATUS_JSON_FILE="$REPO_DIR/automation_status.json"
ACCESS_BLOCK_FILE="$REPO_DIR/.ana_slo_access_block.json"
MODE="${JUGGLER_DAILY_MODE:-run}"
SMART_SLOT_BACKFILL_DAYS="${SMART_SLOT_BACKFILL_DAYS:-30}"
SMART_SLOT_BACKFILL_TASKS="${SMART_SLOT_BACKFILL_TASKS:-4}"
SMART_SLOT_BACKFILL_INTERVAL_SEC="${SMART_SLOT_BACKFILL_INTERVAL_SEC:-0.5}"
DATA_SIZE_WARN_MB="${DATA_SIZE_WARN_MB:-50}"
ANA_SLO_COOLDOWN_HOURS="${ANA_SLO_COOLDOWN_HOURS:-24}"
case "$SMART_SLOT_BACKFILL_DAYS" in ''|*[!0-9]*) SMART_SLOT_BACKFILL_DAYS=30 ;; esac
case "$SMART_SLOT_BACKFILL_TASKS" in ''|*[!0-9]*) SMART_SLOT_BACKFILL_TASKS=4 ;; esac
case "$DATA_SIZE_WARN_MB" in ''|*[!0-9]*) DATA_SIZE_WARN_MB=50 ;; esac
case "$ANA_SLO_COOLDOWN_HOURS" in ''|*[!0-9]*) ANA_SLO_COOLDOWN_HOURS=24 ;; esac

cd "$REPO_DIR"

now_jst() {
  date '+%Y-%m-%d %H:%M:%S JST'
}

log() {
  echo "[$(now_jst)] $*" >> "$LOG_FILE"
}

write_status() {
  local ts
  local msg
  ts="$(now_jst)"
  msg="$*"
  printf '%s\t%s\n' "$ts" "$msg" > "$STATUS_FILE"
  python3 - "$STATUS_JSON_FILE" "$ts" "$msg" "$MODE" "$ANA_SLO_COOLDOWN_HOURS" "$ACCESS_BLOCK_FILE" <<'PY'
import json
import os
import sys

out_path, ts, message, mode, cooldown_hours, block_path = sys.argv[1:7]
lower = message.lower()
if "blocked" in lower:
    category = "blocked"
elif "cooldown" in lower:
    category = "cooldown"
elif "failed" in lower:
    category = "failed"
elif "running" in lower:
    category = "running"
elif lower.startswith("ok"):
    category = "ok"
elif "skipped" in lower:
    category = "skipped"
else:
    category = "unknown"

access_block = None
if os.path.exists(block_path):
    try:
        with open(block_path, encoding="utf-8") as fh:
            access_block = json.load(fh)
    except Exception as exc:
        access_block = {"parse_error": str(exc)}

payload = {
    "updated_at": ts,
    "status": message,
    "category": category,
    "mode": mode,
    "schedule": "毎朝7:31 JST / Mac launchd",
    "cooldown_hours": int(cooldown_hours) if str(cooldown_hours).isdigit() else cooldown_hours,
    "access_block": access_block,
    "source": "run_daily.sh",
}
with open(out_path, "w", encoding="utf-8") as fh:
    json.dump(payload, fh, ensure_ascii=False, indent=2)
    fh.write("\n")
PY
}

configure_git_identity() {
  git config user.email "action@github.com"
  git config user.name "local-cron"
}

publish_status_update() {
  [ "${PUBLISH_DAILY_STATUS:-1}" = "1" ] || return 0
  configure_git_identity
  git add "$STATUS_JSON_FILE" >> "$LOG_FILE" 2>&1 || {
    log "automation status git add failed"
    return 0
  }
  if git diff --cached --quiet -- "$STATUS_JSON_FILE"; then
    return 0
  fi
  if git commit -m "auto: update automation status $(date +'%Y-%m-%d')" -- "$STATUS_JSON_FILE" >> "$LOG_FILE" 2>&1; then
    git push >> "$LOG_FILE" 2>&1 || log "automation status push failed"
  else
    log "automation status commit failed"
  fi
}

cleanup_lock() {
  rmdir "$LOCK_DIR" 2>/dev/null || true
}

fail() {
  local code="$?"
  log "FAILED exit=$code line=${BASH_LINENO[0]} command=${BASH_COMMAND}"
  write_status "FAILED exit=$code"
  publish_status_update || true
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
  publish_status_update
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

access_block_age_sec() {
  [ -f "$ACCESS_BLOCK_FILE" ] || return 1
  local now
  local mtime
  now="$(date '+%s')"
  mtime="$(stat -f '%m' "$ACCESS_BLOCK_FILE" 2>/dev/null || echo 0)"
  [ "$mtime" -gt 0 ] || return 1
  echo $((now - mtime))
}

is_access_cooldown_active() {
  local age
  local cooldown_sec
  age="$(access_block_age_sec)" || return 1
  cooldown_sec=$((ANA_SLO_COOLDOWN_HOURS * 3600))
  [ "$age" -lt "$cooldown_sec" ]
}

log_access_block() {
  if [ -f "$ACCESS_BLOCK_FILE" ]; then
    log "ana-slo access block marker:"
    sed 's/^/  /' "$ACCESS_BLOCK_FILE" >> "$LOG_FILE" 2>/dev/null || true
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

# Cloudflare 403/429 直後に再アクセスすると復旧が遅れるため、一定時間は完全停止する。
if is_access_cooldown_active; then
  log "ana-slo access cooldown active; skipping scrape/compute/push for ${ANA_SLO_COOLDOWN_HOURS}h window"
  log_access_block
  write_status "SKIPPED ana-slo cooldown"
  publish_status_update
  log "=== DONE cooldown ==="
  exit 0
fi

# Run pipeline
SCRAPE_INPUTS_BEFORE="$(fingerprint_scrape_inputs)"
log "scrape_juggler.py start"
python3 scrape_juggler.py --stop-on-consecutive-failures 1 >> "$LOG_FILE" 2>&1
log "scrape_juggler.py done"
if is_access_cooldown_active; then
  log "ana-slo access block detected during scrape; skipping backfill/compute/push"
  log_access_block
  write_status "SKIPPED ana-slo blocked"
  publish_status_update
  log "=== DONE blocked ==="
  exit 0
fi
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
    --stop-on-consecutive-failures 1 \
    --store-interval-sec "$SMART_SLOT_BACKFILL_INTERVAL_SEC" >> "$LOG_FILE" 2>&1
  log "smart slot backfill done"
fi
if is_access_cooldown_active; then
  log "ana-slo access block detected during backfill; skipping compute/push"
  log_access_block
  write_status "SKIPPED ana-slo blocked"
  publish_status_update
  log "=== DONE blocked ==="
  exit 0
fi
SCRAPE_INPUTS_AFTER="$(fingerprint_scrape_inputs)"
if [ "$SCRAPE_INPUTS_BEFORE" = "$SCRAPE_INPUTS_AFTER" ] && [ "${ALLOW_EMPTY_DAILY_COMPUTE:-0}" != "1" ]; then
  log "no scraped data changes detected; skipping compute, commit, and push"
  write_status "OK no scraped changes"
  publish_status_update
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
configure_git_identity
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
publish_status_update
log "=== DONE ==="
