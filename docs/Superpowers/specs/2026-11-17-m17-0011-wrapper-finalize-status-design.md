# M17-0011 — Wrapper finalize false-failed (state=None)

## Problem

Airflow 3 worker context often cannot load upstream TI state (`state=None`) and may miss XCom for `run_children`. `notify_execution_finished` then reports **failed** even when the DAG succeeded, overwriting Admin after a good Mongo ingest.

## Design

1. Extend `upstream_succeeded` with an ORM/`TaskInstance` session lookup when TI-in-context and XCom are inconclusive.
2. Harden `_xcom_indicates_success` (string and list `task_ids`, explicit `return_value` key).
3. Keep failed reporting when ORM state is failed/absent and no XCom.
4. Tests: success via ORM when context TI/XCom empty; still fail when ORM says failed.
