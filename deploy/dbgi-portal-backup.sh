#!/bin/sh
# Daily DBGI portal backup, run once a day by cron (deploy/cron.d/dbgi-portal).
# Saves the database (pg_dump, compressed) and the uploaded files (media) into backups/YYYY-MM-DD/
# in the portal folder, and deletes backup folders older than KEEP_DAYS (default 14).
# These backups stay on this server; copy them somewhere else as well, because a lost server loses them too.
#
# Restore the database (portal stopped except db):
#   gunzip -c backups/DATE/database.sql.gz | docker compose -f COMPOSE_FILE exec -T db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
# Restore the files:
#   docker compose -f COMPOSE_FILE exec -T web tar xzf - -C /app < backups/DATE/media.tar.gz
set -u
cd "$(dirname "$0")/.." || exit 1
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.test-server.yml}"
KEEP_DAYS="${KEEP_DAYS:-14}"
DAY="$(date '+%Y-%m-%d')"
mkdir -p logs "backups/$DAY"
chmod 700 backups
{
  echo "$(date '+%Y-%m-%d %H:%M:%S %Z') backup to backups/$DAY"
  status=0
  /usr/bin/docker compose -f "$COMPOSE_FILE" exec -T db \
    sh -c 'pg_dump --clean --if-exists -U "$POSTGRES_USER" -d "$POSTGRES_DB"' \
    | gzip > "backups/$DAY/database.sql.gz.part" \
    && mv "backups/$DAY/database.sql.gz.part" "backups/$DAY/database.sql.gz" || status=1
  /usr/bin/docker compose -f "$COMPOSE_FILE" exec -T web tar czf - -C /app media \
    > "backups/$DAY/media.tar.gz.part" \
    && mv "backups/$DAY/media.tar.gz.part" "backups/$DAY/media.tar.gz" || status=1
  if [ "$status" -eq 0 ]; then
    find backups -mindepth 1 -maxdepth 1 -type d -mtime +"$KEEP_DAYS" -exec rm -rf {} +
  fi
  ls -l "backups/$DAY"
  echo "exit code $status"
} >> logs/backup.log 2>&1
