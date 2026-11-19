"""Unit tests for parent_org helpers (M48-0001 / #326)."""

from __future__ import annotations

import importlib.util
import sys

from tests.conftest import REPO_ROOT

HELPER = REPO_ROOT / "CICD" / "Local" / "iceberg" / "scripts" / "parent_org.py"


def _load():
    spec = importlib.util.spec_from_file_location("parent_org", HELPER)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["parent_org"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_capital_one_aliases_share_parent_org_id():
    m = _load()
    a = m.parent_org_id_from_company("CAPITAL ONE FINANCIAL CORPORATION")
    b = m.parent_org_id_from_company("Capital One")
    assert a == b
    assert len(a) == 64
