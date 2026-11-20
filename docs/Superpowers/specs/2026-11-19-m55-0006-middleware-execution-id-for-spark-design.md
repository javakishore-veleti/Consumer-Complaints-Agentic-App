# M55-0006 Middleware execution_id → Spark

Admin→Middleware already creates `execution_id` and puts it in Airflow `dag_run.conf`.
`hydrate_raw` must pass that as `CCA_RAW_RUN_ID` (not Airflow `run_id`).
Sanitize stage path chars as a safety net for manual/engine fallbacks.
