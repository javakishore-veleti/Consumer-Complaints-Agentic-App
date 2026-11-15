"""Download the full CFPB complaints zip (All dataset). D51 / D63 / D67."""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

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
from ccaa.download import download_url_to_path
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


def resolve_and_download(**context) -> str:
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

    url = locs["http"]["path"]
    landing = resolve_landing_dir(
        locs["local"]["local_env_var_name"],
        getenv=os.getenv,
        get_variable=Variable.get,
    )
    name = Path(urlparse(url).path).name or "complaints.csv.zip"
    dest = landing / name
    download_url_to_path(url, dest)
    return str(dest)


def notify_finished(**context) -> None:
    execution_id = _execution_id(context)
    dag_run = context["dag_run"]
    upstream = dag_run.get_task_instance("resolve_and_download")
    ok = upstream is not None and str(upstream.state) == "success"
    if ok:
        report_execution_status(
            execution_id,
            "completed",
            engine_run_id=_engine_run_id(context),
        )
        return
    state = getattr(upstream, "state", None) if upstream else None
    report_execution_status(
        execution_id,
        "failed",
        engine_run_id=_engine_run_id(context),
        message=f"resolve_and_download did not succeed (state={state})",
    )


with DAG(
    dag_id="download_cfpb_all",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    tags=["ccaa", "cfpb", "download"],
) as dag:
    download = PythonOperator(
        task_id="resolve_and_download",
        python_callable=resolve_and_download,
    )
    finalize = PythonOperator(
        task_id="notify_finished",
        python_callable=notify_finished,
        trigger_rule=TriggerRule.ALL_DONE,
    )
    download >> finalize
