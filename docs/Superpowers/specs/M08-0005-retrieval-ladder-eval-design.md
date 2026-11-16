# M08-0005…0007 (#187–#189) Advanced Intellect retrieval + EVALUATION

## Decisions (D93)

1. **Local-only ladder.** No paid LLM / cross-encoder APIs. Self-query and decompose are **heuristic stubs**; rerank is **lexical overlap** over hybrid candidates. Documented in tests.
2. **Configs (frozen names, 5.25-aligned):** `baseline` | `hybrid` | `self_query` | `decompose` | `reranker` | `everything`. Default remains `baseline` (D90 vector-only).
3. **Hybrid.** Pure-Python Okapi BM25 over JSONL texts + vector cosine ranks → **RRF** (`k=60`). Module `app/core/common/retrieval_ladder.py`; extends `vector_search` corpus load.
4. **API.** `POST /intellect/query` optional `config` (string). Response may include `config` echo. Portal can pass config; default unchanged.
5. **EVALUATION.** In-repo golden fixture + `evaluation_scorecard` (Hit@K, MRR) for every ladder config. Pytest runs harness. **Ship bias:** recommend `reranker` (hybrid + lexical rerank), not necessarily `everything`.
6. **Out of scope:** pgvector query path (still JSONL Intellect), paid LLM self-query, cloud eval SaaS (M90).
