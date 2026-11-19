# M51-0002 / #342 — hydrate_refined_iceberg_3m Admin workflow

## Goal
Airflow DAG + seed/bind so Admin Lakehouse can start refined hydrate (same callback loop as Downloads).

## Approach
- DAG wraps `spark-submit hydrate_refined_3m.py` via docker sock into `cca-spark-iceberg`.
- COUNT(*) DQ on `demo.refined.cfpb_complaints_3m`.
- Alembic 0027 + Mongo ensure seed/bind to 3m MIO.
