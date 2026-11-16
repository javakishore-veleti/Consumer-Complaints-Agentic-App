"""Download or stage CFPB complaints into local landing. D51 / D63 / D67 / D91."""

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
    resolve_app_endpoint,
    resolve_landing_dir,
)
from ccaa.download import download_url_to_path
from ccaa.split_parts import (
    DEFAULT_PART_GLOB,
    DEFAULT_STAGE_FROM_ENV,
    resolve_named_dir,
    stage_parts_from_dir,
    stage_parts_from_urls,
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


def resolve_and_download(**context) -> dict:
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
        stage_from_path: Path | None = None
        http_url: str | None = None
        if ep_name:
            resolved = resolve_app_endpoint(
                conn,
                ep_name,
                getenv=os.getenv,
                get_variable=Variable.get,
            )
            frm = resolved["from"]
            to = resolved["to"]
            if to.get("kind") == "env" and to.get("value"):
                landing = Path(to["value"])
            elif to.get("kind") == "path" and to.get("path"):
                landing = Path(to["path"])
            else:
                raise ValueError(f"app_endpoint {ep_name} to side is not a landing path")
            if frm.get("kind") == "env" and frm.get("value"):
                # Stage endpoint: from = source dir, to = landing
                stage_from_path = Path(frm["value"])
            else:
                http_url = frm.get("path") or frm.get("value")
        else:
            code = cfg.get("dataset_code")
            if not code:
                raise ValueError("config_used.dataset_code is required")
            locs = load_dataset_locations(conn, code)
            landing = resolve_landing_dir(
                locs["local"]["local_env_var_name"],
                getenv=os.getenv,
                get_variable=Variable.get,
            )
            http_url = locs.get("http", {}).get("path")

    mode = str(cfg.get("source_mode") or "").strip().lower()
    urls = cfg.get("source_urls")
    stage_env = (cfg.get("stage_from_env") or "").strip()
    part_glob = str(cfg.get("source_filename_glob") or DEFAULT_PART_GLOB)
    filenames = cfg.get("source_filenames") if isinstance(cfg.get("source_filenames"), list) else None

    use_split = (
        mode == "split"
        or bool(stage_env)
        or bool(stage_from_path)
        or (isinstance(urls, list) and bool(urls))
        or bool(cfg.get("source_filename_glob"))
    )

    if use_split:
        if isinstance(urls, list) and urls:
            staged = stage_parts_from_urls(urls, landing, download=download_url_to_path)
        else:
            if stage_from_path is not None:
                source_dir = stage_from_path
                if not source_dir.is_dir():
                    raise FileNotFoundError(f"stage source is not a directory: {source_dir}")
            else:
                source_dir = resolve_named_dir(
                    stage_env or DEFAULT_STAGE_FROM_ENV,
                    getenv=os.getenv,
                    get_variable=Variable.get,
                )
            staged = stage_parts_from_dir(
                source_dir,
                landing,
                source_filenames=filenames,
                source_filename_glob=part_glob,
            )
        return {
            "mode": "split",
            "landing": str(landing),
            "parts": [str(p) for p in staged],
            "part_count": len(staged),
        }

    if not http_url:
        raise ValueError("monolith download requires an HTTP source URL")
    name = Path(urlparse(str(http_url)).path).name or "complaints.csv.zip"
    dest = landing / name
    download_url_to_path(str(http_url), dest)
    return {
        "mode": "monolith",
        "landing": str(landing),
        "parts": [str(dest)],
        "part_count": 1,
    }


def notify_finished(**context) -> None:
    execution_id = _execution_id(context)
    dag_run = context["dag_run"]
    upstream = dag_run.get_task_instance("resolve_and_download")
    ok = upstream is not None and str(upstream.state) == "success"
    ti = context.get("ti")
    volume: dict = {}
    if ti is not None:
        pulled = ti.xcom_pull(task_ids="resolve_and_download") or {}
        if isinstance(pulled, dict) and "part_count" in pulled:
            volume["batch_count"] = int(pulled["part_count"])
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
