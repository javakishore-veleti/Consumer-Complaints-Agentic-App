"""Unit tests for Iceberg refined_signature helpers (M46-0001 / #324)."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from tests.conftest import REPO_ROOT

HELPER = REPO_ROOT / "CICD" / "Local" / "iceberg" / "scripts" / "refined_signature.py"


def _load():
    spec = importlib.util.spec_from_file_location("refined_signature", HELPER)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["refined_signature"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_signature_id_stable_under_case_and_whitespace():
    m = _load()
    a = m.signature_id_from_fields("Credit card", "", "Billing", "", "", "Closed")
    b = m.signature_id_from_fields("  CREDIT CARD ", None, "Billing", "", "", "Closed")
    assert a == b
    assert len(a) == 64


def test_zip3_hygiene():
    m = _load()
    assert m.zip3_from_zip_code("90001") == "900"
    assert m.zip3_from_zip_code("90001-1234") == "900"
    assert m.zip3_from_zip_code("12") == "UNK"
    assert m.zip3_from_zip_code(None) == "UNK"
