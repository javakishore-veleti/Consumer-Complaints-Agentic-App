# M12-0001 (#239) — Finalize status callback on Airflow 3

## Problem

`notify_finished` calls `dag_run.get_task_instance(task_id)`, which does not exist on Airflow 3. Finalize crashes; Middleware never receives `failed`/`completed`; Admin stays on `started`.

## Design

1. Add `ccaa.status_callback.upstream_succeeded(context, task_id) -> bool` that reads the upstream TI via Airflow 3–safe APIs (`context["ti"].get_dagrun()` / task instance map / `DagRun.get_task_instances()` fallback), never `dag_run.get_task_instance`.
2. Add `ccaa.status_callback.notify_execution_finished(context, work_task_id, *, message_prefix=...)` that:
   - always calls `report_execution_status` with `completed` or `failed`
   - never raises after determining status (wrap report errors only if unavoidable; prefer report failed then re-raise only for true callback transport bugs — primary goal is Middleware gets a terminal status)
3. Replace every DAG’s `notify_finished` body to use the shared helper.
4. Keep `TriggerRule.ALL_DONE` on finalize tasks.

## DAGs in scope

`download_cfpb_all`, `filter_cfpb_3_months`, `ingest_cfpb_all`, `ingest_cfpb_imports_wrapper`, `index_cfpb_all`, `index_cfpb_pgvector`, `index_cfpb_chroma`, `index_cfpb_redis`.
