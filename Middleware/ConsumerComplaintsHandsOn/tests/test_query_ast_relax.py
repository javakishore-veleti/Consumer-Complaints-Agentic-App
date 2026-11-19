"""M54 Query AST relaxation (#366 / #368)."""

from pathlib import Path
import json

from app.core.common.query_ast import RelaxAstReq, relax_ast

REPO_ROOT = Path(__file__).resolve().parents[3]
GOLDEN = REPO_ROOT / "CICD" / "Local" / "iceberg" / "golden" / "query_ast_relax_golden_3m.json"


def test_relax_ast_golden_steps():
    data = json.loads(GOLDEN.read_text(encoding="utf-8"))
    case = data["cases"][0]
    steps = relax_ast(RelaxAstReq(case["ast"]))
    assert [s.step for s in steps] == case["expect_steps"]
    assert "zip3" not in steps[0].sql
    assert "Credit Cards" in steps[-1].sql


def test_query_ast_relax_trail_without_execute(client):
    data = json.loads(GOLDEN.read_text(encoding="utf-8"))
    case = data["cases"][0]
    response = client.post(
        "/intellect/query-ast",
        json={"ast": case["ast"], "execute": False, "relax": True},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["sql"]
    assert [s["step"] for s in body["relaxation"]] == case["expect_steps"]
    assert body["relaxation"][0]["reason"]
    assert body["relaxation"][0]["sql"]


def test_query_ast_relax_false_has_empty_trail(client):
    data = json.loads(GOLDEN.read_text(encoding="utf-8"))
    case = data["cases"][0]
    response = client.post(
        "/intellect/query-ast",
        json={"ast": case["ast"], "execute": False, "relax": False},
    )
    assert response.status_code == 200
    assert response.json()["relaxation"] == []
