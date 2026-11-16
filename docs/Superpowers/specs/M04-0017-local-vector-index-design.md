# M04-0017 / M04-0018 (#163 / #164) Local vector index

Decision **D88**. Next free: **D89**.

## D88

1. Local vector store = filesystem directory `CCA_VECTOR_STORE_PATH` (upsert-listed). MVP store is JSONL files under that path (no paid cloud; no required Chroma/pgvector container for unit tests). Deterministic hash embeddings for CI; swap later for real model.
2. DAG `index_cfpb_all`: read complaint Mongo → upsert into vector store; callbacks with volume.
3. Seed workflow + All MIO bind + AppEndpoint `cfpb_index_mongo_to_vectors` (from `CCA_MONGO_COMPLAINTS_URL` → `CCA_VECTOR_STORE_PATH`).
4. Admin **Index** page (mirrors DB Ingest) for `index_*` workflows.

## Out of scope

Intellect query UI (M05 #166), paid vector SaaS.
