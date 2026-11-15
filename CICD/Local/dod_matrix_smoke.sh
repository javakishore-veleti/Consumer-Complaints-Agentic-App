#!/usr/bin/env bash
# M03-0013 DoD matrix smoke: SQLite + Mongo (always) + Postgres (when URL set).
# Exit 0 only if no FAIL cells. Postgres SKIP is OK unless CCA_DOD_REQUIRE_POSTGRES=1.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
MW="$ROOT/Middleware/ConsumerComplaintsHandsOn"
SQLITE_NODE="tests/test_e2e_happy_path_smoke.py::test_happy_path_start_callback_mios_status"
PG_NODE="tests/test_postgres.py::test_start_workflow_and_callback_persist_on_postgres"
MONGO_NODE="tests/test_mongodb_operational_store.py::test_start_workflow_and_callback_persist_on_mongo"

run_cell() {
  local name="$1"
  local node="$2"
  local required="$3"
  local status
  if [[ "$required" == "skip" ]]; then
    echo "SKIP  $name (CCA_TEST_POSTGRES_URL unset; set it or CCA_DOD_REQUIRE_POSTGRES=1 to require)"
    echo "SKIP" >"$ROOT/runtime_data/tmp/dod-matrix-$name.status"
    return 0
  fi
  if (cd "$MW" && uv run pytest "$node" -q); then
    status=PASS
  else
    status=FAIL
  fi
  echo "$status $name ($node)"
  echo "$status" >"$ROOT/runtime_data/tmp/dod-matrix-$name.status"
  [[ "$status" == "PASS" ]]
}

mkdir -p "$ROOT/runtime_data/tmp"

echo "=== DoD matrix smoke (M03-0013) ==="
fail=0

run_cell sqlite "$SQLITE_NODE" run || fail=1
run_cell mongodb "$MONGO_NODE" run || fail=1

pg_mode=run
if [[ -z "${CCA_TEST_POSTGRES_URL:-}" ]]; then
  if [[ "${CCA_DOD_REQUIRE_POSTGRES:-}" == "1" ]]; then
    echo "FAIL  postgres (CCA_DOD_REQUIRE_POSTGRES=1 but CCA_TEST_POSTGRES_URL unset)"
    echo "FAIL" >"$ROOT/runtime_data/tmp/dod-matrix-postgres.status"
    fail=1
    pg_mode=done
  else
    pg_mode=skip
  fi
fi
if [[ "$pg_mode" != "done" ]]; then
  run_cell postgres "$PG_NODE" "$pg_mode" || fail=1
fi

echo
echo "=== Matrix summary ==="
printf "%-10s %s\n" "sqlite" "$(cat "$ROOT/runtime_data/tmp/dod-matrix-sqlite.status")"
printf "%-10s %s\n" "postgres" "$(cat "$ROOT/runtime_data/tmp/dod-matrix-postgres.status")"
printf "%-10s %s\n" "mongodb" "$(cat "$ROOT/runtime_data/tmp/dod-matrix-mongodb.status")"

if [[ "$fail" -ne 0 ]]; then
  echo "DoD matrix smoke FAILED"
  exit 1
fi
echo "DoD matrix smoke OK"
exit 0
