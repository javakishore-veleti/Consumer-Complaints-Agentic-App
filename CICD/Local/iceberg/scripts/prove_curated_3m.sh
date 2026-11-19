#!/usr/bin/env bash
# Prove curated 3m Money Topics + parent_org (M48-0001 / #326).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONTAINER="${CCA_ICEBERG_SPARK_CONTAINER:-cca-spark-iceberg}"
REPO_ROOT="$(cd "$ROOT/../../../.." && pwd)"
EVIDENCE_DIR="${CCA_CURATED_PROOF_DIR:-$REPO_ROOT/runtime_data/tmp}"
mkdir -p "$EVIDENCE_DIR"
STAMP=$(date -u +%Y%m%dT%H%M%SZ)
EVIDENCE="$EVIDENCE_DIR/curated-3m-proof-$STAMP.txt"

parse_last_int() {
  python3 -c "import re,sys; nums=re.findall(r'\d+', sys.stdin.read()); print(nums[-1] if nums else '')"
}

CCA_CURATED_RUN_ID="proof-$STAMP" bash "$ROOT/run_hydrate_curated_3m.sh"

REF=$(docker exec "$CONTAINER" spark-sql -e "SELECT COUNT(*) FROM demo.refined.cfpb_complaints_3m;" | parse_last_int)
CUR=$(docker exec "$CONTAINER" spark-sql -e "SELECT COUNT(*) FROM demo.curated.cfpb_complaints_3m;" | parse_last_int)
NULL_TOPIC=$(docker exec "$CONTAINER" spark-sql -e "SELECT SUM(CASE WHEN primary_money_topic IS NULL OR TRIM(primary_money_topic)='' THEN 1 ELSE 0 END) FROM demo.curated.cfpb_complaints_3m;" | parse_last_int)
NULL_ORG=$(docker exec "$CONTAINER" spark-sql -e "SELECT SUM(CASE WHEN parent_org_id IS NULL OR TRIM(parent_org_id)='' THEN 1 ELSE 0 END) FROM demo.curated.cfpb_complaints_3m;" | parse_last_int)
GROUPBY=$(docker exec "$CONTAINER" spark-sql -e "
SELECT primary_money_topic, COUNT(*) AS n
FROM demo.curated.cfpb_complaints_3m
GROUP BY primary_money_topic
ORDER BY n DESC;
")
CAPONE=$(docker exec "$CONTAINER" spark-sql -e "
SELECT parent_org_name, primary_money_topic, COUNT(*) n
FROM demo.curated.cfpb_complaints_3m
WHERE lower(parent_org_name) LIKE '%capital one%'
GROUP BY parent_org_name, primary_money_topic
ORDER BY n DESC
LIMIT 5;
")

{
  echo "stamp=$STAMP"
  echo "refined_count=$REF"
  echo "curated_count=$CUR"
  echo "null_primary_money_topic=$NULL_TOPIC"
  echo "null_parent_org_id=$NULL_ORG"
  echo
  echo "=== SparkSQL group-by Money Topic ==="
  echo "$GROUPBY"
  echo
  echo "=== Capital One by Money Topic ==="
  echo "$CAPONE"
} | tee "$EVIDENCE"

# Optional DuckDB demo if installed (reads SparkSQL evidence already; try parquet path via spark)
if command -v duckdb >/dev/null 2>&1; then
  echo "=== DuckDB note ===" | tee -a "$EVIDENCE"
  echo "duckdb present: SparkSQL group-by is authoritative for this prove; DuckDB Iceberg rest optional." | tee -a "$EVIDENCE"
fi

[ "$CUR" = "$REF" ] || { echo "FAIL curated=$CUR refined=$REF" >&2; exit 2; }
[ "${NULL_TOPIC:-1}" = "0" ] || { echo "FAIL null topics" >&2; exit 3; }
[ "${NULL_ORG:-1}" = "0" ] || { echo "FAIL null parent_org_id" >&2; exit 4; }
echo "$GROUPBY" | grep -qi "Credit Reports" || { echo "FAIL group-by missing Credit Reports" >&2; exit 5; }
echo "$CAPONE" | grep -qi "capital one" || { echo "FAIL Capital One demo empty" >&2; exit 6; }

echo "PASS: curated=$CUR topics populated; evidence=$EVIDENCE"
