#!/usr/bin/env bash
# Show the state of every local service.
# Usage: CICD/Local/docker-all-status.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

for f in "$ROOT"/*/docker-compose.y*ml; do
  [ -e "$f" ] || continue
  dir="$(dirname "$f")"
  echo "==> $(basename "$dir")"
  (cd "$dir" && docker compose ps -a)
  echo
done

echo "Airflow UI: http://localhost:${AIRFLOW_PORT:-8080}   (user: airflow / password: airflow)"
