#!/usr/bin/env bash
# Host wrapper: foundational Iceberg DDL via docker exec (CI/dev). Prefer Admin Schemas WF.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONTAINER="${CCA_ICEBERG_SPARK_CONTAINER:-cca-spark-iceberg}"

if ! docker inspect -f '{{.State.Running}}' "$CONTAINER" 2>/dev/null | grep -qx true; then
  echo "container $CONTAINER is not running. Start with: npm run local:containers:iceberg:start" >&2
  exit 1
fi

# Ensure SQL is visible (compose mounts ./sql; fall back to docker cp of scripts folder helper).
if ! docker exec "$CONTAINER" test -f /opt/cca/iceberg/sql/create_raw_tables.sql; then
  echo "==> sql mount missing; copying $ROOT/sql into container"
  docker exec "$CONTAINER" mkdir -p /opt/cca/iceberg/sql
  docker cp "$ROOT/sql/." "${CONTAINER}:/opt/cca/iceberg/sql/"
fi

docker cp "$ROOT/scripts/apply_iceberg_foundational_ddl_incontainer.sh" \
  "${CONTAINER}:/tmp/apply_iceberg_foundational_ddl_incontainer.sh"
docker exec "$CONTAINER" chmod +x /tmp/apply_iceberg_foundational_ddl_incontainer.sh
docker exec "$CONTAINER" bash /tmp/apply_iceberg_foundational_ddl_incontainer.sh
