#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONTAINER="${CCA_ICEBERG_SPARK_CONTAINER:-cca-spark-iceberg}"

docker inspect -f '{{.State.Running}}' "$CONTAINER" 2>/dev/null | grep -qx true || {
  echo "start iceberg first (npm run local:containers:iceberg:start)" >&2
  exit 1
}

python3 "$ROOT/run_query_ast_golden_3m.py" --container "$CONTAINER"
