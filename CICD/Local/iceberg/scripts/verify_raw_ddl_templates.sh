#!/usr/bin/env bash
# Static checks for Raw DDL templates (M45-0001 / #320) — no Docker required.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SQL_FILE="${ROOT}/sql/create_raw_tables.sql"

fail() { echo "FAIL: $*" >&2; exit 1; }

[ -f "$SQL_FILE" ] || fail "missing $SQL_FILE"

for t in \
  cfpb_complaints_3m \
  cfpb_complaints_6m \
  cfpb_complaints_9m \
  cfpb_complaints_12m \
  cfpb_complaints_all \
  cfpb_complaints_quarantine
do
  grep -q "demo.raw.${t}" "$SQL_FILE" || fail "expected table demo.raw.${t}"
done

grep -q "CREATE NAMESPACE IF NOT EXISTS demo.raw" "$SQL_FILE" || fail "missing CREATE NAMESPACE"
grep -q "PARTITIONED BY (months(date_received))" "$SQL_FILE" || fail "missing months(date_received) partition"
grep -q "consumer_complaint_narrative" "$SQL_FILE" || fail "missing reserved narrative column"
grep -q "_row_hash" "$SQL_FILE" || fail "missing audit _row_hash"
grep -q "SHOW TABLES IN demo.raw" "$SQL_FILE" || fail "missing SHOW TABLES verify"

echo "OK: Raw DDL templates present for 5 slices + quarantine"
