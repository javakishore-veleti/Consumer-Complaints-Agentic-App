#!/usr/bin/env bash
# Prove Lift 3m row count reconciles to demo.raw.cfpb_complaints_3m (M45-0004 / #323).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONTAINER="${CCA_ICEBERG_SPARK_CONTAINER:-cca-spark-iceberg}"
TABLE="${CCA_RAW_TABLE:-demo.raw.cfpb_complaints_3m}"
QTABLE="${CCA_RAW_QUARANTINE_TABLE:-demo.raw.cfpb_complaints_quarantine}"
LIFT_HOST="${CCA_LIFT_ZONE:-$HOME/runtime_data/apps/datasets/CCA/complains_datasets}"
REPO_ROOT="$(cd "$ROOT/../../../.." && pwd)"
EVIDENCE_DIR="${CCA_RAW_PROOF_DIR:-$REPO_ROOT/runtime_data/tmp}"
mkdir -p "$EVIDENCE_DIR"
STAMP=$(date -u +%Y%m%dT%H%M%SZ)
EVIDENCE="$EVIDENCE_DIR/raw-3m-proof-$STAMP.txt"

if ! docker inspect -f '{{.State.Running}}' "$CONTAINER" 2>/dev/null | grep -qx true; then
  echo "container $CONTAINER is not running" >&2
  exit 1
fi

# Lift expected count (host-side, same zips Spark reads via /lift)
EXPECTED=$(python3 - <<PY
import glob, os, zipfile
lift=os.path.expanduser("$LIFT_HOST")
batches=sorted(glob.glob(lift+"/imports/*/dataset"))
latest=None
for b in batches:
    if glob.glob(b+"/*3_months*.csv.zip"):
        latest=b
assert latest, "no 3m batch"
rows=0
for z in sorted(glob.glob(latest+"/*3_months*.csv.zip")):
    with zipfile.ZipFile(z) as zf:
        name=zf.namelist()[0]
        with zf.open(name) as f:
            rows += max(sum(1 for _ in f)-1, 0)
print(rows)
print(latest, file=__import__('sys').stderr)
PY
)

echo "expected_lift_rows=$EXPECTED"
echo "==> full hydrate"
CCA_RAW_RUN_ID="proof-$STAMP" bash "$ROOT/run_hydrate_raw_3m.sh"

echo "==> SparkSQL counts"
COUNT_OUT=$(docker exec "$CONTAINER" spark-sql -e "SELECT COUNT(*) FROM ${TABLE};")
Q_OUT=$(docker exec "$CONTAINER" spark-sql -e "SELECT COUNT(*) FROM ${QTABLE};")
BAD_OUT=$(docker exec "$CONTAINER" spark-sql -e "SELECT SUM(CASE WHEN date_received IS NULL THEN 1 ELSE 0 END)+SUM(CASE WHEN complaint_id IS NULL OR TRIM(CAST(complaint_id AS STRING))='' THEN 1 ELSE 0 END)+SUM(CASE WHEN product IS NULL OR TRIM(CAST(product AS STRING))='' THEN 1 ELSE 0 END)+SUM(CASE WHEN company IS NULL OR TRIM(CAST(company AS STRING))='' THEN 1 ELSE 0 END) AS bad_keys FROM ${TABLE};")
SAMPLE_OUT=$(docker exec "$CONTAINER" spark-sql -e "SELECT complaint_id, date_received, product, company FROM ${TABLE} LIMIT 3;")

parse_last_int() {
  python3 -c "import re,sys; nums=re.findall(r'\d+', sys.stdin.read()); print(nums[-1] if nums else '')"
}

ACTUAL=$(printf '%s' "$COUNT_OUT" | parse_last_int)
QCOUNT=$(printf '%s' "$Q_OUT" | parse_last_int)
BAD=$(printf '%s' "$BAD_OUT" | parse_last_int)

{
  echo "stamp=$STAMP"
  echo "table=$TABLE"
  echo "expected_lift_rows=$EXPECTED"
  echo "actual_iceberg_rows=$ACTUAL"
  echo "quarantine_rows=$QCOUNT"
  echo "mandatory_key_bad_rows=$BAD"
  echo
  echo "=== COUNT(*) ==="
  echo "$COUNT_OUT"
  echo "=== quarantine COUNT(*) ==="
  echo "$Q_OUT"
  echo "=== bad_keys ==="
  echo "$BAD_OUT"
  echo "=== sample ==="
  echo "$SAMPLE_OUT"
} | tee "$EVIDENCE"

if [ "$ACTUAL" != "$EXPECTED" ]; then
  echo "FAIL: count mismatch actual=$ACTUAL expected=$EXPECTED" >&2
  exit 2
fi
if [ "${BAD:-1}" != "0" ]; then
  echo "FAIL: mandatory key bad rows=$BAD" >&2
  exit 3
fi

echo "PASS: reconciled $ACTUAL rows; quarantine=$QCOUNT; evidence=$EVIDENCE"
