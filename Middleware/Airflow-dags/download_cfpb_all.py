"""Download or stage CFPB complaints into local landing. D51 / D63 / D67 / D91 / M11."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from uuid import uuid4

from airflow import DAG
from airflow.models import Variable
from airflow.operators.python import PythonOperator
from airflow.utils.trigger_rule import TriggerRule

from ccaa.dag_context import fetch_dag_context, materialize_app_endpoint
from ccaa.db_reader import resolve_landing_dir
from ccaa.download import download_url_to_path
from ccaa.import_runs import (
    LOCATION_LOCAL_PATH,
    build_import_metadata,
    dataset_dir,
    prepare_run_folder,
    resolve_snapshot_window,
    write_import_metadata,
)
from ccaa.split_parts import (
    DEFAULT_PART_GLOB,
    DEFAULT_STAGE_FROM_ENV,
    resolve_named_dir,
    stage_parts_from_dir,
    stage_parts_from_urls,
)
from ccaa.status_callback import (
    notify_execution_finished,
    report_execution_status,
    report_import_run_create,
    report_import_run_update,
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


def _conf(context) -> dict:
    return (context.get("dag_run").conf or {}) if context.get("dag_run") else {}


def resolve_and_download(**context) -> dict:
    execution_id = _execution_id(context)
    report_execution_status(
        execution_id,
        "started",
        engine_run_id=_engine_run_id(context),
    )

    ctx = fetch_dag_context(execution_id)
    cfg = ctx.get("config_used") or {}
    ep_name = (cfg.get("app_endpoint_name") or "").strip()
    stage_from_path: Path | None = None
    http_url: str | None = None
    if ep_name:
        raw_ep = ctx.get("app_endpoint") or fetch_dag_context(
            execution_id, app_endpoint=ep_name
        ).get("app_endpoint")
        if not raw_ep:
            raise ValueError(f"app_endpoint not found: {ep_name}")
        resolved = materialize_app_endpoint(
            raw_ep, getenv=os.getenv, get_variable=Variable.get
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
        locs = ctx.get("dataset_locations") or {}
        if "local" not in locs or not locs["local"].get("local_env_var_name"):
            raise ValueError("dataset missing local landing location")
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
        conf = _conf(context)
        started = datetime.now(timezone.utc)
        snap_start, snap_end = resolve_snapshot_window(
            started,
            source_snapshot_start=conf.get("source_snapshot_start"),
            source_snapshot_end=conf.get("source_snapshot_end"),
        )
        run_folder = prepare_run_folder(landing, started)
        dest_dir = dataset_dir(run_folder)
        import_id = str(uuid4())
        location_ref = str(run_folder.resolve())
        meta = build_import_metadata(
            import_id=import_id,
            workflow_started_at=started,
            source_snapshot_start=snap_start,
            source_snapshot_end=snap_end,
            location_ref=location_ref,
            location_kind=LOCATION_LOCAL_PATH,
            part_glob=part_glob,
            part_count=0,
        )
        write_import_metadata(run_folder, meta)
        report_import_run_create(
            {
                "id": import_id,
                "run_folder_name": run_folder.name,
                "location_kind": LOCATION_LOCAL_PATH,
                "location_ref": location_ref,
                "source_snapshot_start": meta["source_snapshot_start"],
                "source_snapshot_end": meta["source_snapshot_end"],
                "workflow_started_at": meta["workflow_started_at"],
                "status": "staging",
                "execution_id": execution_id,
                "part_count": 0,
            }
        )

        try:
            if isinstance(urls, list) and urls:
                staged = stage_parts_from_urls(urls, dest_dir, download=download_url_to_path)
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
                    dest_dir,
                    source_filenames=filenames,
                    source_filename_glob=part_glob,
                )
            completed = datetime.now(timezone.utc)
            meta["part_count"] = len(staged)
            meta["workflow_completed_at"] = completed.strftime("%Y-%m-%dT%H:%M:%SZ")
            write_import_metadata(run_folder, meta)
            report_import_run_update(
                import_id,
                {
                    "status": "landed",
                    "workflow_completed_at": meta["workflow_completed_at"],
                    "part_count": len(staged),
                },
            )
        except Exception as exc:
            report_import_run_update(
                import_id,
                {
                    "status": "failed",
                    "message": str(exc)[:2000],
                },
            )
            raise

        return {
            "mode": "split",
            "landing": str(landing),
            "run_folder": str(run_folder),
            "import_id": import_id,
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
    ti = context.get("ti")
    volume: dict = {}
    if ti is not None:
        pulled = ti.xcom_pull(task_ids="resolve_and_download") or {}
        if isinstance(pulled, dict) and "part_count" in pulled:
            volume["batch_count"] = int(pulled["part_count"])
    notify_execution_finished(
        context,
        "resolve_and_download",
        completed_kwargs=volume or None,
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
