"""Ingest landed CFPB complaints zip into local Mongo. D20 / D67 / D86."""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

from airflow import DAG
from airflow.models import Variable
from airflow.operators.python import PythonOperator
from airflow.utils.trigger_rule import TriggerRule

from ccaa.db_reader import (
    load_dataset_locations,
    load_execution_config,
    make_engine,
    resolve_landing_dir,
)
from ccaa.mongo_ingest import (
    DEFAULT_BATCH_SIZE,
    ingest_complaints_zip,
    open_complaints_collection,
    resolve_complaints_mongo_url,
)
from ccaa.status_callback import report_execution_status


def _execution_id(context) -> str:
    conf = (context.get("dag_run").conf or {}) if context.get("dag_run") else {}
    execution_id = conf.get("execution_id")
    if not execution_id:
        raise ValueError("dag_run.conf.execution_id is required")
    return str(execution_id)


def _engine_run_id(context) -> str | None:
    run_id = context.get("run_id")
    return str(run_id)[:128] if run_id else None


def resolve_and_ingest(**context) -> dict:
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
        code = cfg.get("dataset_code")
        if not code:
            raise ValueError("config_used.dataset_code is required")
        locs = load_dataset_locations(conn, code)

    landing = resolve_landing_dir(
        locs["local"]["local_env_var_name"],
        getenv=os.getenv,
        get_variable=Variable.get,
    )
    filename = str(cfg.get("source_filename") or "complaints.csv.zip")
    source = landing / filename
    batch_size = int(cfg.get("batch_size") or DEFAULT_BATCH_SIZE)

    mongo_url = resolve_complaints_mongo_url(
        getenv=os.getenv,
        get_variable=Variable.get,
    )
    coll = open_complaints_collection(mongo_url)
    result = ingest_complaints_zip(source, coll, batch_size=batch_size)
    # Stash for notify_finished via XCom
    return {
        "rows_loaded": result.rows_loaded,
        "batch_count": result.batch_count,
        "source": str(source),
    }


def notify_finished(**context) -> None:
    execution_id = _execution_id(context)
    dag_run = context["dag_run"]
    upstream = dag_run.get_task_instance("resolve_and_ingest")
    ok = upstream is not None and str(upstream.state) == "success"
    ti = context.get("ti")
    volume = {}
    if ti is not None:
        pulled = ti.xcom_pull(task_ids="resolve_and_ingest") or {}
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
        message=f"resolve_and_ingest did not succeed (state={state})",
    )


with DAG(
    dag_id="ingest_cfpb_all",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    tags=["ccaa", "cfpb", "ingest"],
) as dag:
    ingest = PythonOperator(
        task_id="resolve_and_ingest",
        python_callable=resolve_and_ingest,
    )
    finalize = PythonOperator(
        task_id="notify_finished",
        python_callable=notify_finished,
        trigger_rule=TriggerRule.ALL_DONE,
    )
    ingest >> finalize
