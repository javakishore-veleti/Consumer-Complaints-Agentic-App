"""Index local Mongo complaints into local pgvector (D67 / D92)."""

from __future__ import annotations

import os
from datetime import datetime

from airflow import DAG
from airflow.models import Variable
from airflow.operators.python import PythonOperator
from airflow.utils.trigger_rule import TriggerRule

from ccaa.db_reader import load_execution_config, make_engine, resolve_app_endpoint
from ccaa.mongo_ingest import resolve_complaints_mongo_url
from ccaa.status_callback import report_execution_status
from ccaa.vector_index import (
    BACKEND_PGVECTOR,
    index_complaint_docs,
    iter_mongo_complaints,
    open_vector_store,
    resolve_pgvector_url,
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

    db_url = Variable.get("CCA_DB_URL")
    engine = make_engine(db_url)
    with engine.connect() as conn:
        cfg = load_execution_config(conn, execution_id)
        ep_name = (cfg.get("app_endpoint_name") or "").strip()
        if ep_name:
            resolved = resolve_app_endpoint(
                conn,
                ep_name,
                getenv=os.getenv,
                get_variable=Variable.get,
            )
            frm = resolved["from"]
            to = resolved["to"]
            if frm.get("kind") != "env" or not frm.get("value"):
                raise ValueError(f"app_endpoint {ep_name} from must be Mongo env URI")
            if to.get("kind") != "env" or not to.get("value"):
                raise ValueError(f"app_endpoint {ep_name} to must be CCA_PGVECTOR_URL env")
            mongo_url = frm["value"]
            pg_url = to["value"]
        else:
            mongo_url = resolve_complaints_mongo_url(
                getenv=os.getenv,
                get_variable=Variable.get,
            )
            pg_url = resolve_pgvector_url(
                getenv=os.getenv,
                get_variable=Variable.get,
            )

    batch_size = int(cfg.get("batch_size") or 500)
    store = open_vector_store(backend=BACKEND_PGVECTOR, dsn=pg_url)
    result = index_complaint_docs(
        iter_mongo_complaints(mongo_url),
        store,
        batch_size=batch_size,
    )
    return {
        "rows_loaded": result.rows_loaded,
        "batch_count": result.batch_count,
        "backend": BACKEND_PGVECTOR,
    }


def notify_finished(**context) -> None:
    execution_id = _execution_id(context)
    dag_run = context["dag_run"]
    upstream = dag_run.get_task_instance("resolve_and_index")
    ok = upstream is not None and str(upstream.state) == "success"
    ti = context.get("ti")
    volume = {}
    if ti is not None:
        pulled = ti.xcom_pull(task_ids="resolve_and_index") or {}
        if isinstance(pulled, dict):
            if "rows_loaded" in pulled:
                volume["rows_loaded"] = int(pulled["rows_loaded"])
            if "batch_count" in pulled:
                volume["batch_count"] = int(pulled["batch_count"])
    if ok:
        report_execution_status(
            execution_id,
            "completed",
            engine_run_id=_engine_run_id(context),
            **volume,
        )
        return
    state = getattr(upstream, "state", None) if upstream else None
    report_execution_status(
        execution_id,
        "failed",
        engine_run_id=_engine_run_id(context),
        message=f"resolve_and_index did not succeed (state={state})",
    )


with DAG(
    dag_id="index_cfpb_pgvector",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    tags=["ccaa", "cfpb", "index", "pgvector"],
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
