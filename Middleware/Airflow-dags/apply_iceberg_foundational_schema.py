"""Airflow DAG: Iceberg foundational schema (all zones) — M58-0001 / #400.

Idempotent DDL: Raw → Refined → Taxonomy → Curated inside ``cca-spark-iceberg``.
"""

from __future__ import annotations

import logging
import shlex
from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.trigger_rule import TriggerRule

from ccaa.raw_iceberg import spark_container_name
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
    import docker

    return docker.DockerClient(base_url="unix://var/run/docker.sock")


def _exec(container_name: str, cmd: list[str]) -> str:
    client = _docker_client()
    container = client.containers.get(container_name)
    result = container.exec_run(cmd, demux=True)
    exit_code = result.exit_code
    out_b, err_b = result.output if isinstance(result.output, tuple) else (result.output, b"")
    out = (out_b or b"").decode("utf-8", errors="replace")
    err = (err_b or b"").decode("utf-8", errors="replace")
    if exit_code != 0:
        detail = (out[-4000:] + ("\n--- stderr ---\n" + err[-4000:] if err else "")).strip()
        raise RuntimeError(f"docker exec {container_name} failed ({exit_code}): {detail or err or out}")
    return out


def apply_foundational_ddl(**context) -> dict:
    eid = _execution_id(context)
    if eid:
        report_execution_status(eid, "started", engine_run_id=_engine_run_id(context))
    container = spark_container_name()
    script = "/opt/cca/iceberg/scripts/apply_iceberg_foundational_ddl_incontainer.sh"
    out = _exec(
        container,
        [
            "bash",
            "-lc",
            f"chmod +x {shlex.quote(script)} && bash {shlex.quote(script)}",
        ],
    )
    log.info("foundational DDL output (tail): %s", out[-2000:])
    return {"container": container}


def notify_finished(**context) -> None:
    notify_execution_finished(context, "apply_foundational_ddl")


with DAG(
    dag_id="apply_iceberg_foundational_schema",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    tags=["cca", "iceberg", "schema", "foundational"],
    doc_md=__doc__,
) as dag:
    apply = PythonOperator(task_id="apply_foundational_ddl", python_callable=apply_foundational_ddl)
    finalize = PythonOperator(
        task_id="notify_finished",
        python_callable=notify_finished,
        trigger_rule=TriggerRule.ALL_DONE,
    )
    apply >> finalize
