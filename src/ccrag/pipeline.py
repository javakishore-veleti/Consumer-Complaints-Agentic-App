"""The advanced RAG pipeline. Every step is a function, every technique is a flag on `Config`.

    question -> [decompose] -> parts
      each part -> [self-query: plan a metadata filter] -> [rewrite] -> query -> [+ multi-query] [+ HyDE]
                -> search (vector | bm25 | hybrid) -> fuse -> [rerank] -> top k
      union of the parts' chunks -> LLM -> answer that cites its sources
"""
import re
from dataclasses import dataclass, replace
from functools import cache
from threading import Lock
from typing import Literal

from pydantic import BaseModel, Field

from . import llm
from .chunking import Chunk, build_chunks
from .config import REFUSAL
from .steps import current_trace, step
from .store import BM25Index, Catalog, Filter, as_filter, catalog_from_chunks, passes, vector_ids

# ---------------------------------------------------------------- the corpus, loaded once


@dataclass
class Corpus:
    chunks: list[Chunk]
    by_id: dict[str, Chunk]
    catalog: Catalog


@cache
def corpus() -> Corpus:
    chunks = build_chunks()
    return Corpus(chunks, {c.id: c for c in chunks}, catalog_from_chunks(chunks))


@cache
def bm25_index(filter: Filter) -> BM25Index:
    return BM25Index([c for c in corpus().chunks if passes(c, filter)])


# ---------------------------------------------------------------- search: vector, bm25, hybrid


@step("vector")
def vector_search(query, k, filter):
    return vector_ids(llm.embed([query])[0], k, as_filter(filter))


@step("bm25")
def bm25_search(query, k, filter):
    return bm25_index(as_filter(filter)).search(query, k)


def fuse(lists, k):
    """Reciprocal rank fusion: each list adds 1 / (60 + rank) to a chunk's score."""
    scores = {}
    for ids in lists:
        for rank, id in enumerate(ids, 1):
            scores[id] = scores.get(id, 0) + 1 / (60 + rank)
    return sorted(scores, key=scores.get, reverse=True)[:k]


def union(lists):
    return list(dict.fromkeys(id for ids in lists for id in ids))


def search(query, retriever, k, filter=None):
    filter = [list(p) for p in filter] if filter else None  # JSON-friendly for the memo key
    if retriever == "vector":
        return vector_search(query, k, filter)
    if retriever == "bm25":
        return bm25_search(query, k, filter)
    return fuse([vector_search(query, k, filter), bm25_search(query, k, filter)], k)


# ---------------------------------------------------------------- self-query: plan a filter


class SearchPlan(BaseModel):
    scope: Literal["complaints", "docs"] | None = Field(
        None, description="'docs' if the question asks what a database field or the database itself means; "
                          "'complaints' if it asks about individual complaint records; otherwise null.")
    product: str | None = Field(None, description="A product from the catalog, only if the question names one.")
    company: str | None = Field(None, description="A company from the catalog, only if the question names one.")
    state: str | None = Field(None, description="Two-letter US state code of the consumer, only if named.")
    year: int | None = Field(None, description="Year the complaint was received, only if the question gives one.")
    company_response: str | None = Field(None, description="A company response from the catalog, only if named.")
    submitted_via: str | None = Field(None, description="A submission channel from the catalog, only if named.")
    timely: bool | None = Field(None, description="True/false only if the question asks for timely/late responses.")
    older_american: bool | None = Field(None, description="True only if the question asks for Older American complaints.")
    servicemember: bool | None = Field(None, description="True only if the question asks for Servicemember complaints.")


def planner_prompt(catalog: Catalog) -> str:
    return (
        "You plan searches over a store of CFPB consumer complaint records and the database's field reference.\n"
        "Fill in a metadata filter for the user's question. Set a field ONLY when the question explicitly asks for "
        "it; otherwise leave it null. Never guess.\n\n"
        f"products: {catalog.products}\n"
        f"company responses: {catalog.responses}\n"
        f"submission channels: {catalog.channels}\n"
        f"years: {catalog.years}\n"
        f"companies (use the name exactly as listed): {catalog.top_companies()}")


def _match(value, options):
    """Case-insensitive exact match of `value` against `options`; returns the canonical option or None."""
    return next((o for o in options if o.lower() == str(value).strip().lower()), None)


def _resolve_company(name, companies):
    exact = _match(name, companies)
    if exact:
        return exact
    contained = [c for c in companies if str(name).strip().lower() in c.lower()]
    return contained[0] if len(contained) == 1 else None


def to_filter(plan: SearchPlan, catalog: Catalog) -> Filter:
    """Turn a plan into a filter, dropping any value the index does not hold (a wrong filter returns nothing)."""
    if plan.scope == "docs":
        return (("kind", "doc"),)
    f = {}
    if plan.scope == "complaints":
        f["kind"] = "complaint"
    if plan.product and (v := _match(plan.product, catalog.products)):
        f["product"] = v
    if plan.company and (v := _resolve_company(plan.company, catalog.companies)):
        f["company"] = v
    if plan.state and plan.state.upper() in catalog.states:
        f["state"] = plan.state.upper()
    if plan.year in catalog.years:
        f["year"] = plan.year
    if plan.company_response and (v := _match(plan.company_response, catalog.responses)):
        f["company_response"] = v
    if plan.submitted_via and (v := _match(plan.submitted_via, catalog.channels)):
        f["submitted_via"] = v
    for flag in ("timely", "older_american", "servicemember"):
        if getattr(plan, flag) is not None:
            f[flag] = getattr(plan, flag)
    return as_filter(f)


@step("plan")
def plan_filter(question):
    c = corpus().catalog
    plan = llm.parse(planner_prompt(c), question, SearchPlan)
    return [list(p) for p in to_filter(plan, c) or ()]


# ---------------------------------------------------------------- the LLM steps before search


def lines(text):
    return [re.sub(r"^\s*(?:\d+[.)]|[-•*])\s*", "", line).strip() for line in text.splitlines() if line.strip()]


@step("decompose")
def split(question):
    return lines(llm.chat("Split this question into separate standalone questions, one per line. If it asks only one "
                          "thing, return it unchanged. Reply with the questions only.", question)) or [question]


@step("rewrite")
def rewrite(question):
    return llm.chat("Rewrite this question as one short search query for a document search engine. "
                    "Reply with the query only.", question)


@step("multi_query")
def variants(question):
    return lines(llm.chat("Write 3 different versions of this question for a document search engine, one per line. "
                          "Reply with the questions only.", question))[:3]


@step("hyde")
def fake_answer(question):
    return llm.chat("Write a short passage, as it might appear in a CFPB complaint record or its field reference, "
                    "that answers this question. Reply with the passage only.", question)


# ---------------------------------------------------------------- rerank and answer


@cache
def cross_encoder(name):
    from sentence_transformers import CrossEncoder  # optional dependency: pip install -e ".[rerank]"
    return CrossEncoder(RERANKERS[name])


RERANKERS = {"bge": "BAAI/bge-reranker-v2-m3", "minilm": "cross-encoder/ms-marco-MiniLM-L6-v2"}


@step("rerank", lock=Lock())
def rerank(question, ids, model, k):
    by_id = corpus().by_id
    hits = cross_encoder(model).rank(question, [by_id[id].text for id in ids])
    return [ids[hit["corpus_id"]] for hit in hits[:k]]


ANSWER_SYSTEM = (
    "Answer the question using only the numbered sources. After each sentence, cite the sources it uses, like [1] or "
    "[2][3]. Refer to complaints by their complaint ID. The sources are structured complaint records and the "
    "database field reference; they do not contain what the consumer wrote, and they cannot be counted or totalled. "
    "If the sources do not contain the answer, reply exactly: " + REFUSAL)


@step("generate")
def generate(question, ids):
    by_id = corpus().by_id
    sources = "\n\n".join(f"[{i}] {by_id[id].text}" for i, id in enumerate(ids, 1))
    return llm.chat(ANSWER_SYSTEM, f"Sources:\n\n{sources}\n\nQuestion: {question}")


# ---------------------------------------------------------------- Config: one flag per technique


@dataclass(frozen=True)
class Config:
    name: str
    retriever: str = "vector"           # vector | bm25 | hybrid
    self_query: bool = False            # plan a metadata filter per part
    query_steps: tuple[str, ...] = ()   # any of: decompose, rewrite, multi_query, hyde
    rerank: str | None = None           # None | bge | minilm
    rerank_depth: int = 20              # candidates the reranker reads
    k: int = 4                          # chunks per part sent to the LLM


BASELINE = Config("baseline")
HYBRID = replace(BASELINE, name="+hybrid", retriever="hybrid")
SELF_QUERY = replace(HYBRID, name="+self-query", self_query=True)
DECOMPOSE = replace(SELF_QUERY, name="+decomposition", query_steps=("decompose",))
RERANK = replace(DECOMPOSE, name="+reranker", rerank="bge")
EVERYTHING = replace(RERANK, name="everything", query_steps=("decompose", "rewrite", "multi_query", "hyde"))
LADDER = [BASELINE, HYBRID, SELF_QUERY, DECOMPOSE, RERANK, EVERYTHING]
CONFIGS = {c.name: c for c in LADDER}


def retrieve(question, config):
    parts = split(question) if "decompose" in config.query_steps else [question]
    found = []
    for part in parts:
        filter = as_filter(plan_filter(part)) if config.self_query else None
        query = rewrite(part) if "rewrite" in config.query_steps else part
        queries = [query]
        if "multi_query" in config.query_steps:
            queries += variants(query)
        if "hyde" in config.query_steps:
            queries.append(fake_answer(query))
        depth = config.rerank_depth if config.rerank else config.k
        candidates = fuse([search(q, config.retriever, depth, filter) for q in queries], depth)
        found.append(rerank(part, candidates, config.rerank, config.k) if config.rerank else candidates[:config.k])
    return union(found)


def ask(question, config):
    """Returns the answer, the chunk ids sent to the LLM, and the trace (step, seconds, tokens)."""
    trace = []
    token = current_trace.set(trace)
    try:
        ids = retrieve(question, config)
        answer = generate(question, ids)
    finally:
        current_trace.reset(token)
    return {"answer": answer, "ids": ids, "trace": trace}
