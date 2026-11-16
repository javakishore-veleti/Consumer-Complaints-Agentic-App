# M05-0005 (#166) Intellect MVP query local indexed complaints

Decision **D90**. Next free: **D91**.

## D90

1. Intellect uses **local** vector JSONL (`CCA_VECTOR_STORE_PATH`, D88) — not a paid LLM/cloud vector DB. Same hash embeddings for ranking (cosine).
2. API `POST /intellect/query` body `{ "query": string, "limit"?: int }` → top-k hits `{ id, text, score }`. No callback secret (portal). Open Q4: Intellect does **not** share admin schema for query; vectors are filesystem-only.
3. Portal `Portals/consumer-complaints-intellect` (Vite SPA on :4201): query box + results. Not Admin Imports.
4. npm scripts + `portals-all` status/start/stop include Intellect.

## Out of scope

Agentic RAG with LLM, PySpark index rewrite, cloud.
