#!/bin/sh
# Daily DBGI portal backup, run once a day by cron (deploy/cron.d/dbgi-portal).
# Saves the database (pg_dump, compressed) and the uploaded files (media) into backups/YYYY-MM-DD/
# in the portal folder, and deletes backup folders older than KEEP_DAYS (default 14).
# Each day's backup is also uploaded, encrypted, off the server when the rclone remote below is set up.
#
# Restore the database (portal stopped except db):
#   gunzip -c backups/DATE/database.sql.gz | docker compose -f COMPOSE_FILE exec -T db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
# Restore the files:
#   docker compose -f COMPOSE_FILE exec -T web tar xzf - -C /app < backups/DATE/media.tar.gz
set -u
cd "$(dirname "$0")/.." || exit 1
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.test-server.yml}"
KEEP_DAYS="${KEEP_DAYS:-14}"
OFFSITE_REMOTE="${OFFSITE_REMOTE:-dbgi-backup}"
OFFSITE_KEEP_DAYS="${OFFSITE_KEEP_DAYS:-30}"
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
  # Off-server copy: if an rclone remote named $OFFSITE_REMOTE exists (an encrypted "crypt" remote over
  # Google Drive on the DBGI server), upload today's backup there and delete copies older than OFFSITE_KEEP_DAYS.
  if [ "$status" -eq 0 ] && command -v rclone >/dev/null 2>&1 \
    && rclone listremotes | grep -qx "$OFFSITE_REMOTE:"; then
    rclone copy "backups/$DAY" "$OFFSITE_REMOTE:$DAY" && echo "off-server copy: done" || {
      echo "off-server copy: FAILED"
      status=1
    }
    rclone delete --min-age "${OFFSITE_KEEP_DAYS}d" "$OFFSITE_REMOTE:" && rclone rmdirs --leave-root "$OFFSITE_REMOTE:"
  else
    echo "off-server copy: skipped"
  fi
  ls -l "backups/$DAY"
  echo "exit code $status"
} >> logs/backup.log 2>&1
