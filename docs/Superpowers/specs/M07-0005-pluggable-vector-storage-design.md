# M07-0005…0008 (#179–#182) Pluggable local vector Storage Layer

## Decisions (D92)

1. **Adapter seam.** `SupportsVectorUpsert` + `open_vector_store(backend=...)` — backends `jsonl` (CI/default) and `pgvector` (local real store). Plain Python; PySpark-ready later.
2. **JSONL retained.** Existing `index_cfpb_all` + `cfpb_index_mongo_to_vectors` → `CCA_VECTOR_STORE_PATH` unchanged for CI/Intellect MVP.
3. **pgvector.** Env/Variable **`CCA_PGVECTOR_URL`** (upsert-listed). Local compose under `CICD/Local/pgvector` (image `pgvector/pgvector:pg16`), npm profile `pgvector`. Helper `PgvectorStore` creates extension + table `complaint_vectors` (id, text, embedding vector(DIM)).
4. **Index DAG.** New `index_cfpb_pgvector` (same callback pattern) Mongo SoT → pgvector via AppEndpoint `cfpb_index_mongo_to_pgvector`.
5. **Seeds.** Alembic `0018` + Mongo: workflow, All MIO bind, index AppEndpoint. Admin Index shows both `index_*` workflows.
6. **Out of scope:** Chroma/Milvus adapters (follow-on), retrieval ladder (M08), cloud vector SaaS (M90), Intellect query against pgvector (can stay JSONL until M08).
