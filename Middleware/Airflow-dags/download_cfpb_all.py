"""Download the full CFPB complaints zip (All dataset). D51 / D63. Status callbacks: story #59."""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.models import Variable

from ccaa.db_reader import (
    load_dataset_locations,
    load_execution_config,
    make_engine,
    resolve_landing_dir,
)
from ccaa.download import download_url_to_path


def _notify_started(execution_id: str) -> None:
    # TODO story #59: POST /callbacks/workflow-executions/{execution_id}/status status=started
    return None


def _notify_finished(execution_id: str, ok: bool) -> None:
    # TODO story #59: POST ... status=completed|failed
    return None


def resolve_and_download(**context) -> str:
    conf = context.get("dag_run").conf or {}
    execution_id = conf.get("execution_id")
    if not execution_id:
        raise ValueError("dag_run.conf.execution_id is required")

    _notify_started(execution_id)
    try:
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
        _notify_finished(execution_id, True)
        return str(dest)
    except Exception:
        _notify_finished(execution_id, False)
        raise


with DAG(
    dag_id="download_cfpb_all",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    tags=["ccaa", "cfpb", "download"],
) as dag:
    PythonOperator(
        task_id="resolve_and_download",
        python_callable=resolve_and_download,
    )
