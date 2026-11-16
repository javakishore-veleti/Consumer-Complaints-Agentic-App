# M09-0006…0011 (#200–#205) Extra local vector backends + pgvector consolidate

## Decisions (D94)

1. **Consolidate pgvector.** Ops Postgres image → `pgvector/pgvector:pg16`. `CCA_PGVECTOR_URL` targets that instance (e.g. `postgresql://postgres:postgres@127.0.0.1:5432/cca`). Retire `CICD/Local/pgvector`; npm `pgvector` profile aliases to `postgres`.
2. **Chroma = separate container.** `CICD/Local/chroma`, profile `chroma`, env `CCA_CHROMA_URL`. Backend `chroma` on `open_vector_store`. DAG `index_cfpb_chroma` + AppEndpoint `cfpb_index_mongo_to_chroma`.
3. **Redis Stack = separate container.** `CICD/Local/redis` (vector + cache), profile `redis`, env `CCA_REDIS_URL`. Backend `redis`. DAG `index_cfpb_redis` + AppEndpoint `cfpb_index_mongo_to_redis`.
4. **Distinct endpoints** — never share `to_env_var_name` across backends. JSONL endpoint unchanged.
5. **Injectable clients** for Chroma/Redis in unit tests (no paid APIs; containers opt-in).
6. **Out of scope:** Intellect query against Chroma/Redis (can stay JSONL/ladder); cloud SaaS (M90).
