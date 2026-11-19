#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 - <<PY
import sys
sys.path.insert(0, "$ROOT")
from mode2_classify import MONEY_TOPICS, classify_signature, primary_topic_from_product, registry_signature_id

assert len(MONEY_TOPICS) == 12
assert primary_topic_from_product("Credit card", "General-purpose credit card or charge card") == "Credit Cards"
assert primary_topic_from_product("Mortgage", "Reverse mortgage") == "Reverse Mortgages"
assert primary_topic_from_product("Vehicle loan or lease", "Loan") == "Auto Loans"
a = registry_signature_id("Credit card", "", "Billing dispute", "", "")
b = registry_signature_id("  CREDIT CARD ", None, "Billing dispute", "", "")
assert a == b and len(a) == 64
out = classify_signature("Checking or savings account", "Checking account", "Fraud or scam", "", "")
assert out["primary_money_topic"] == "Bank Accounts & Services"
assert out["is_fraud_scam"] is True
assert out["secondary_money_topic"] == "Fraud & Scams"
print("OK: mode2_classify")
PY
