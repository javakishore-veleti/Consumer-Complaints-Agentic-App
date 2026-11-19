"""Airflow DAG: Lift Zone 3m → Iceberg Raw hydrate (M45-0003 / #322).

Does not re-download CFPB data. Invokes Spark inside ``cca-spark-iceberg`` via
Docker API (local compose mounts ``/var/run/docker.sock``).
"""

from __future__ import annotations

import logging
import shlex
from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.trigger_rule import TriggerRule

from ccaa.raw_iceberg import (
    DEFAULT_TARGET_TABLE,
    dq_null_check_sql,
    find_latest_3m_batch,
    pre_ingest_gate,
    resolve_lift_root,
    spark_container_name,
)
from ccaa.status_callback import notify_execution_finished, report_execution_status

log = logging.getLogger(__name__)


def _execution_id(context) -> str | None:
    conf = (context.get("dag_run").conf or {}) if context.get("dag_run") else {}
    raw = conf.get("execution_id")
    return str(raw) if raw else None


def _engine_run_id(context) -> str:
    run_id = context.get("run_id")
    return str(run_id)[:128] if run_id else f"manual-{datetime.utcnow():%Y%m%dT%H%M%SZ}"


def _docker_client():
    import docker  # baked into local cca-airflow image

    return docker.DockerClient(base_url="unix://var/run/docker.sock")


def _exec(container_name: str, cmd: list[str], workdir: str | None = None) -> str:
    client = _docker_client()
    container = client.containers.get(container_name)
    result = container.exec_run(cmd, workdir=workdir, demux=True)
    exit_code = result.exit_code
    out_b, err_b = result.output if isinstance(result.output, tuple) else (result.output, b"")
    out = (out_b or b"").decode("utf-8", errors="replace")
    err = (err_b or b"").decode("utf-8", errors="replace")
    if exit_code != 0:
        raise RuntimeError(f"docker exec {container_name} failed ({exit_code}): {err or out}")
    return out


def sense_lift_3m(**context) -> dict:
    eid = _execution_id(context)
    if eid:
        report_execution_status(eid, "started", engine_run_id=_engine_run_id(context))
    lift = resolve_lift_root()
    batch = find_latest_3m_batch(lift)
    log.info("sensed lift batch %s", batch)
    return {"lift_root": str(lift), "batch_dir": str(batch)}


def run_pre_ingest_gate(**context) -> dict:
    ti = context["ti"]
    sensed = ti.xcom_pull(task_ids="sense_lift_3m") or {}
    batch = sensed.get("batch_dir")
    if not batch:
        raise ValueError("sense_lift_3m did not return batch_dir")
    from pathlib import Path

    return pre_ingest_gate(Path(batch))


def hydrate_raw(**context) -> dict:
    run_id = _engine_run_id(context)
    container = spark_container_name()
    scripts = "/opt/cca/iceberg/scripts"
    out = _exec(
        container,
        [
            "bash",
            "-lc",
            f"export CCA_RAW_RUN_ID={shlex.quote(run_id)}; "
            f"bash {shlex.quote(scripts + '/run_hydrate_raw_3m_incontainer.sh')}",
        ],
    )
    log.info("hydrate output (tail): %s", out[-2000:])
    return {"run_id": run_id, "container": container}


def dq_checks(**context) -> dict:
    container = spark_container_name()
    table = DEFAULT_TARGET_TABLE
    count_out = _exec(container, ["spark-sql", "-e", f"SELECT COUNT(*) FROM {table};"])
    # spark-sql prints the number on its own line among logs — take last integer token
    digits = [tok for tok in count_out.replace(",", " ").split() if tok.isdigit()]
    if not digits:
        raise RuntimeError(f"could not parse COUNT from: {count_out[-500:]}")
    total = int(digits[-1])
    if total <= 0:
        raise RuntimeError(f"{table} COUNT(*)={total} — expected > 0")

    null_sql = dq_null_check_sql(table)
    null_out = _exec(container, ["spark-sql", "-e", null_sql + ";"])
    log.info("dq null check: %s", null_out[-1000:])
    # Fail if any null_* > 0 appears as non-zero after total in a simple scan:
    # Prefer explicit spark-sql that returns bad count.
    bad_sql = (
        f"SELECT "
        + " + ".join(
            [
                "SUM(CASE WHEN date_received IS NULL THEN 1 ELSE 0 END)",
                "SUM(CASE WHEN complaint_id IS NULL OR TRIM(CAST(complaint_id AS STRING)) = '' THEN 1 ELSE 0 END)",
                "SUM(CASE WHEN product IS NULL OR TRIM(CAST(product AS STRING)) = '' THEN 1 ELSE 0 END)",
                "SUM(CASE WHEN company IS NULL OR TRIM(CAST(company AS STRING)) = '' THEN 1 ELSE 0 END)",
            ]
        )
        + f" AS bad_keys FROM {table}"
    )
    bad_out = _exec(container, ["spark-sql", "-e", bad_sql + ";"])
    bad_digits = [tok for tok in bad_out.replace(",", " ").split() if tok.isdigit()]
    bad = int(bad_digits[-1]) if bad_digits else -1
    if bad != 0:
        raise RuntimeError(f"mandatory-key null/blank rows={bad} (output={bad_out[-500:]})")
    return {"total": total, "bad_keys": bad}


def cleanup_stage(**context) -> dict:
    run_id = _engine_run_id(context)
    container = spark_container_name()
    stage = f"/tmp/cca_raw_stage/{run_id}"
    try:
        _exec(container, ["bash", "-lc", f"rm -rf {shlex.quote(stage)}"])
    except Exception as exc:  # noqa: BLE001 — cleanup best-effort
        log.warning("cleanup failed for %s: %s", stage, exc)
        return {"cleaned": False, "stage": stage, "error": str(exc)}
    return {"cleaned": True, "stage": stage}


def notify_finished(**context) -> None:
    notify_execution_finished(context, "dq_checks")


with DAG(
    dag_id="hydrate_raw_iceberg_3m",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    tags=["cca", "raw", "iceberg", "3m"],
    doc_md=__doc__,
) as dag:
    sense = PythonOperator(task_id="sense_lift_3m", python_callable=sense_lift_3m)
    gate = PythonOperator(task_id="pre_ingest_gate", python_callable=run_pre_ingest_gate)
    hydrate = PythonOperator(task_id="hydrate_raw", python_callable=hydrate_raw)
    dq = PythonOperator(task_id="dq_checks", python_callable=dq_checks)
    cleanup = PythonOperator(
        task_id="cleanup_stage",
        python_callable=cleanup_stage,
        trigger_rule=TriggerRule.ALL_DONE,
    )
    finalize = PythonOperator(
        task_id="notify_finished",
        python_callable=notify_finished,
        trigger_rule=TriggerRule.ALL_DONE,
    )

    sense >> gate >> hydrate >> dq >> cleanup >> finalize
