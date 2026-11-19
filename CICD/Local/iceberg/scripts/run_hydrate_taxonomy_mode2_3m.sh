#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ICEBERG_ROOT="$(cd "$ROOT/.." && pwd)"
CONTAINER="${CCA_ICEBERG_SPARK_CONTAINER:-cca-spark-iceberg}"
RUN_ID="${CCA_TAXONOMY_RUN_ID:-manual-$(date -u +%Y%m%dT%H%M%SZ)}"

docker inspect -f '{{.State.Running}}' "$CONTAINER" 2>/dev/null | grep -qx true || {
  echo "start iceberg first" >&2
  exit 1
}

bash "$ROOT/apply_taxonomy_ddl.sh"

if docker exec "$CONTAINER" test -f /opt/cca/iceberg/scripts/hydrate_taxonomy_mode2_3m.py; then
  SCRIPTS=/opt/cca/iceberg/scripts
  TOPICS=/opt/cca/iceberg/taxonomy/money_topics.json
  # ensure taxonomy json mounted — if missing, copy
  if ! docker exec "$CONTAINER" test -f "$TOPICS"; then
    docker exec "$CONTAINER" mkdir -p /opt/cca/iceberg/taxonomy || true
    docker cp "$ICEBERG_ROOT/taxonomy/money_topics.json" "${CONTAINER}:/opt/cca/iceberg/taxonomy/money_topics.json"
  fi
else
  docker cp "$ROOT/mode2_classify.py" "${CONTAINER}:/tmp/mode2_classify.py"
  docker cp "$ROOT/hydrate_taxonomy_mode2_3m.py" "${CONTAINER}:/tmp/hydrate_taxonomy_mode2_3m.py"
  docker cp "$ICEBERG_ROOT/taxonomy/money_topics.json" "${CONTAINER}:/tmp/money_topics.json"
  SCRIPTS=/tmp
  TOPICS=/tmp/money_topics.json
fi

docker exec -e PYTHONPATH="$SCRIPTS" "$CONTAINER" \
  spark-submit "$SCRIPTS/hydrate_taxonomy_mode2_3m.py" \
    --money-topics-json "$TOPICS" \
    --run-id "$RUN_ID"
echo "done run_id=$RUN_ID"
