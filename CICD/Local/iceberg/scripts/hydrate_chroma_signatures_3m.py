"""Host: export Iceberg semantic_signatures → Chroma cfpb_semantic_signatures (M49-0001 / #336)."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
REPO = SCRIPTS.parents[3]
DAGS = REPO / "Middleware" / "Airflow-dags"
if str(DAGS) not in sys.path:
    sys.path.insert(0, str(DAGS))
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from ccaa import vector_index as vi  # noqa: E402
from signature_catalog import (  # noqa: E402
    COLLECTION_NAME,
    signature_to_catalog_doc,
)

EXPORT_IN_CONTAINER = "/tmp/cfpb_semantic_signatures_export"
HOST_EXPORT = Path(os.environ.get("CCA_SIGNATURES_EXPORT_DIR", str(SCRIPTS.parent / ".tmp_exports" / "cfpb_semantic_signatures")))


def _docker_export(container: str, host_export: Path) -> None:
    export_py = SCRIPTS / "export_semantic_signatures_jsonl.py"
    if subprocess.call(
        [
            "docker",
            "exec",
            container,
            "test",
            "-f",
            "/opt/cca/iceberg/scripts/export_semantic_signatures_jsonl.py",
        ]
    ) == 0:
        remote = "/opt/cca/iceberg/scripts/export_semantic_signatures_jsonl.py"
    else:
        subprocess.check_call(
            ["docker", "cp", str(export_py), f"{container}:/tmp/export_semantic_signatures_jsonl.py"]
        )
        remote = "/tmp/export_semantic_signatures_jsonl.py"
    subprocess.check_call(
        ["docker", "exec", container, "rm", "-rf", EXPORT_IN_CONTAINER]
    )
    subprocess.check_call(
        [
            "docker",
            "exec",
            container,
            "/opt/spark/bin/spark-submit",
            remote,
            "--out",
            EXPORT_IN_CONTAINER,
        ]
    )
    if host_export.exists():
        import shutil

        shutil.rmtree(host_export)
    host_export.parent.mkdir(parents=True, exist_ok=True)
    subprocess.check_call(["docker", "cp", f"{container}:{EXPORT_IN_CONTAINER}", str(host_export)])


def _iter_rows(export_dir: Path):
    # Spark JSON write: part-*.json (and sometimes bare *.json); dedupe paths.
    files = sorted(
        {
            p
            for p in list(export_dir.rglob("*.json")) + list(export_dir.rglob("part-*"))
            if p.is_file() and not p.name.startswith("_") and not p.name.endswith(".crc")
        }
    )
    if not files:
        raise FileNotFoundError(f"no JSON parts under {export_dir}")
    for path in files:
        with path.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                yield json.loads(line)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--chroma-url",
        default=os.environ.get("CCA_CHROMA_URL", "http://127.0.0.1:8100"),
    )
    p.add_argument(
        "--container",
        default=os.environ.get("CCA_ICEBERG_SPARK_CONTAINER", "cca-spark-iceberg"),
    )
    p.add_argument("--batch-size", type=int, default=256)
    p.add_argument("--skip-export", action="store_true")
    p.add_argument("--export-dir", default=str(HOST_EXPORT))
    args = p.parse_args()

    export_dir = Path(args.export_dir)
    if not args.skip_export:
        _docker_export(args.container, export_dir)

    store = vi.ChromaStore(args.chroma_url, collection=COLLECTION_NAME)
    batch: list[dict] = []
    total = 0
    for row in _iter_rows(export_dir):
        batch.append(
            signature_to_catalog_doc(row, hash_embedding=vi.hash_embedding, dim=vi.DEFAULT_DIM)
        )
        if len(batch) >= args.batch_size:
            total += store.upsert(batch)
            batch = []
    if batch:
        total += store.upsert(batch)
    counted = store.count()
    print(f"upserted={total} chroma_count={counted} collection={COLLECTION_NAME}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
