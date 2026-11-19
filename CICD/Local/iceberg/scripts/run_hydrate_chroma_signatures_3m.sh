#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONTAINER="${CCA_ICEBERG_SPARK_CONTAINER:-cca-spark-iceberg}"
CHROMA_URL="${CCA_CHROMA_URL:-http://127.0.0.1:8100}"

docker inspect -f '{{.State.Running}}' "$CONTAINER" 2>/dev/null | grep -qx true || {
  echo "start iceberg first (npm run local:containers:iceberg:start)" >&2
  exit 1
}

python3 "$ROOT/hydrate_chroma_signatures_3m.py" \
  --chroma-url "$CHROMA_URL" \
  --container "$CONTAINER"
echo "done chroma catalog hydrate"
