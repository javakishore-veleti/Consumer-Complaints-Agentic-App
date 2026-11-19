"""Unit tests for query_ast translator (M50-0001 / #338; home M52-0001 / #352)."""

from __future__ import annotations

import pytest

from app.core.common import query_ast as m


def test_ast_to_sql_and_eq_fields():
    sql = m.ast_to_sql(
        m.AstToSqlReq(
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
    )
    assert "SELECT COUNT(*) AS n FROM demo.curated.cfpb_complaints_3m WHERE" in sql
    assert "parent_org_id = 'abc'" in sql
    assert "primary_money_topic = 'Credit Cards'" in sql


def test_rejects_disallowed_field_and_like():
    with pytest.raises(ValueError, match="field not allowed"):
        m.ast_to_sql(
            m.AstToSqlReq(
                {
                    "filter_tree": {
                        "op": "EQ",
                        "field": "company_raw",
                        "value": "x",
                    }
                }
            )
        )


def test_k_anonymity():
    m.assert_k_anonymous(m.KAnonReq(10))
    with pytest.raises(ValueError, match="k-anonymity"):
        m.assert_k_anonymous(m.KAnonReq(9))


def test_cicd_shim_reexports():
    import importlib.util
    import sys

    from tests.conftest import REPO_ROOT

    helper = REPO_ROOT / "CICD" / "Local" / "iceberg" / "scripts" / "query_ast.py"
    spec = importlib.util.spec_from_file_location("query_ast_shim", helper)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["query_ast_shim"] = mod
    spec.loader.exec_module(mod)
    assert mod.ast_to_sql is m.ast_to_sql
