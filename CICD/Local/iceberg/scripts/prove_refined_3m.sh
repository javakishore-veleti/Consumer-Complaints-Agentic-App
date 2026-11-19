#!/usr/bin/env bash
# Prove refined 3m reconciles from Raw and has signature_id (M46-0001 / #324).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONTAINER="${CCA_ICEBERG_SPARK_CONTAINER:-cca-spark-iceberg}"
RAW="${CCA_RAW_TABLE:-demo.raw.cfpb_complaints_3m}"
REF="${CCA_REFINED_TABLE:-demo.refined.cfpb_complaints_3m}"
REPO_ROOT="$(cd "$ROOT/../../../.." && pwd)"
EVIDENCE_DIR="${CCA_REFINED_PROOF_DIR:-$REPO_ROOT/runtime_data/tmp}"
mkdir -p "$EVIDENCE_DIR"
STAMP=$(date -u +%Y%m%dT%H%M%SZ)
EVIDENCE="$EVIDENCE_DIR/refined-3m-proof-$STAMP.txt"

docker inspect -f '{{.State.Running}}' "$CONTAINER" 2>/dev/null | grep -qx true || {
  echo "iceberg not running" >&2
  exit 1
}

bash "$ROOT/apply_refined_ddl.sh"
CCA_REFINED_RUN_ID="proof-$STAMP" bash "$ROOT/run_hydrate_refined_3m.sh"

parse_last_int() {
  python3 -c "import re,sys; nums=re.findall(r'\d+', sys.stdin.read()); print(nums[-1] if nums else '')"
}

RAW_N=$(docker exec "$CONTAINER" spark-sql -e "SELECT COUNT(*) FROM ${RAW};" | parse_last_int)
REF_N=$(docker exec "$CONTAINER" spark-sql -e "SELECT COUNT(*) FROM ${REF};" | parse_last_int)
SIG_N=$(docker exec "$CONTAINER" spark-sql -e "SELECT COUNT(DISTINCT signature_id) FROM ${REF};" | parse_last_int)
NULL_SIG=$(docker exec "$CONTAINER" spark-sql -e "SELECT SUM(CASE WHEN signature_id IS NULL OR TRIM(signature_id)='' THEN 1 ELSE 0 END) FROM ${REF};" | parse_last_int)
DEMO=$(docker exec "$CONTAINER" spark-sql -e "SELECT COUNT(*) AS n, COUNT(DISTINCT signature_id) AS u_sig FROM ${REF};")

{
  echo "stamp=$STAMP"
  echo "raw_count=$RAW_N"
  echo "refined_count=$REF_N"
  echo "distinct_signature_id=$SIG_N"
  echo "null_signature_id=$NULL_SIG"
  echo
  echo "=== operator demo ==="
  echo "$DEMO"
} | tee "$EVIDENCE"

[ "$REF_N" = "$RAW_N" ] || { echo "FAIL count mismatch" >&2; exit 2; }
[ "${NULL_SIG:-1}" = "0" ] || { echo "FAIL null signature_id" >&2; exit 3; }
[ "${SIG_N:-0}" -gt 0 ] || { echo "FAIL no distinct signature_id" >&2; exit 4; }

echo "PASS: refined=$REF_N raw=$RAW_N u_sig=$SIG_N evidence=$EVIDENCE"
