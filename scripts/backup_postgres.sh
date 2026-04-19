#!/usr/bin/env sh
set -eu

stamp="$(date +%Y%m%d-%H%M%S)"
mkdir -p backups
docker compose -f docker-compose.production.yml exec -T postgres pg_dump \
  -U "${POSTGRES_USER:-scnu}" \
  -d "${POSTGRES_DB:-scnu_thesis}" \
  --format=custom \
  > "backups/scnu-thesis-${stamp}.dump"

printf '%s\n' "Wrote backups/scnu-thesis-${stamp}.dump"
