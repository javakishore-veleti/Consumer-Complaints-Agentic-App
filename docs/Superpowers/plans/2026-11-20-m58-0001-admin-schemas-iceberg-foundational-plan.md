# M58-0001 Implementation Plan

**Story:** #400

## Tasks

1. Mount Iceberg `./sql` in compose; add foundational in-container + host DDL scripts.
2. Airflow DAG `apply_iceberg_foundational_schema` with status callbacks.
3. Alembic 0033 + Mongo bootstrap seed + MIO bind; update SEEDED workflow lists in tests.
4. Admin Schemas page + sidebar + route + unit test (mirror Lakehouse, filter `apply_`).
5. Runbook: drop operator iceberg npm DDL/hydrate; document Schemas → Lakehouse.
6. Lint, pytest, Admin build; commit/push; PR; merge.
