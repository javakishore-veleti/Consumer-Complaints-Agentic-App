"""Derive the CFPB 3-month dataset from the All zip by Date received. D51 / D63 / D67 / D70."""

from __future__ import annotations

import os
from datetime import date, datetime, timezone
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
from ccaa.filter_by_date import assert_expected_row_count, filter_zip_by_date_received
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


def _as_of_date(context, cfg: dict) -> date:
    conf = (context.get("dag_run").conf or {}) if context.get("dag_run") else {}
    raw = conf.get("as_of_date") or cfg.get("as_of_date")
    if raw:
        return datetime.strptime(str(raw).strip()[:10], "%Y-%m-%d").date()
    return datetime.now(timezone.utc).date()


def resolve_and_filter(**context) -> str:
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
        months = int(cfg.get("months", 3))
        source_name = str(cfg.get("source_filename") or "complaints.csv.zip")
        output_name = str(cfg.get("output_filename") or "complaints_3_months.csv.zip")
        date_column = str(cfg.get("date_column") or "Date received")
        locs = load_dataset_locations(conn, code)

    landing = resolve_landing_dir(
        locs["local"]["local_env_var_name"],
        getenv=os.getenv,
        get_variable=Variable.get,
    )
    source = landing / source_name
    dest = landing / output_name
    result = filter_zip_by_date_received(
        source,
        dest,
        months=months,
        as_of=_as_of_date(context, cfg),
        date_column=date_column,
    )
    expected = cfg.get("expected_row_count")
    if expected is not None:
        assert_expected_row_count(result.rows_kept, int(expected))
    return f"{result.dest}:{result.rows_kept}"


def notify_finished(**context) -> None:
    execution_id = _execution_id(context)
    dag_run = context["dag_run"]
    upstream = dag_run.get_task_instance("resolve_and_filter")
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
        message=f"resolve_and_filter did not succeed (state={state})",
    )


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
