"""Unit tests for Mode 2 classify helpers (M47-0001 / #325)."""

from __future__ import annotations

import importlib.util
import sys

from tests.conftest import REPO_ROOT

HELPER = REPO_ROOT / "CICD" / "Local" / "iceberg" / "scripts" / "mode2_classify.py"


def _load():
    spec = importlib.util.spec_from_file_location("mode2_classify", HELPER)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["mode2_classify"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_twelve_money_topics_and_credit_card_cue():
    m = _load()
    assert len(m.MONEY_TOPICS) == 12
    assert (
        m.primary_topic_from_product("Credit card", "General-purpose credit card or charge card")
        == "Credit Cards"
    )


def test_fraud_overlay_on_bank_account():
    m = _load()
    out = m.classify_signature(
        "Checking or savings account", "Checking account", "Fraud or scam", "", ""
    )
    assert out["primary_money_topic"] == "Bank Accounts & Services"
    assert out["is_fraud_scam"] is True
    assert out["secondary_money_topic"] == "Fraud & Scams"
