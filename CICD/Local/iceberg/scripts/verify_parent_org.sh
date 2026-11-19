#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 - <<PY
import sys
sys.path.insert(0, "$ROOT")
from parent_org import parent_org_id_from_company, canonical_parent_org_name

a = parent_org_id_from_company("CAPITAL ONE FINANCIAL CORPORATION")
b = parent_org_id_from_company("Capital One")
assert a == b and len(a) == 64
assert canonical_parent_org_name("Capital One Bank") == "CAPITAL ONE FINANCIAL CORPORATION"
print("OK: parent_org")
PY
