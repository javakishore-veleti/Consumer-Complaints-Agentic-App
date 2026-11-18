"""Derive the CFPB 3-month dataset by Date received (D51 / D63 / D67 / D70 / M10-0023 / M17-0001).

Input may be a single .zip/.csv file or a folder of them. Airflow checks which and
filters each matching file **sequentially** (one file at a time, not parallel).

Outputs land in a UTC ``YYYY-MM-DD-HH-MM-SS`` import-run folder under the landing
root and are registered in ``dataset_import_runs`` (same contract as download/stage).
"""

from __future__ import annotations

import logging
import os
from datetime import date, datetime, time, timezone
from pathlib import Path
from uuid import uuid4

from airflow import DAG
from airflow.models import Variable
from airflow.operators.python import PythonOperator
from airflow.utils.trigger_rule import TriggerRule

from ccaa.dag_context import fetch_dag_context
from ccaa.db_reader import resolve_landing_dir
from ccaa.filter_by_date import (
    assert_expected_row_count,
    filter_path_by_date_received,
    filtered_output_name,
    list_filter_inputs,
    subtract_calendar_months,
)
from ccaa.import_runs import (
    LOCATION_LOCAL_PATH,
    build_import_metadata,
    dataset_dir,
    prepare_run_folder,
    resolve_snapshot_window,
    write_import_metadata,
)
from ccaa.status_callback import (
    notify_execution_finished,
    report_execution_status,
    report_import_run_create,
    report_import_run_update,
)

log = logging.getLogger(__name__)


def _execution_id(context) -> str:
    conf = (context.get("dag_run").conf or {}) if context.get("dag_run") else {}
    execution_id = conf.get("execution_id")
    if not execution_id:
        raise ValueError("dag_run.conf.execution_id is required")
    return str(execution_id)


def _engine_run_id(context) -> str | None:
    run_id = context.get("run_id")
    return str(run_id)[:128] if run_id else None


def _mio_id(context) -> str | None:
    conf = (context.get("dag_run").conf or {}) if context.get("dag_run") else {}
    raw = conf.get("mio_id")
    return str(raw) if raw else None


def _as_of_date(context, cfg: dict) -> date:
    conf = (context.get("dag_run").conf or {}) if context.get("dag_run") else {}
    raw = conf.get("as_of_date") or cfg.get("as_of_date")
    if raw:
        return datetime.strptime(str(raw).strip()[:10], "%Y-%m-%d").date()
    return datetime.now(timezone.utc).date()


def _resolve_source_path(cfg: dict, landing: Path) -> Path:
    """Prefer explicit source_path, then CCA_CFPB_SPLIT_SOURCE_PATH, then landing file."""
    raw = cfg.get("source_path")
    if raw:
        return Path(str(raw)).expanduser()
    env_name = str(cfg.get("source_path_env") or "CCA_CFPB_SPLIT_SOURCE_PATH_3_MONTHS").strip()
    from_env = ""

    def _lookup(name: str) -> str:
        if not name:
            return ""
        value = (os.getenv(name) or "").strip()
        if value:
            return value
        try:
            return str(Variable.get(name) or "").strip()
        except Exception:
            return ""

    if env_name:
        from_env = _lookup(env_name)
    # Legacy single-folder env (pre–M17-0005) if the per-MIO var is unset.
    if not from_env:
        from_env = _lookup("CCA_CFPB_SPLIT_SOURCE_PATH")
    if from_env:
        return Path(from_env).expanduser()
    source_name = str(cfg.get("source_filename") or "complaints.csv.zip")
    return landing / source_name


def resolve_and_filter(**context) -> str:
    execution_id = _execution_id(context)
    report_execution_status(
        execution_id,
        "started",
        engine_run_id=_engine_run_id(context),
    )

    ctx = fetch_dag_context(execution_id)
    cfg = ctx.get("config_used") or {}
    code = cfg.get("dataset_code")
    if not code:
        raise ValueError("config_used.dataset_code is required")
    months = int(cfg.get("months", 3))
    date_column = str(cfg.get("date_column") or "Date received")
    locs = ctx.get("dataset_locations") or {}
    if "local" not in locs or not locs["local"].get("local_env_var_name"):
        raise ValueError("dataset missing local landing location")

    landing = resolve_landing_dir(
        locs["local"]["local_env_var_name"],
        getenv=os.getenv,
        get_variable=Variable.get,
    )
    source_path = _resolve_source_path(cfg, landing)
    inputs = list_filter_inputs(source_path)
    as_of = _as_of_date(context, cfg)
    expected = cfg.get("expected_row_count")
    total = len(inputs)

    started = datetime.now(timezone.utc)
    snap_start_dt = datetime.combine(
        subtract_calendar_months(as_of, months),
        time.min,
        tzinfo=timezone.utc,
    )
    snap_end_dt = datetime.combine(as_of, time.max.replace(microsecond=0), tzinfo=timezone.utc)
    snap_start, snap_end = resolve_snapshot_window(
        started,
        source_snapshot_start=snap_start_dt,
        source_snapshot_end=snap_end_dt,
    )
    run_folder = prepare_run_folder(landing, started)
    dest_dir = dataset_dir(run_folder)
    import_id = str(uuid4())
    location_ref = str(run_folder.resolve())
    part_glob = "*_3_months.csv.zip"
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
            "mio_id": _mio_id(context),
            "part_count": 0,
        }
    )

    log.info(
        "filter_cfpb_3_months start execution_id=%s dataset_code=%s "
        "mode=sequential file_count=%s months=%s as_of=%s date_column=%s "
        "input_path=%s landing=%s run_folder=%s import_id=%s",
        execution_id,
        code,
        total,
        months,
        as_of.isoformat(),
        date_column,
        source_path,
        landing,
        run_folder,
        import_id,
    )
    for i, src in enumerate(inputs, start=1):
        log.info("filter input [%s/%s] %s", i, total, src)

    kept_total = 0
    outputs: list[str] = []
    try:
        for i, src in enumerate(inputs, start=1):
            dest = dest_dir / filtered_output_name(src)
            log.info(
                "filter progress [%s/%s] BEGIN input=%s output=%s",
                i,
                total,
                src,
                dest,
            )
            try:
                result = filter_path_by_date_received(
                    src,
                    dest,
                    months=months,
                    as_of=as_of,
                    date_column=date_column,
                )
            except Exception:
                log.exception(
                    "filter progress [%s/%s] FAILED input=%s intended_output=%s",
                    i,
                    total,
                    src,
                    dest,
                )
                raise
            kept_total += result.rows_kept
            outputs.append(f"{result.dest}:{result.rows_kept}")
            log.info(
                "filter progress [%s/%s] DONE input=%s output=%s rows_kept=%s",
                i,
                total,
                src,
                result.dest,
                result.rows_kept,
            )

        if expected is not None:
            assert_expected_row_count(kept_total, int(expected))

        completed = datetime.now(timezone.utc)
        meta["part_count"] = total
        meta["workflow_completed_at"] = completed.strftime("%Y-%m-%dT%H:%M:%SZ")
        write_import_metadata(run_folder, meta)
        report_import_run_update(
            import_id,
            {
                "status": "landed",
                "workflow_completed_at": meta["workflow_completed_at"],
                "part_count": total,
            },
        )
    except Exception as exc:
        report_import_run_update(
            import_id,
            {"status": "failed", "message": str(exc)[:2000]},
        )
        raise

    summary = ";".join(outputs)
    log.info(
        "filter_cfpb_3_months complete execution_id=%s files=%s rows_kept_total=%s "
        "run_folder=%s import_id=%s",
        execution_id,
        total,
        kept_total,
        run_folder,
        import_id,
    )
    return summary


def notify_finished(**context) -> None:
    notify_execution_finished(context, "resolve_and_filter")


with DAG(
    dag_id="filter_cfpb_3_months",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    tags=["ccaa", "cfpb", "filter"],
) as dag:
    filter_task = PythonOperator(
        task_id="resolve_and_filter",
        python_callable=resolve_and_filter,
    )
    finalize = PythonOperator(
        task_id="notify_finished",
        python_callable=notify_finished,
        trigger_rule=TriggerRule.ALL_DONE,
    )
    filter_task >> finalize
