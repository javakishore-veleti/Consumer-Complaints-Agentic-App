"""Unit tests for signature_catalog helpers (M49-0001 / #336)."""

from __future__ import annotations

import importlib.util
import sys

from tests.conftest import REPO_ROOT

HELPER = REPO_ROOT / "CICD" / "Local" / "iceberg" / "scripts" / "signature_catalog.py"


def _load():
    spec = importlib.util.spec_from_file_location("signature_catalog", HELPER)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["signature_catalog"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_signature_to_catalog_doc_builds_id_text_metadata_embedding():
    m = _load()

    def fake_embed(text: str, *, dim: int = 32):
        return [0.1] * dim

    row = {
        "signature_id": "sig-1",
        "product": "Credit card",
        "sub_product": "General-purpose",
        "issue": "Billing",
        "sub_issue": "",
        "tags": "",
        "primary_money_topic": "Credit Cards",
        "secondary_money_topic": "",
        "is_fraud_scam": False,
        "is_money_transfer": False,
    }
    doc = m.signature_to_catalog_doc(row, hash_embedding=fake_embed, dim=8)
    assert doc["id"] == "sig-1"
    assert "Credit card" in doc["text"]
    assert "Credit Cards" in doc["text"]
    assert doc["metadata"]["primary_money_topic"] == "Credit Cards"
    assert len(doc["embedding"]) == 8


def test_signature_catalog_requires_signature_id():
    m = _load()
    try:
        m.signature_to_catalog_doc({}, hash_embedding=lambda t, dim=32: [0.0] * dim)
        raise AssertionError("expected ValueError")
    except ValueError as exc:
        assert "signature_id" in str(exc)
