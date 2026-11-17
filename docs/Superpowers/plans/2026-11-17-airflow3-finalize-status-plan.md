# M12-0001 (#239) Plan

1. [x] Tests for `task_instance_for` / `notify_execution_finished` (Airflow 3: no `get_task_instance`)
2. [x] Implement helpers in `ccaa/status_callback.py`
3. [x] Wire all CCAA DAGs' `notify_finished` to the helper
4. [x] Lint + full tests; commit/push; merge main; close #239 + M12
