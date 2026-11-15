#!/usr/bin/env bash
# Stop local Docker services. Data volumes are kept; pass --wipe to delete them too.
# Usage:
#   CICD/Local/docker-all-down.sh [--wipe]                         # every service
#   CICD/Local/docker-all-down.sh [--wipe] --profile sqlite|postgres|mongodb
#   CICD/Local/docker-all-down.sh [--wipe] [service ...]
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=docker-profiles.sh
source "$ROOT/docker-profiles.sh"

cca_parse_profile_args "$@" || exit 1

flags=()
if [ "${CCA_WIPE:-0}" = "1" ]; then
  flags=(-v)
fi

if [ -n "${CCA_PROFILE:-}" ]; then
  echo "profile=$CCA_PROFILE  expected: $(cca_profile_services "$CCA_PROFILE" | paste -sd' ' -)"
fi

while IFS= read -r svc; do
  [ -n "$svc" ] || continue
  dir="$ROOT/$svc"
  [ -d "$dir" ] || { echo "no such service: $svc" >&2; exit 1; }
  echo "==> stopping $svc ${flags[*]:-}"
  # Airflow's compose file needs FERNET_KEY at parse time even to stop; an empty value is fine for `down`.
  (cd "$dir" && FERNET_KEY="${FERNET_KEY:-}" docker compose down ${flags[@]+"${flags[@]}"})
done < <(cca_resolved_services)
