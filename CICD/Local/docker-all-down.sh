#!/usr/bin/env bash
# Stop local Docker services and remove their named volumes by default (M01-0073 / #133).
# Usage:
#   CICD/Local/docker-all-down.sh [--keep-volumes] [--wipe]                         # every service
#   CICD/Local/docker-all-down.sh [--keep-volumes] [--wipe] --profile sqlite|postgres|mongodb
#   CICD/Local/docker-all-down.sh [--keep-volumes] [--wipe] [service ...]
# --wipe is accepted as a no-op alias (wipe is already the default).
# --keep-volumes runs plain `docker compose down` (volumes retained).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=docker-profiles.sh
source "$ROOT/docker-profiles.sh"

cca_parse_profile_args "$@" || exit 1

flags=()
if [ "${CCA_WIPE:-1}" = "1" ]; then
  flags=(-v)
fi

if [ -n "${CCA_PROFILE:-}" ]; then
  echo "profile=$CCA_PROFILE  expected: $(cca_profile_services "$CCA_PROFILE" | paste -sd' ' -)"
fi

while IFS= read -r svc; do
  [ -n "$svc" ] || continue
  dir="$ROOT/$svc"
  [ -d "$dir" ] || { echo "no such service: $svc" >&2; exit 1; }
  if [ "${CCA_WIPE:-1}" = "1" ]; then
    echo "==> stopping $svc (removing volumes)"
  else
    echo "==> stopping $svc (keeping volumes)"
  fi
  # Airflow's compose file needs FERNET_KEY at parse time even to stop; an empty value is fine for `down`.
  (cd "$dir" && FERNET_KEY="${FERNET_KEY:-}" docker compose down ${flags[@]+"${flags[@]}"})
done < <(cca_resolved_services)
