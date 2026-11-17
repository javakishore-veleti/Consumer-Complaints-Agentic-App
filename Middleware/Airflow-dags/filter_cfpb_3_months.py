"""Derive the CFPB 3-month dataset by Date received (D51 / D63 / D67 / D70 / M10-0023).

Input may be a single .zip/.csv file or a folder of them. Airflow checks which and
filters each matching file.
"""

from __future__ import annotations

import os
from datetime import date, datetime, timezone
from pathlib import Path

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
)
from ccaa.status_callback import notify_execution_finished, report_execution_status


def _execution_id(context) -> str:
    conf = (context.get("dag_run").conf or {}) if context.get("dag_run") else {}
    execution_id = conf.get("execution_id")
    if not execution_id:
        raise ValueError("dag_run.conf.execution_id is required")
    return str(execution_id)


def _engine_run_id(context) -> str | None:
    run_id = context.get("run_id")
    return str(run_id)[:128] if run_id else None


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
    env_name = str(cfg.get("source_path_env") or "CCA_CFPB_SPLIT_SOURCE_PATH").strip()
    from_env = ""
    if env_name:
        from_env = (os.getenv(env_name) or "").strip()
        if not from_env:
            try:
                from_env = str(Variable.get(env_name) or "").strip()
            except Exception:
                from_env = ""
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

    kept_total = 0
    outputs: list[str] = []
    for src in inputs:
        dest = landing / filtered_output_name(src)
        result = filter_path_by_date_received(
            src,
            dest,
            months=months,
            as_of=as_of,
            date_column=date_column,
        )
        kept_total += result.rows_kept
        outputs.append(f"{result.dest}:{result.rows_kept}")

    if expected is not None:
        assert_expected_row_count(kept_total, int(expected))
    return ";".join(outputs)


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
