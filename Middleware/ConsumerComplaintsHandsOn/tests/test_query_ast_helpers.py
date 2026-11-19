"""Unit tests for query_ast translator (M50-0001 / #338)."""

from __future__ import annotations

import importlib.util
import sys

import pytest

from tests.conftest import REPO_ROOT

HELPER = REPO_ROOT / "CICD" / "Local" / "iceberg" / "scripts" / "query_ast.py"


def _load():
    spec = importlib.util.spec_from_file_location("query_ast", HELPER)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["query_ast"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_ast_to_sql_and_eq_fields():
    m = _load()
    sql = m.ast_to_sql(
        {
            "table": "demo.curated.cfpb_complaints_3m",
            "filter_tree": {
                "op": "AND",
                "args": [
                    {"op": "EQ", "field": "parent_org_id", "value": "abc"},
                    {"op": "EQ", "field": "primary_money_topic", "value": "Credit Cards"},
                ],
            },
        }
    )
    assert "SELECT COUNT(*) AS n FROM demo.curated.cfpb_complaints_3m WHERE" in sql
    assert "parent_org_id = 'abc'" in sql
    assert "primary_money_topic = 'Credit Cards'" in sql


def test_rejects_disallowed_field_and_like():
    m = _load()
    with pytest.raises(ValueError, match="field not allowed"):
        m.ast_to_sql(
            {
                "filter_tree": {
                    "op": "EQ",
                    "field": "company_raw",
                    "value": "x",
                }
            }
        )


def test_k_anonymity():
    m = _load()
    m.assert_k_anonymous(10)
    with pytest.raises(ValueError, match="k-anonymity"):
        m.assert_k_anonymous(9)
