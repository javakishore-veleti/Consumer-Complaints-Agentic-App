"""POST /intellect/query-ast (M52-0001 / #352)."""

import json
from pathlib import Path

from tests.conftest import REPO_ROOT

GOLDEN = REPO_ROOT / "CICD" / "Local" / "iceberg" / "golden" / "query_ast_golden_3m.json"


def test_query_ast_translates_golden_without_execute(client):
    case = json.loads(GOLDEN.read_text(encoding="utf-8"))["cases"][0]
    response = client.post("/intellect/query-ast", json={"ast": case["ast"], "execute": False})
    assert response.status_code == 200
    body = response.json()
    assert body["executed"] is False
    assert body["count"] is None
    assert "SELECT COUNT(*) AS n FROM demo.curated.cfpb_complaints_3m WHERE" in body["sql"]
    assert "primary_money_topic = 'Credit Cards'" in body["sql"]


def test_query_ast_rejects_bad_field(client):
    response = client.post(
        "/intellect/query-ast",
        json={"ast": {"filter_tree": {"op": "EQ", "field": "company_raw", "value": "x"}}},
    )
    assert response.status_code == 422


def test_query_ast_execute_without_warehouse_is_503(client, monkeypatch):
    monkeypatch.setattr(
        "app.core.services.impl.query_ast_service_impl._container_running",
        lambda _req: False,
    )
    case = json.loads(GOLDEN.read_text(encoding="utf-8"))["cases"][0]
    response = client.post("/intellect/query-ast", json={"ast": case["ast"], "execute": True})
    assert response.status_code == 503
    assert "warehouse unavailable" in response.json()["detail"]


def test_openapi_includes_query_ast(client):
    spec = client.get("/openapi.json").json()
    assert "/intellect/query-ast" in spec["paths"]
