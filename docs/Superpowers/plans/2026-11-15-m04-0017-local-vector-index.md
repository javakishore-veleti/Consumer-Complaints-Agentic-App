# M04-0017 / M04-0018 (#163 / #164) Local vector index — plan

**Goal:** Local JSONL vector store + `index_cfpb_all` DAG (D88), seed workflow/MIO/AppEndpoint, Admin Index page.

## Tasks

1. Spec D88 (filesystem JSONL + hash embeddings; `CCA_VECTOR_STORE_PATH`).
2. `ccaa/vector_index.py` + unit tests; DAG `index_cfpb_all.py` + file smoke test.
3. Alembic `0015` + Mongo bootstrap parity; upsert list + `.env.example`.
4. Admin Index page (`index_*` filter); nav + routes; exclude from Imports already done.
5. DESIGN.md D88; PRODUCT_FEATURES F8; close open Q3.
6. Lint/tests; commit/push; PR; merge; close #163/#164/#149/#144.
