#!/usr/bin/env bash
# Stop every local service. Data volumes are kept; pass --wipe to delete them too (Airflow's database included).
# Usage: CICD/Local/docker-all-down.sh [--wipe] [service ...]
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

flags=()
if [ "${1:-}" = "--wipe" ]; then
  flags=(-v)
  shift
fi

services() {
  if [ "$#" -gt 0 ]; then printf '%s\n' "$@"; return; fi
  for f in "$ROOT"/*/docker-compose.y*ml; do [ -e "$f" ] && basename "$(dirname "$f")"; done
}

for svc in $(services "$@"); do
  dir="$ROOT/$svc"
  [ -d "$dir" ] || { echo "no such service: $svc" >&2; exit 1; }
  echo "==> stopping $svc ${flags[*]:-}"
  # Airflow's compose file needs FERNET_KEY at parse time even to stop; an empty value is fine for `down`.
  (cd "$dir" && FERNET_KEY="${FERNET_KEY:-}" docker compose down ${flags[@]+"${flags[@]}"})
done
