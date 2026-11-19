# M45-0003 / #322 — Airflow Raw Iceberg DAG design

## Goal
DAG `hydrate_raw_iceberg_3m`: sense Lift 3m zips → pre-ingest gate → invoke Spark hydrate in `cca-spark-iceberg` → DQ count + mandatory-key null checks → cleanup staging.

## Invoke path
Local Airflow workers call Docker API (`unix:///var/run/docker.sock`) to `exec` the existing `run_hydrate_raw_3m.sh` / spark-sql verify inside `cca-spark-iceberg`. No second Spark runtime. Compose mounts the socket; image adds `docker` Python SDK.

## Tasks
1. `sense_lift_3m` — latest `imports/*/dataset/*3_months*.csv.zip` must exist (no download).
2. `pre_ingest_gate` — ≥1 zip with payload; header map matches 15 CFPB columns.
3. `hydrate_raw` — docker-exec hydrate (run_id = Airflow run_id).
4. `dq_checks` — COUNT(*) > 0; null rate 0 on mandatory keys via spark-sql.
5. `cleanup_stage` — rm `/tmp/cca_raw_stage/<run_id>` in spark container (always).
