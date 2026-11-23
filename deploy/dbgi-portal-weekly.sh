#!/bin/sh
# Weekly DBGI portal job, run every Monday morning by cron (deploy/cron.d/dbgi-portal).
# send_owner_summary emails the owner the same few numbers as his Overview page. It can be
# switched off in Portal settings, under Pricing.
#
# Runs from the portal folder (the folder above this script). Set COMPOSE_FILE for production.
set -u
cd "$(dirname "$0")/.." || exit 1
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.test-server.yml}"
mkdir -p logs
{
  echo "$(date '+%Y-%m-%d %H:%M:%S %Z') send_owner_summary"
  /usr/bin/docker compose -f "$COMPOSE_FILE" exec -T web python manage.py send_owner_summary
  echo "exit code $?"
} >> logs/owner-summary.log 2>&1
