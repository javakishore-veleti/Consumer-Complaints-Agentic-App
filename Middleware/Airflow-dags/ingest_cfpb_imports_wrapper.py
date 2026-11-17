"""Wrapper: sequential/parallel Mongo ingest of selected import runs (M11)."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.utils.trigger_rule import TriggerRule

from ccaa.status_callback import (
    report_execution_status,
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


def prepare_and_mark(**context) -> list[dict]:
    """Validate conf, mark each import ingesting, return child conf payloads."""
    execution_id = _execution_id(context)
    report_execution_status(
        execution_id,
        "started",
        engine_run_id=_engine_run_id(context),
    )
    conf = _conf(context)
    imports = conf.get("imports")
    if not isinstance(imports, list) or not imports:
        raise ValueError("dag_run.conf.imports is required (non-empty)")
    mode = str(conf.get("mode") or "sequential").strip().lower() or "sequential"
    children: list[dict] = []
    for item in imports:
        if not isinstance(item, dict) or not item.get("id") or not item.get("location_ref"):
            raise ValueError("each imports[] entry needs id and location_ref")
        import_id = str(item["id"])
        report_import_run_update(import_id, {"status": "ingesting"})
        children.append(
            {
                "execution_id": execution_id,
                "import_id": import_id,
                "location_kind": item.get("location_kind") or "local_path",
                "location_ref": item["location_ref"],
                "run_folder_name": item.get("run_folder_name"),
                "mode": mode,
            }
        )
    return children


def _trigger_child(context, child: dict) -> dict:
    op = TriggerDagRunOperator(
        task_id=f"_trigger_{child['import_id'][:8]}",
        trigger_dag_id="ingest_cfpb_all",
        conf={
            "execution_id": child["execution_id"],
            "import_id": child["import_id"],
            "location_kind": child["location_kind"],
            "location_ref": child["location_ref"],
        },
        wait_for_completion=True,
        poke_interval=5,
        reset_dag_run=True,
    )
    op.execute(context=context)
    return {"import_id": child["import_id"], "ok": True}


def run_children(**context) -> dict:
    """Trigger ingest_cfpb_all once per import (sequential default; parallel via thread pool)."""
    ti = context["ti"]
    children = ti.xcom_pull(task_ids="prepare_and_mark") or []
    if not children:
        raise ValueError("no imports to ingest")
    mode = str(children[0].get("mode") or "sequential")
    results: list[dict] = []

    if mode == "parallel" and len(children) > 1:
        errors: list[BaseException] = []
        with ThreadPoolExecutor(max_workers=min(8, len(children))) as pool:
            futures = {pool.submit(_trigger_child, context, child): child for child in children}
            for fut in as_completed(futures):
                child = futures[fut]
                try:
                    results.append(fut.result())
                except BaseException as exc:
                    report_import_run_update(
                        child["import_id"],
                        {"status": "failed", "message": str(exc)[:2000]},
                    )
                    errors.append(exc)
        if errors:
            raise errors[0]
    else:
        for child in children:
            try:
                results.append(_trigger_child(context, child))
            except Exception as exc:
                report_import_run_update(
                    child["import_id"],
                    {"status": "failed", "message": str(exc)[:2000]},
                )
                raise
    return {"mode": mode, "results": results, "count": len(results)}


def notify_finished(**context) -> None:
    execution_id = _execution_id(context)
    dag_run = context["dag_run"]
    upstream = dag_run.get_task_instance("run_children")
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
        message=f"run_children did not succeed (state={state})",
    )


with DAG(
    dag_id="ingest_cfpb_imports_wrapper",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    tags=["ccaa", "cfpb", "ingest", "wrapper"],
) as dag:
    prepare = PythonOperator(
        task_id="prepare_and_mark",
        python_callable=prepare_and_mark,
    )
    run = PythonOperator(
        task_id="run_children",
        python_callable=run_children,
    )
    finalize = PythonOperator(
        task_id="notify_finished",
        python_callable=notify_finished,
        trigger_rule=TriggerRule.ALL_DONE,
    )
    prepare >> run >> finalize
