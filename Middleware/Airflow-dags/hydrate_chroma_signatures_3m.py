"""Airflow DAG: Chroma cfpb_semantic_signatures catalog (M51-0005 / #345)."""

from __future__ import annotations

import json
import logging
import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.trigger_rule import TriggerRule

from ccaa import vector_index as vi
from ccaa.lakehouse_spark import (
    docker_exec,
    engine_run_id,
    execution_id,
    spark_container_name,
    spark_submit_script,
)
from ccaa.signature_catalog import COLLECTION_NAME, signature_to_catalog_doc
from ccaa.status_callback import notify_execution_finished, report_execution_status

log = logging.getLogger(__name__)
EXPORT_IN_CONTAINER = "/tmp/cfpb_semantic_signatures_export"


def mark_started(**context) -> None:
    eid = execution_id(context)
    if eid:
        report_execution_status(eid, "started", engine_run_id=engine_run_id(context))


def hydrate_chroma(**context) -> dict:
    run_id = execution_id(context) or engine_run_id(context)
    container = spark_container_name()
    docker_exec(container, ["rm", "-rf", EXPORT_IN_CONTAINER])
    spark_submit_script(
        script_name="export_semantic_signatures_jsonl.py",
        run_id=run_id,
        pass_run_id=False,
        extra_args=["--out", EXPORT_IN_CONTAINER],
    )
    host_dir = Path(tempfile.mkdtemp(prefix="cca_chroma_export_"))
    try:
        import docker

        client = docker.DockerClient(base_url="unix://var/run/docker.sock")
        # docker cp container:path host_dir
        # SDK: get_archive — use CLI via container for simplicity
        docker_exec(container, ["bash", "-lc", f"test -d {EXPORT_IN_CONTAINER}"])
        # Copy via `docker cp` subprocess from Airflow host namespace
        import subprocess

        dest = host_dir / "export"
        subprocess.check_call(["docker", "cp", f"{container}:{EXPORT_IN_CONTAINER}", str(dest)])
        files = sorted(
            {
                p
                for p in list(dest.rglob("*.json")) + list(dest.rglob("part-*"))
                if p.is_file() and not p.name.startswith("_") and not p.name.endswith(".crc")
            }
        )
        if not files:
            raise FileNotFoundError(f"no export parts under {dest}")
        chroma_url = (
            os.environ.get("CCA_CHROMA_URL") or "http://host.docker.internal:8100"
        ).strip()
        store = vi.ChromaStore(chroma_url, collection=COLLECTION_NAME)
        batch: list[dict] = []
        total = 0
        for path in files:
            with path.open(encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    row = json.loads(line)
                    batch.append(
                        signature_to_catalog_doc(
                            row, hash_embedding=vi.hash_embedding, dim=vi.DEFAULT_DIM
                        )
                    )
                    if len(batch) >= 256:
                        total += store.upsert(batch)
                        batch = []
        if batch:
            total += store.upsert(batch)
        counted = store.count()
        log.info("chroma upserted=%s count=%s", total, counted)
        if counted <= 0:
            raise RuntimeError("chroma collection empty after upsert")
        return {"upserted": total, "chroma_count": counted}
    finally:
        shutil.rmtree(host_dir, ignore_errors=True)


def notify_finished(**context) -> None:
    notify_execution_finished(context, "hydrate_chroma")


with DAG(
    dag_id="hydrate_chroma_signatures_3m",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    tags=["cca", "chroma", "lakehouse", "3m"],
    doc_md=__doc__,
) as dag:
    start = PythonOperator(task_id="mark_started", python_callable=mark_started)
    hydrate = PythonOperator(task_id="hydrate_chroma", python_callable=hydrate_chroma)
    finalize = PythonOperator(
        task_id="notify_finished",
        python_callable=notify_finished,
        trigger_rule=TriggerRule.ALL_DONE,
    )
    start >> hydrate >> finalize
