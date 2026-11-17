"""Index local Mongo complaints into local chroma (D94)."""

from __future__ import annotations

import os
from datetime import datetime

from airflow import DAG
from airflow.models import Variable
from airflow.operators.python import PythonOperator
from airflow.utils.trigger_rule import TriggerRule

from ccaa.dag_context import fetch_dag_context, materialize_app_endpoint
from ccaa.mongo_ingest import resolve_complaints_mongo_url
from ccaa.status_callback import notify_execution_finished, report_execution_status
from ccaa.vector_index import (
    BACKEND_CHROMA,
    index_complaint_docs,
    iter_mongo_complaints,
    open_vector_store,
    resolve_chroma_url,
)


def _execution_id(context) -> str:
    conf = (context.get("dag_run").conf or {}) if context.get("dag_run") else {}
    execution_id = conf.get("execution_id")
    if not execution_id:
        raise ValueError("dag_run.conf.execution_id is required")
    return str(execution_id)


def _engine_run_id(context) -> str | None:
    run_id = context.get("run_id")
    return str(run_id)[:128] if run_id else None


def resolve_and_index(**context) -> dict:
    execution_id = _execution_id(context)
    report_execution_status(
        execution_id,
        "started",
        engine_run_id=_engine_run_id(context),
    )

    ctx = fetch_dag_context(execution_id)
    cfg = ctx.get("config_used") or {}
    ep_name = (cfg.get("app_endpoint_name") or "").strip()
    if ep_name:
        raw_ep = ctx.get("app_endpoint")
        if not raw_ep:
            raw_ep = fetch_dag_context(execution_id, app_endpoint=ep_name).get("app_endpoint")
        if not raw_ep:
            raise ValueError(f"app_endpoint not found: {ep_name}")
        resolved = materialize_app_endpoint(
            raw_ep, getenv=os.getenv, get_variable=Variable.get
        )
        frm = resolved["from"]
        to = resolved["to"]
            if frm.get("kind") != "env" or not frm.get("value"):
                raise ValueError(f"app_endpoint {ep_name} from must be Mongo env URI")
            if to.get("kind") != "env" or not to.get("value"):
                raise ValueError(f"app_endpoint {ep_name} to must be CCA_CHROMA_URL env")
            mongo_url = frm["value"]
            target_url = to["value"]
        else:
            mongo_url = resolve_complaints_mongo_url(
                getenv=os.getenv,
                get_variable=Variable.get,
            )
            target_url = resolve_chroma_url(
                getenv=os.getenv,
                get_variable=Variable.get,
            )

    batch_size = int(cfg.get("batch_size") or 500)
    store = open_vector_store(backend=BACKEND_CHROMA, dsn=target_url)
    result = index_complaint_docs(
        iter_mongo_complaints(mongo_url),
        store,
        batch_size=batch_size,
    )
    return {
        "rows_loaded": result.rows_loaded,
        "batch_count": result.batch_count,
        "backend": BACKEND_CHROMA,
    }


def notify_finished(**context) -> None:
    ti = context.get("ti")
    volume: dict = {}
    if ti is not None:
        pulled = ti.xcom_pull(task_ids="resolve_and_index") or {}
        if isinstance(pulled, dict):
            if "rows_loaded" in pulled:
                volume["rows_loaded"] = int(pulled["rows_loaded"])
            if "batch_count" in pulled:
                volume["batch_count"] = int(pulled["batch_count"])
    notify_execution_finished(
        context,
        "resolve_and_index",
        completed_kwargs=volume or None,
    )


with DAG(
    dag_id="index_cfpb_chroma",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    tags=["ccaa", "cfpb", "index", "chroma"],
) as dag:
    index = PythonOperator(
        task_id="resolve_and_index",
        python_callable=resolve_and_index,
    )
    finalize = PythonOperator(
        task_id="notify_finished",
        python_callable=notify_finished,
        trigger_rule=TriggerRule.ALL_DONE,
    )
    index >> finalize
