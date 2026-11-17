# M10-0014 (#221) Local Airflow DAGs unpaused by default

## Decision
1. `AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION=false` in local `docker-compose.yaml`.
2. Matching `dags_are_paused_at_creation = False` in local `airflow.cfg`.
3. Runbook §0.5 becomes “confirm enabled”; existing paused metadata needs one-time unpause or Airflow recreate.
