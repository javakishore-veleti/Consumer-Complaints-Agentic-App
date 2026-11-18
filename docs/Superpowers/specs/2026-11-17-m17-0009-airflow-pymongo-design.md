# M17-0009 — Airflow image pymongo

Bake `pymongo` into `CICD/Local/airflow/Dockerfile` and build that image from compose (D51). Document rebuild + verify via `import pymongo` in the scheduler container / re-run ingest past `resolve_and_ingest`.
