# M51-0001 / #341 — Admin Lakehouse + hydrate_raw_iceberg_3m

## Goal
Same control loop as Downloads: Admin → Middleware start → Airflow DAG → callback status.

## Scope
1. Seed `hydrate_raw_iceberg_3m` in `app_workflows` + bind to 3m MIO (Alembic 0026 + Mongo ensure).
2. Admin **Lakehouse** page listing `hydrate_*` workflows; Start/Refresh.
3. Reuse existing DAG `hydrate_raw_iceberg_3m` (already reports started/completed/failed).

## Out of scope
Refined/Taxonomy/Curated/Chroma Admin workflows (M51-0002+); changing Mio status API shape.
