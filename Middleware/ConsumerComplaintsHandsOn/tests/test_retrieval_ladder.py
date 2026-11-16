"""D93: BM25 + RRF hybrid and ladder configs (local stubs, no paid APIs)."""

import pytest

from app.core.common.retrieval_ladder import (
    CONFIG_EVERYTHING,
    CONFIG_HYBRID,
    CONFIG_RERANKER,
    CONFIG_SELF_QUERY,
    Bm25ScoresReq,
    DecomposeQueryReq,
    NormalizeConfigReq,
    RetrievalReq,
    RrfFuseReq,
    SelfQueryFilterReq,
    TokenizeReq,
    bm25_scores,
    decompose_query,
    normalize_config,
    retrieve,
    rrf_fuse,
    self_query_filter,
    tokenize,
)
from app.core.common.vector_search import HashEmbeddingReq, hash_embedding


def _corpus():
    texts = {
        "a": "Credit card billing overcharge dispute",
        "b": "Mortgage escrow delay servicing",
        "c": "Student loan debt collection",
    }
    return [
        {"id": k, "text": v, "embedding": hash_embedding(HashEmbeddingReq(text=v))}
        for k, v in texts.items()
    ]


def test_tokenize_and_bm25_ranks_relevant_doc():
    docs = [
        tokenize(TokenizeReq(text="credit card billing")),
        tokenize(TokenizeReq(text="mortgage escrow")),
        tokenize(TokenizeReq(text="student loan")),
    ]
    scores = bm25_scores(
        Bm25ScoresReq(query_tokens=tokenize(TokenizeReq(text="credit billing")), docs_tokens=docs)
    )
    assert scores[0] > scores[1]
    assert scores[0] > scores[2]


def test_rrf_fuse_prefers_shared_top_ranks():
    fused = rrf_fuse(RrfFuseReq(rank_lists=[["a", "b", "c"], ["a", "c", "b"]]))
    assert fused[0][0] == "a"


def test_hybrid_prefers_lexical_match_over_hash_noise():
    """Hash embeddings are non-semantic; hybrid BM25+RRF should surface the billing doc."""
    corpus = _corpus()
    hybrid = retrieve(
        RetrievalReq(query="billing overcharge credit", corpus=corpus, limit=2, config=CONFIG_HYBRID)
    )
    assert hybrid and hybrid[0]["id"] == "a"


def test_self_query_stub_filters_without_llm():
    corpus = _corpus()
    filtered = self_query_filter(SelfQueryFilterReq(query="billing credit", corpus=corpus))
    ids = {r["id"] for r in filtered}
    assert "a" in ids


def test_decompose_stub_splits_and_clause():
    assert decompose_query(DecomposeQueryReq(query="billing and mortgage")) == ["billing", "mortgage"]


def test_reranker_and_everything_run_locally():
    corpus = _corpus()
    for cfg in (CONFIG_RERANKER, CONFIG_EVERYTHING, CONFIG_SELF_QUERY):
        hits = retrieve(RetrievalReq(query="credit card billing", corpus=corpus, limit=2, config=cfg))
        assert hits
        assert hits[0]["id"]


def test_unknown_config_raises():
    with pytest.raises(ValueError, match="unknown retrieval config"):
        normalize_config(NormalizeConfigReq(value="chroma"))
