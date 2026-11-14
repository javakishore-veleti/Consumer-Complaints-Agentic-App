#!/usr/bin/env bash
# Start every local service: each CICD/Local/<service>/docker-compose.yaml is one service.
# Usage: CICD/Local/docker-all-up.sh [service ...]     (no arguments = all services)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

services() {
  if [ "$#" -gt 0 ]; then printf '%s\n' "$@"; return; fi
  for f in "$ROOT"/*/docker-compose.y*ml; do [ -e "$f" ] && basename "$(dirname "$f")"; done
}

for svc in $(services "$@"); do
  dir="$ROOT/$svc"
  [ -d "$dir" ] || { echo "no such service: $svc" >&2; exit 1; }
  if [ -f "$dir/.env.example" ] && [ ! -f "$dir/.env" ]; then
    echo "[$svc] missing $dir/.env - copy .env.example to .env and fill it in" >&2
    exit 1
  fi
  echo "==> starting $svc"
  (cd "$dir" && docker compose up -d)
done

echo
"$ROOT/docker-all-status.sh"
