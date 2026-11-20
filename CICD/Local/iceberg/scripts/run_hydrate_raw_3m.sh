#!/usr/bin/env bash
# Stage Lift 3m zips inside Spark container and hydrate Iceberg Raw (M45-0002 / #321).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONTAINER="${CCA_ICEBERG_SPARK_CONTAINER:-cca-spark-iceberg}"
RUN_ID="${CCA_RAW_RUN_ID:-manual-$(date -u +%Y%m%dT%H%M%SZ)}"
LIMIT_ARGS=()
if [ "${CCA_RAW_LIMIT:-0}" != "0" ]; then
  LIMIT_ARGS=(--limit "${CCA_RAW_LIMIT}")
fi

if ! docker inspect -f '{{.State.Running}}' "$CONTAINER" 2>/dev/null | grep -qx true; then
  echo "container $CONTAINER is not running. Start with: npm run local:containers:iceberg:start" >&2
  exit 1
fi

echo "==> copy hydrate scripts into $CONTAINER"
docker cp "$ROOT/hydrate_raw_headers.py" "${CONTAINER}:/tmp/hydrate_raw_headers.py"
docker cp "$ROOT/hydrate_raw_3m.py" "${CONTAINER}:/tmp/hydrate_raw_3m.py"
docker cp "$ROOT/stage_unzip_3m.sh" "${CONTAINER}:/tmp/stage_unzip_3m.sh"
docker exec "$CONTAINER" chmod +x /tmp/stage_unzip_3m.sh /tmp/hydrate_raw_3m.py

echo "==> stage unzip run_id=$RUN_ID"
STAGE_DIR=$(docker exec -e CCA_LIFT_ZONE_IN_CONTAINER=/lift "$CONTAINER" \
  bash /tmp/stage_unzip_3m.sh "$RUN_ID" | tee /dev/stderr | tail -1)

echo "==> /opt/spark/bin/spark-submit hydrate stage=$STAGE_DIR"
docker exec \
  -e PYTHONPATH=/tmp \
  "$CONTAINER" \
  /opt/spark/bin/spark-submit /tmp/hydrate_raw_3m.py \
    --stage-dir "$STAGE_DIR" \
    --run-id "$RUN_ID" \
    --slice 3m \
    "${LIMIT_ARGS[@]+"${LIMIT_ARGS[@]}"}"

echo "==> done run_id=$RUN_ID"
