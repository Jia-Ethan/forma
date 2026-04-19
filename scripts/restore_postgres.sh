#!/usr/bin/env sh
set -eu

if [ "${1:-}" = "" ]; then
  printf '%s\n' "Usage: scripts/restore_postgres.sh backups/scnu-thesis-YYYYmmdd-HHMMSS.dump" >&2
  exit 2
fi

docker compose -f docker-compose.production.yml exec -T postgres pg_restore \
  -U "${POSTGRES_USER:-scnu}" \
  -d "${POSTGRES_DB:-scnu_thesis}" \
  --clean \
  --if-exists \
  < "$1"
