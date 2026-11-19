#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 - <<PY
import sys
sys.path.insert(0, "$ROOT")
from refined_signature import signature_id_from_fields, zip3_from_zip_code

a = signature_id_from_fields("Credit card", "", "Billing", "", "", "Closed")
b = signature_id_from_fields("  CREDIT CARD ", None, "Billing", "", "", "Closed")
assert a == b and len(a) == 64
assert zip3_from_zip_code("90001") == "900"
assert zip3_from_zip_code("90001-1234") == "900"
assert zip3_from_zip_code("12") == "UNK"
assert zip3_from_zip_code(None) == "UNK"
print("OK: refined_signature")
PY
