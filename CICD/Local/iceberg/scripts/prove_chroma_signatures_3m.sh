#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONTAINER="${CCA_ICEBERG_SPARK_CONTAINER:-cca-spark-iceberg}"
CHROMA_URL="${CCA_CHROMA_URL:-http://127.0.0.1:8100}"
REPO="$(cd "$ROOT/../../../.." && pwd)"

parse_last_int() {
  tr -cd '0-9\n' | awk 'NF{print}' | tail -1
}

USIG=$(docker exec "$CONTAINER" spark-sql -e \
  "SELECT COUNT(*) FROM demo.taxonomy.semantic_signatures;" | parse_last_int)
USIG=${USIG:-0}

PROOF=$(REPO_ROOT="$REPO" SCRIPTS_DIR="$ROOT" CCA_CHROMA_URL="$CHROMA_URL" python3 - <<'PY'
import os, sys
from pathlib import Path
repo = Path(os.environ["REPO_ROOT"])
scripts = Path(os.environ["SCRIPTS_DIR"])
sys.path.insert(0, str(repo / "Middleware" / "Airflow-dags"))
sys.path.insert(0, str(scripts))
from ccaa import vector_index as vi
from signature_catalog import COLLECTION_NAME

url = os.environ.get("CCA_CHROMA_URL", "http://127.0.0.1:8100")
store = vi.ChromaStore(url, collection=COLLECTION_NAME)
n = store.count()
q = store.query_text("Credit card | Billing dispute", n_results=3)
ids = (q.get("ids") or [[]])[0]
metas = (q.get("metadatas") or [[]])[0]
hit = ids[0] if ids else ""
topic = ""
if metas and isinstance(metas[0], dict):
    topic = str(metas[0].get("primary_money_topic") or "")
print(f"chroma_count={n}")
print(f"query_hit_id={hit}")
print(f"query_hit_topic={topic}")
PY
)

echo "$PROOF"
CHROMA_N=$(echo "$PROOF" | awk -F= '/^chroma_count=/{print $2}')
HIT=$(echo "$PROOF" | awk -F= '/^query_hit_id=/{print $2}')

echo "taxonomy_usig=$USIG"
if [[ -z "$CHROMA_N" || "$CHROMA_N" -lt 1 ]]; then
  echo "FAIL: empty chroma collection" >&2
  exit 1
fi
if [[ -z "$HIT" ]]; then
  echo "FAIL: query returned no ids" >&2
  exit 1
fi
if [[ "$CHROMA_N" -ne "$USIG" ]]; then
  echo "WARN: chroma_count=$CHROMA_N != taxonomy_usig=$USIG" >&2
  python3 -c "import sys; usig=int('$USIG'); n=int('$CHROMA_N'); sys.exit(0 if abs(n-usig)<=max(5,int(0.05*usig)) else 1)" || {
    echo "FAIL: count mismatch beyond tolerance" >&2
    exit 1
  }
fi
echo "PASS: chroma catalog searchable collection=cfpb_semantic_signatures count=$CHROMA_N hit=$HIT"
