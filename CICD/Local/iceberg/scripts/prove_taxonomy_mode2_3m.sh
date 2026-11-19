#!/usr/bin/env bash
# Prove taxonomy Mode 2 for 3m (M47-0001 / #325).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONTAINER="${CCA_ICEBERG_SPARK_CONTAINER:-cca-spark-iceberg}"
REPO_ROOT="$(cd "$ROOT/../../../.." && pwd)"
EVIDENCE_DIR="${CCA_TAXONOMY_PROOF_DIR:-$REPO_ROOT/runtime_data/tmp}"
mkdir -p "$EVIDENCE_DIR"
STAMP=$(date -u +%Y%m%dT%H%M%SZ)
EVIDENCE="$EVIDENCE_DIR/taxonomy-mode2-3m-proof-$STAMP.txt"

parse_last_int() {
  python3 -c "import re,sys; nums=re.findall(r'\d+', sys.stdin.read()); print(nums[-1] if nums else '')"
}

CCA_TAXONOMY_RUN_ID="proof-$STAMP" bash "$ROOT/run_hydrate_taxonomy_mode2_3m.sh"

TOPICS=$(docker exec "$CONTAINER" spark-sql -e "SELECT COUNT(*) FROM demo.taxonomy.money_topics;" | parse_last_int)
XWALK=$(docker exec "$CONTAINER" spark-sql -e "SELECT COUNT(*) FROM demo.taxonomy.product_crosswalk;" | parse_last_int)
USIG=$(docker exec "$CONTAINER" spark-sql -e "SELECT COUNT(*) FROM demo.taxonomy.semantic_signatures;" | parse_last_int)
EXPECTED_USIG=$(docker exec "$CONTAINER" spark-sql -e "
SELECT COUNT(DISTINCT concat_ws('||',
  lower(trim(coalesce(product,''))),
  lower(trim(coalesce(sub_product,''))),
  lower(trim(coalesce(issue,''))),
  lower(trim(coalesce(sub_issue,''))),
  lower(trim(coalesce(tags,'')))))
FROM demo.refined.cfpb_complaints_3m;" | parse_last_int)

DEMO=$(docker exec "$CONTAINER" spark-sql -e "
SELECT r.company, r.product, s.primary_money_topic, s.secondary_money_topic, s.signature_id
FROM demo.refined.cfpb_complaints_3m r
JOIN demo.taxonomy.semantic_signatures s
  ON lower(trim(coalesce(r.product,''))) = lower(trim(coalesce(s.product,'')))
 AND lower(trim(coalesce(r.sub_product,''))) = lower(trim(coalesce(s.sub_product,'')))
 AND lower(trim(coalesce(r.issue,''))) = lower(trim(coalesce(s.issue,'')))
 AND lower(trim(coalesce(r.sub_issue,''))) = lower(trim(coalesce(s.sub_issue,'')))
 AND lower(trim(coalesce(r.tags,''))) = lower(trim(coalesce(s.tags,'')))
WHERE lower(r.company) LIKE '%capital one%'
LIMIT 3;
")

{
  echo "stamp=$STAMP"
  echo "money_topics=$TOPICS"
  echo "product_crosswalk=$XWALK"
  echo "semantic_signatures=$USIG"
  echo "expected_u_sig=$EXPECTED_USIG"
  echo
  echo "=== Capital One demo ==="
  echo "$DEMO"
} | tee "$EVIDENCE"

[ "$TOPICS" = "12" ] || { echo "FAIL money_topics=$TOPICS" >&2; exit 2; }
[ "$XWALK" -ge 50 ] || { echo "FAIL crosswalk=$XWALK (need ~55 U_prod)" >&2; exit 3; }
[ "$USIG" = "$EXPECTED_USIG" ] || { echo "FAIL sig count $USIG != $EXPECTED_USIG" >&2; exit 4; }
echo "$DEMO" | grep -qi "capital one" || { echo "FAIL Capital One demo empty" >&2; exit 5; }
echo "$DEMO" | grep -Eq "Credit Cards|Bank Accounts|Credit Reports|Debt Collection|Money Transfers|Fraud" || {
  echo "FAIL missing primary_money_topic in demo" >&2
  exit 6
}

echo "PASS: topics=12 crosswalk=$XWALK u_sig=$USIG evidence=$EVIDENCE"
