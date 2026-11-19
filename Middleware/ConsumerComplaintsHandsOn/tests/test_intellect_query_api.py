"""POST /intellect/query (D90)."""

import json
from pathlib import Path

from app.core.common.vector_search import HashEmbeddingReq, hash_embedding


def _seed_store(tmp_path: Path) -> Path:
    store = tmp_path / "vectors"
    store.mkdir()
    row = {
        "id": "c1",
        "text": "Credit card billing overcharge",
        "embedding": hash_embedding(HashEmbeddingReq(text="Credit card billing overcharge")),
    }
    (store / "complaints.jsonl").write_text(json.dumps(row) + "\n", encoding="utf-8")
    return store


def test_query_returns_ranked_hits(client, tmp_path, monkeypatch):
    store = _seed_store(tmp_path)
    monkeypatch.setenv("CCA_VECTOR_STORE_PATH", str(store))
    response = client.post("/intellect/query", json={"query": "billing overcharge", "limit": 3})
    assert response.status_code == 200
    body = response.json()
    assert body["hits"]
    assert body["hits"][0]["id"] == "c1"
    assert body["config"] == "baseline"


def test_hybrid_config_query(client, tmp_path, monkeypatch):
    store = _seed_store(tmp_path)
    monkeypatch.setenv("CCA_VECTOR_STORE_PATH", str(store))
    response = client.post(
        "/intellect/query",
        json={"query": "billing overcharge", "limit": 3, "config": "hybrid"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["config"] == "hybrid"
    assert body["hits"][0]["id"] == "c1"


def test_blank_query_is_422(client, tmp_path, monkeypatch):
    monkeypatch.setenv("CCA_VECTOR_STORE_PATH", str(tmp_path))
    response = client.post("/intellect/query", json={"query": "  "})
    assert response.status_code == 422


def test_unknown_config_is_422(client, tmp_path, monkeypatch):
    monkeypatch.setenv("CCA_VECTOR_STORE_PATH", str(tmp_path))
    response = client.post("/intellect/query", json={"query": "x", "config": "paid_llm"})
    assert response.status_code == 422


def test_path_is_in_openapi(client):
    spec = client.get("/openapi.json").json()
    assert "/intellect/query" in spec["paths"]


def test_signatures_config_uses_jsonl_catalog(client, tmp_path, monkeypatch):
    store = tmp_path / "vectors"
    store.mkdir()
    row = {
        "id": "sig-cc",
        "text": "Credit card | Billing dispute | Credit Cards",
        "embedding": hash_embedding(HashEmbeddingReq(text="Credit card Billing dispute Credit Cards")),
    }
    (store / "cfpb_semantic_signatures.jsonl").write_text(json.dumps(row) + "\n", encoding="utf-8")
    monkeypatch.setenv("CCA_VECTOR_STORE_PATH", str(store))
    response = client.post(
        "/intellect/query",
        json={"query": "credit card billing", "limit": 3, "config": "signatures"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["config"] == "signatures"
    assert body["hits"]
    assert body["hits"][0]["id"] == "sig-cc"


def test_signatures_config_empty_catalog_is_ok(client, tmp_path, monkeypatch):
    monkeypatch.setenv("CCA_VECTOR_STORE_PATH", str(tmp_path))
    monkeypatch.delenv("CCA_CHROMA_URL", raising=False)
    response = client.post(
        "/intellect/query",
        json={"query": "anything", "limit": 3, "config": "signatures"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["config"] == "signatures"
    assert body["hits"] == []
