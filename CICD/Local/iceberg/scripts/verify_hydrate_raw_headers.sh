#!/usr/bin/env bash
# TDD static check for Raw hydrate header map (M45-0002 / #321).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 - <<PY
import sys
sys.path.insert(0, "$ROOT")
from hydrate_raw_headers import (
    CFPB_HEADER_TO_RAW,
    RAW_SOURCE_COLUMNS,
    AUDIT_COLUMNS,
    MANDATORY_KEYS,
    normalize_header,
    rename_map_for_dataframe,
)

assert len(CFPB_HEADER_TO_RAW) == 15
assert len(RAW_SOURCE_COLUMNS) == 16
assert len(AUDIT_COLUMNS) == 5
assert normalize_header("Complaint ID") == "complaint_id"
assert normalize_header("\ufeffDate received") == "date_received"
m = rename_map_for_dataframe(list(CFPB_HEADER_TO_RAW.keys()))
assert m["ZIP code"] == "zip_code"
assert set(MANDATORY_KEYS) == {"complaint_id", "date_received", "product", "company"}
print("OK: hydrate_raw_headers")
PY
