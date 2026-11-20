#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONTAINER="${CCA_ICEBERG_SPARK_CONTAINER:-cca-spark-iceberg}"
RUN_ID="${CCA_CURATED_RUN_ID:-manual-$(date -u +%Y%m%dT%H%M%SZ)}"

docker inspect -f '{{.State.Running}}' "$CONTAINER" 2>/dev/null | grep -qx true || {
  echo "start iceberg first" >&2
  exit 1
}
bash "$ROOT/apply_curated_ddl.sh"

if docker exec "$CONTAINER" test -f /opt/cca/iceberg/scripts/hydrate_curated_3m.py; then
  SCRIPTS=/opt/cca/iceberg/scripts
else
  docker cp "$ROOT/parent_org.py" "${CONTAINER}:/tmp/parent_org.py"
  docker cp "$ROOT/hydrate_curated_3m.py" "${CONTAINER}:/tmp/hydrate_curated_3m.py"
  SCRIPTS=/tmp
fi

docker exec -e PYTHONPATH="$SCRIPTS" "$CONTAINER" \
  /opt/spark/bin/spark-submit "$SCRIPTS/hydrate_curated_3m.py" --run-id "$RUN_ID"
echo "done run_id=$RUN_ID"
