#!/usr/bin/env bash
# Apply Raw Iceberg DDL (M45-0001 / #320) inside cca-spark-iceberg.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SQL_FILE="${ROOT}/sql/create_raw_tables.sql"
CONTAINER="${CCA_ICEBERG_SPARK_CONTAINER:-cca-spark-iceberg}"

if [ ! -f "$SQL_FILE" ]; then
  echo "missing SQL: $SQL_FILE" >&2
  exit 1
fi

if ! docker inspect -f '{{.State.Running}}' "$CONTAINER" 2>/dev/null | grep -qx true; then
  echo "container $CONTAINER is not running. Start with: npm run local:containers:iceberg:start" >&2
  exit 1
fi

echo "==> applying Raw DDL from $SQL_FILE via $CONTAINER"
# Copy SQL into the container and run non-interactively (spark-sql -f).
docker cp "$SQL_FILE" "${CONTAINER}:/tmp/create_raw_tables.sql"
docker exec "$CONTAINER" spark-sql -f /tmp/create_raw_tables.sql

echo
echo "==> verify (SHOW TABLES IN demo.raw)"
docker exec "$CONTAINER" spark-sql -e "SHOW TABLES IN demo.raw;"
