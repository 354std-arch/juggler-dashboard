#!/bin/bash
# juggler-dashboard daily pipeline (runs locally to bypass Cloudflare IP block)
set -e

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_FILE="$REPO_DIR/run_daily.log"

cd "$REPO_DIR"

echo "=== $(date '+%Y-%m-%d %H:%M:%S JST') START ===" >> "$LOG_FILE"

# Pull latest changes first
git pull --rebase >> "$LOG_FILE" 2>&1 || echo "git pull failed, continuing" >> "$LOG_FILE"

# Run pipeline
python3 scrape_juggler.py >> "$LOG_FILE" 2>&1
python3 feedback.py >> "$LOG_FILE" 2>&1
python3 compute.py >> "$LOG_FILE" 2>&1
python3 morning_compute.py >> "$LOG_FILE" 2>&1
python3 candidate_compute.py >> "$LOG_FILE" 2>&1

# Commit and push
git config user.email "action@github.com"
git config user.name "local-cron"
git add data.json morning_data.json candidate_data.json raw_data.csv store_list.json feedback_data.json
[ -f store_model_summary.csv ] && git add store_model_summary.csv
[ -f store_freshness.json ] && git add store_freshness.json
[ -f seat_data.json ] && git add seat_data.json
git add seat_data_*.json 2>/dev/null || true

git diff --cached --quiet || git commit -m "auto: update data.json $(date +'%Y-%m-%d')"
git push >> "$LOG_FILE" 2>&1

echo "=== $(date '+%Y-%m-%d %H:%M:%S JST') DONE ===" >> "$LOG_FILE"
