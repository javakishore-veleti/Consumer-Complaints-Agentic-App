"""Shared Spark-docker helpers for Admin-triggerable lakehouse hydrate DAGs (M51)."""

from __future__ import annotations

import logging
import os
import shlex
from datetime import datetime
from typing import Any

log = logging.getLogger(__name__)

DEFAULT_SPARK_CONTAINER = "cca-spark-iceberg"
SCRIPTS_IN_CONTAINER = "/opt/cca/iceberg/scripts"


def spark_container_name() -> str:
    return (os.environ.get("CCA_ICEBERG_SPARK_CONTAINER") or DEFAULT_SPARK_CONTAINER).strip()


def execution_id(context: dict[str, Any]) -> str | None:
    conf = (context.get("dag_run").conf or {}) if context.get("dag_run") else {}
    raw = conf.get("execution_id")
    return str(raw) if raw else None


def engine_run_id(context: dict[str, Any]) -> str:
    run_id = context.get("run_id")
    return str(run_id)[:128] if run_id else f"manual-{datetime.utcnow():%Y%m%dT%H%M%SZ}"


def docker_exec(container_name: str, cmd: list[str], *, workdir: str | None = None) -> str:
    import docker

    client = docker.DockerClient(base_url="unix://var/run/docker.sock")
    container = client.containers.get(container_name)
    result = container.exec_run(cmd, workdir=workdir, demux=True)
    exit_code = result.exit_code
    out_b, err_b = result.output if isinstance(result.output, tuple) else (result.output, b"")
    out = (out_b or b"").decode("utf-8", errors="replace")
    err = (err_b or b"").decode("utf-8", errors="replace")
    if exit_code != 0:
        raise RuntimeError(f"docker exec {container_name} failed ({exit_code}): {err or out}")
    return out


def parse_last_int(spark_out: str) -> int:
    digits = [tok for tok in spark_out.replace(",", " ").split() if tok.isdigit()]
    if not digits:
        raise RuntimeError(f"could not parse integer from spark output: {spark_out[-500:]}")
    return int(digits[-1])


def spark_submit_script(
    *,
    script_name: str,
    run_id: str | None = None,
    extra_args: list[str] | None = None,
    env_exports: dict[str, str] | None = None,
    pass_run_id: bool = True,
) -> str:
    container = spark_container_name()
    scripts = SCRIPTS_IN_CONTAINER
    remote = f"{scripts}/{script_name}"
    args_list = list(extra_args or [])
    if pass_run_id and run_id is not None:
        args_list = ["--run-id", run_id, *args_list]
    args = " ".join(shlex.quote(a) for a in args_list)
    exports = " ".join(f"export {k}={shlex.quote(v)};" for k, v in (env_exports or {}).items())
    cmd = (
        f"{exports} "
        f"export PYTHONPATH={shlex.quote(scripts)}; "
        f"spark-submit {shlex.quote(remote)} {args}"
    ).strip()
    out = docker_exec(container, ["bash", "-lc", cmd])
    log.info("spark-submit %s tail: %s", script_name, out[-1500:])
    return out


def count_table(table: str) -> int:
    container = spark_container_name()
    out = docker_exec(container, ["spark-sql", "-e", f"SELECT COUNT(*) FROM {table};"])
    return parse_last_int(out)
