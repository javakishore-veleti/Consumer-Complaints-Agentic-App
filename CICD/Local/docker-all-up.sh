#!/usr/bin/env bash
# Start local Docker services.
# Usage:
#   CICD/Local/docker-all-up.sh                         # every service (unchanged)
#   CICD/Local/docker-all-up.sh --profile sqlite|postgres|mongodb|pgvector
#   CICD/Local/docker-all-up.sh [service ...]           # named services only
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=docker-profiles.sh
source "$ROOT/docker-profiles.sh"

cca_parse_profile_args "$@" || exit 1

if [ -n "${CCA_PROFILE:-}" ]; then
  echo "profile=$CCA_PROFILE  expected: $(cca_profile_services "$CCA_PROFILE" | paste -sd' ' -)"
fi

while IFS= read -r svc; do
  [ -n "$svc" ] || continue
  dir="$ROOT/$svc"
  [ -d "$dir" ] || { echo "no such service: $svc" >&2; exit 1; }
  if [ -f "$dir/.env.example" ] && [ ! -f "$dir/.env" ]; then
    echo "[$svc] missing $dir/.env - copy .env.example to .env and fill it in" >&2
    exit 1
  fi
  echo "==> starting $svc"
  # Airflow Dockerfile bakes pymongo (M17-0009 / #257); --build picks up image changes.
  if [ -f "$dir/Dockerfile" ]; then
    (cd "$dir" && docker compose up -d --build)
  else
    (cd "$dir" && docker compose up -d)
  fi
done < <(cca_resolved_services)

echo
if [ -n "${CCA_PROFILE:-}" ]; then
  "$ROOT/docker-all-status.sh" --profile "$CCA_PROFILE"
else
  "$ROOT/docker-all-status.sh"
fi
