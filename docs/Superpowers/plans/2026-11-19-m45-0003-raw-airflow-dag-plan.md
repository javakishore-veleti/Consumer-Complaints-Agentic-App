# M45-0003 / #322 — Implementation plan

1. Add `ccaa/raw_iceberg.py` helpers + unit tests (no Docker).
2. Add DAG `hydrate_raw_iceberg_3m.py`.
3. Mount docker.sock in local Airflow compose; pip install `docker` in Dockerfile.
4. Document DAG in Iceberg README + 3m runbook pointer.
5. Parse-check DAG; commit-push; PR/merge; story-complete.
