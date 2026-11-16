"""EVALUATION scorecard for Intellect retrieval ladder configs (D93)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.core.common.retrieval_ladder import LADDER_CONFIGS, RetrievalReq, retrieve
from app.core.common.vector_search import HashEmbeddingReq, hash_embedding

# Ship bias from 5.25 / M08 notes — prefer +reranker over everything.
SHIP_RECOMMENDATION = "reranker"


@dataclass
class GoldenQuery:
    query: str
    relevant_ids: list[str]


@dataclass
class ScorecardRow:
    config: str
    hit_at_1: float
    hit_at_5: float
    mrr: float
    queries: int


@dataclass
class HitAtKReq:
    ranked_ids: list[str]
    relevant_ids: list[str]
    k: int


@dataclass
class ReciprocalRankReq:
    ranked_ids: list[str]
    relevant_ids: list[str]


@dataclass
class LoadGoldenReq:
    path: Path


@dataclass
class CorpusFromDocsReq:
    docs: list[dict[str, Any]]


@dataclass
class EvaluateConfigReq:
    corpus: list[dict[str, Any]]
    queries: list[GoldenQuery]
    config: str
    limit: int = 5


@dataclass
class RunScorecardReq:
    golden_path: Path
    configs: tuple[str, ...] = LADDER_CONFIGS
    limit: int = 5


@dataclass
class ScorecardAsDictsReq:
    rows: list[ScorecardRow]


def hit_at_k(req: HitAtKReq) -> float:
    if req.k < 1 or not req.relevant_ids:
        return 0.0
    top = set(req.ranked_ids[: req.k])
    return 1.0 if top.intersection(req.relevant_ids) else 0.0


def reciprocal_rank(req: ReciprocalRankReq) -> float:
    relevant = set(req.relevant_ids)
    for i, doc_id in enumerate(req.ranked_ids, start=1):
        if doc_id in relevant:
            return 1.0 / i
    return 0.0


def load_golden(req: LoadGoldenReq) -> tuple[list[dict[str, Any]], list[GoldenQuery]]:
    data = json.loads(req.path.read_text(encoding="utf-8"))
    docs = list(data.get("docs") or [])
    queries = [
        GoldenQuery(query=str(q["query"]), relevant_ids=[str(x) for x in (q.get("relevant_ids") or [])])
        for q in (data.get("queries") or [])
    ]
    return docs, queries


def corpus_from_docs(req: CorpusFromDocsReq) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for d in req.docs:
        text = str(d.get("text") or "")
        out.append(
            {
                "id": str(d.get("id") or ""),
                "text": text,
                "embedding": d.get("embedding") or hash_embedding(HashEmbeddingReq(text=text)),
            }
        )
    return out


def evaluate_config(req: EvaluateConfigReq) -> ScorecardRow:
    if not req.queries:
        return ScorecardRow(config=req.config, hit_at_1=0.0, hit_at_5=0.0, mrr=0.0, queries=0)
    h1 = h5 = mrr = 0.0
    for gq in req.queries:
        hits = retrieve(
            RetrievalReq(query=gq.query, corpus=req.corpus, limit=req.limit, config=req.config)
        )
        ranked = [h["id"] for h in hits]
        h1 += hit_at_k(HitAtKReq(ranked_ids=ranked, relevant_ids=gq.relevant_ids, k=1))
        h5 += hit_at_k(HitAtKReq(ranked_ids=ranked, relevant_ids=gq.relevant_ids, k=5))
        mrr += reciprocal_rank(ReciprocalRankReq(ranked_ids=ranked, relevant_ids=gq.relevant_ids))
    n = float(len(req.queries))
    return ScorecardRow(
        config=req.config,
        hit_at_1=h1 / n,
        hit_at_5=h5 / n,
        mrr=mrr / n,
        queries=len(req.queries),
    )


def run_scorecard(req: RunScorecardReq) -> list[ScorecardRow]:
    docs, queries = load_golden(LoadGoldenReq(path=req.golden_path))
    corpus = corpus_from_docs(CorpusFromDocsReq(docs=docs))
    return [
        evaluate_config(
            EvaluateConfigReq(corpus=corpus, queries=queries, config=cfg, limit=req.limit)
        )
        for cfg in req.configs
    ]


def scorecard_as_dicts(req: ScorecardAsDictsReq) -> list[dict[str, Any]]:
    return [
        {
            "config": r.config,
            "hit_at_1": r.hit_at_1,
            "hit_at_5": r.hit_at_5,
            "mrr": r.mrr,
            "queries": r.queries,
        }
        for r in req.rows
    ]
