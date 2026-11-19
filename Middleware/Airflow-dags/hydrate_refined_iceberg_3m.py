"""Airflow DAG: refined Iceberg 3m hydrate (M51-0002 / #342).

Admin → Middleware → this DAG → callbacks. Invokes Spark hydrate_refined_3m.py
inside ``cca-spark-iceberg``.
"""

from __future__ import annotations

import logging
from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.trigger_rule import TriggerRule

from ccaa.lakehouse_spark import count_table, engine_run_id, execution_id, spark_submit_script
from ccaa.status_callback import notify_execution_finished, report_execution_status

log = logging.getLogger(__name__)
TARGET = "demo.refined.cfpb_complaints_3m"


def mark_started(**context) -> None:
    eid = execution_id(context)
    if eid:
        report_execution_status(eid, "started", engine_run_id=engine_run_id(context))


def hydrate_refined(**context) -> dict:
    run_id = engine_run_id(context)
    spark_submit_script(script_name="hydrate_refined_3m.py", run_id=run_id)
    return {"run_id": run_id, "table": TARGET}


def dq_count(**context) -> dict:
    total = count_table(TARGET)
    if total <= 0:
        raise RuntimeError(f"{TARGET} COUNT(*)={total} — expected > 0")
    return {"total": total}


def notify_finished(**context) -> None:
    notify_execution_finished(context, "dq_count")


with DAG(
    dag_id="hydrate_refined_iceberg_3m",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    tags=["cca", "refined", "iceberg", "3m", "lakehouse"],
    doc_md=__doc__,
) as dag:
    start = PythonOperator(task_id="mark_started", python_callable=mark_started)
    hydrate = PythonOperator(task_id="hydrate_refined", python_callable=hydrate_refined)
    dq = PythonOperator(task_id="dq_count", python_callable=dq_count)
    finalize = PythonOperator(
        task_id="notify_finished",
        python_callable=notify_finished,
        trigger_rule=TriggerRule.ALL_DONE,
    )
    start >> hydrate >> dq >> finalize
