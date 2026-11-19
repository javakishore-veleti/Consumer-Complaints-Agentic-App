#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SQL_FILE="${ROOT}/sql/create_refined_tables.sql"
CONTAINER="${CCA_ICEBERG_SPARK_CONTAINER:-cca-spark-iceberg}"

[ -f "$SQL_FILE" ] || { echo "missing $SQL_FILE" >&2; exit 1; }
docker inspect -f '{{.State.Running}}' "$CONTAINER" 2>/dev/null | grep -qx true || {
  echo "container $CONTAINER not running" >&2
  exit 1
}
docker cp "$SQL_FILE" "${CONTAINER}:/tmp/create_refined_tables.sql"
docker exec "$CONTAINER" spark-sql -f /tmp/create_refined_tables.sql
docker exec "$CONTAINER" spark-sql -e "SHOW TABLES IN demo.refined;"
