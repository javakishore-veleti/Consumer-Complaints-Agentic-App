# M17-0011 plan

1. Red tests for ORM fallback + xcom list task_ids.
2. Implement `_ti_state_from_orm` and wire into `upstream_succeeded`.
3. Harden `_xcom_indicates_success`.
4. Run `test_ccaa_status_callback.py`; commit/push/PR.
