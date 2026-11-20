#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONTAINER="${CCA_ICEBERG_SPARK_CONTAINER:-cca-spark-iceberg}"
RUN_ID="${CCA_REFINED_RUN_ID:-manual-$(date -u +%Y%m%dT%H%M%SZ)}"

docker inspect -f '{{.State.Running}}' "$CONTAINER" 2>/dev/null | grep -qx true || {
  echo "start iceberg first: npm run local:containers:iceberg:start" >&2
  exit 1
}

# Prefer mounted scripts path; fall back to docker cp.
if docker exec "$CONTAINER" test -f /opt/cca/iceberg/scripts/hydrate_refined_3m.py; then
  SCRIPTS=/opt/cca/iceberg/scripts
else
  docker cp "$ROOT/hydrate_refined_3m.py" "${CONTAINER}:/tmp/hydrate_refined_3m.py"
  docker cp "$ROOT/refined_signature.py" "${CONTAINER}:/tmp/refined_signature.py"
  SCRIPTS=/tmp
fi

docker exec -e PYTHONPATH="$SCRIPTS" "$CONTAINER" \
  /opt/spark/bin/spark-submit "$SCRIPTS/hydrate_refined_3m.py" --run-id "$RUN_ID"
echo "done run_id=$RUN_ID"
