#!/bin/sh
# Daily DBGI portal job, run once a day by cron (deploy/cron.d/dbgi-portal).
# process_deadlines sends the 60-day and on-hold reminders, returns overdue deals to DBGI review,
# and sends price expiry reminders. It records each step, so running it twice changes nothing,
# and a missed day is caught up on the next run.
#
# Runs from the portal folder (the folder above this script). Set COMPOSE_FILE for production,
# for example COMPOSE_FILE=docker-compose.yml. The log is logs/deadlines.log in the portal folder.
set -u
cd "$(dirname "$0")/.." || exit 1
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.test-server.yml}"
mkdir -p logs
{
  echo "$(date '+%Y-%m-%d %H:%M:%S %Z') process_deadlines"
  /usr/bin/docker compose -f "$COMPOSE_FILE" exec -T web python manage.py process_deadlines
  echo "exit code $?"
} >> logs/deadlines.log 2>&1
