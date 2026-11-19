#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONTAINER="${CCA_ICEBERG_SPARK_CONTAINER:-cca-spark-iceberg}"
SQL="$ROOT/sql/create_curated_tables.sql"
docker inspect -f '{{.State.Running}}' "$CONTAINER" 2>/dev/null | grep -qx true || {
  echo "iceberg not running" >&2
  exit 1
}
docker cp "$SQL" "${CONTAINER}:/tmp/create_curated_tables.sql"
docker exec "$CONTAINER" spark-sql -f /tmp/create_curated_tables.sql
