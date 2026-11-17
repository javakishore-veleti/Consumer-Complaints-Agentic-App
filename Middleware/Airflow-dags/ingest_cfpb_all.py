"""Ingest landed CFPB complaint zip part(s) into local Mongo. D20 / D67 / D86 / D91 / M11."""

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
    resolve_app_endpoint,
    resolve_landing_dir,
)
from ccaa.import_runs import dataset_dir
from ccaa.mongo_ingest import (
    DEFAULT_BATCH_SIZE,
    ingest_complaints_parts,
    ingest_complaints_zip,
    open_complaints_collection,
    resolve_complaints_mongo_url,
)
from ccaa.split_parts import DEFAULT_PART_GLOB, list_part_files
from ccaa.status_callback import (
    notify_execution_finished,
    report_execution_status,
    report_import_run_update,
)


def _conf(context) -> dict:
    return (context.get("dag_run").conf or {}) if context.get("dag_run") else {}


def _execution_id(context) -> str:
    execution_id = _conf(context).get("execution_id")
    if not execution_id:
        raise ValueError("dag_run.conf.execution_id is required")
    return str(execution_id)


def _engine_run_id(context) -> str | None:
    run_id = context.get("run_id")
    return str(run_id)[:128] if run_id else None


def _import_id(context) -> str | None:
    value = _conf(context).get("import_id")
    return str(value).strip() if value else None


def resolve_and_ingest(**context) -> dict:
    conf = _conf(context)
    execution_id = _execution_id(context)
    import_id = _import_id(context)
    # Child runs (selected import) leave exec-log status to the wrapper.
    if not import_id:
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
            if frm.get("kind") == "env" and frm.get("value"):
                landing = Path(frm["value"])
            elif frm.get("kind") == "path" and frm.get("path"):
                landing = Path(frm["path"])
            else:
                raise ValueError(f"app_endpoint {ep_name} from side is not a landing path")
            to = resolved["to"]
            if to.get("kind") == "env" and to.get("value"):
                mongo_url = to["value"]
            else:
                raise ValueError(f"app_endpoint {ep_name} to side must be env (Mongo URI)")
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
            mongo_url = resolve_complaints_mongo_url(
                getenv=os.getenv,
                get_variable=Variable.get,
            )

    batch_size = int(cfg.get("batch_size") or DEFAULT_BATCH_SIZE)
    filenames = cfg.get("source_filenames") if isinstance(cfg.get("source_filenames"), list) else None
    glob_pat = cfg.get("source_filename_glob")
    single = cfg.get("source_filename")

    location_ref = conf.get("location_ref")
    if import_id and location_ref:
        run_folder = Path(str(location_ref))
        parts_root = dataset_dir(run_folder)
        if not parts_root.is_dir():
            raise FileNotFoundError(f"import dataset dir missing: {parts_root}")
        landing_for_parts = parts_root
    else:
        landing_for_parts = landing

    try:
        # Prefer split list/glob (D91). Legacy: only source_filename → single monolith zip.
        if filenames or glob_pat or not single or import_id:
            parts = list_part_files(
                landing_for_parts,
                source_filenames=filenames,
                source_filename_glob=str(glob_pat) if glob_pat else DEFAULT_PART_GLOB,
                source_filename=None,
            )
            coll = open_complaints_collection(mongo_url)
            result = ingest_complaints_parts(parts, coll, batch_size=batch_size)
            out = {
                "rows_loaded": result.rows_loaded,
                "batch_count": result.batch_count,
                "part_count": len(parts),
                "sources": [str(p) for p in parts],
                "import_id": import_id,
            }
        else:
            source = landing_for_parts / str(single)
            coll = open_complaints_collection(mongo_url)
            result = ingest_complaints_zip(source, coll, batch_size=batch_size)
            out = {
                "rows_loaded": result.rows_loaded,
                "batch_count": result.batch_count,
                "part_count": 1,
                "sources": [str(source)],
                "import_id": import_id,
            }
        if import_id:
            report_import_run_update(import_id, {"status": "ingested", "part_count": out["part_count"]})
        return out
    except Exception as exc:
        if import_id:
            report_import_run_update(import_id, {"status": "failed", "message": str(exc)[:2000]})
        raise


def notify_finished(**context) -> None:
    import_id = _import_id(context)
    if import_id:
        # Wrapper owns the parent execution status.
        return
    ti = context.get("ti")
    volume: dict = {}
    if ti is not None:
        pulled = ti.xcom_pull(task_ids="resolve_and_ingest") or {}
        if isinstance(pulled, dict):
            if "rows_loaded" in pulled:
                volume["rows_loaded"] = int(pulled["rows_loaded"])
            if "batch_count" in pulled:
                volume["batch_count"] = int(pulled["batch_count"])
            if "part_count" in pulled:
                volume["increment_marker"] = f"parts={int(pulled['part_count'])}"[:255]
    notify_execution_finished(
        context,
        "resolve_and_ingest",
        completed_kwargs=volume or None,
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
