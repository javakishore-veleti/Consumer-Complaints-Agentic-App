#!/usr/bin/env bash
# Show the state of local Docker services.
# Usage:
#   CICD/Local/docker-all-status.sh                         # every service
#   CICD/Local/docker-all-status.sh --profile sqlite|postgres|mongodb
#   CICD/Local/docker-all-status.sh [service ...]
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=docker-profiles.sh
source "$ROOT/docker-profiles.sh"

cca_parse_profile_args "$@" || exit 1

if [ -n "${CCA_PROFILE:-}" ]; then
  expected="$(cca_profile_services "$CCA_PROFILE" | paste -sd' ' -)"
  echo "profile=$CCA_PROFILE"
  echo "expected containers (compose projects): $expected"
  echo "(API + Admin UI are host npm processes — not Docker.)"
  echo
fi

while IFS= read -r svc; do
  [ -n "$svc" ] || continue
  dir="$ROOT/$svc"
  [ -d "$dir" ] || { echo "no such service: $svc" >&2; exit 1; }
  echo "==> $svc"
  if ! (cd "$dir" && docker compose ps -a); then
    echo "[$svc] docker compose ps failed (is Docker running?)"
  fi
  echo
done < <(cca_resolved_services)

echo "Airflow UI: http://localhost:${AIRFLOW_PORT:-8080}   (user: airflow / password: airflow)"
