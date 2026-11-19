# M51-0003..0005 — taxonomy / curated / chroma Admin workflows

Same loop as Downloads: Admin Lakehouse → Middleware → Airflow DAG → callbacks.

- `hydrate_taxonomy_mode2_3m` — spark-submit taxonomy Mode 2
- `hydrate_curated_iceberg_3m` — spark-submit curated
- `hydrate_chroma_signatures_3m` — export signatures + Chroma upsert from Airflow worker
