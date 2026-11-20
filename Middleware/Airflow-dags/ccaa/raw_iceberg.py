"""Lift → Iceberg Raw helpers for hydrate_raw_iceberg_3m (M45-0003 / #322)."""

from __future__ import annotations

import os
import zipfile
from pathlib import Path

# Keep in sync with CICD/Local/iceberg/scripts/hydrate_raw_headers.py
EXPECTED_HEADERS = [
    "Date received",
    "Product",
    "Sub-product",
    "Issue",
    "Sub-issue",
    "Company public response",
    "Company",
    "State",
    "ZIP code",
    "Tags",
    "Submitted via",
    "Date sent to company",
    "Company response to consumer",
    "Timely response?",
    "Complaint ID",
]

MANDATORY_SQL_KEYS = ("complaint_id", "date_received", "product", "company")
DEFAULT_SPARK_CONTAINER = "cca-spark-iceberg"
DEFAULT_TARGET_TABLE = "demo.raw.cfpb_complaints_3m"


def _lookup_path(name: str, getenv, get_variable) -> str:
    value = (getenv(name) or "").strip()
    if value:
        return value
    if get_variable is None:
        return ""
    try:
        return str(get_variable(name) or "").strip()
    except Exception:
        return ""


def resolve_lift_root(getenv=os.getenv, get_variable=None) -> Path:
    """Lift root or imports landing dir (same Variable as filter_cfpb_*).

    Prefers env, then Airflow Variable — LocalExecutor often has no CCA_* in
    process env, only Variables from Sync secrets.
    """
    raw = (
        _lookup_path("CCA_LIFT_ZONE", getenv, get_variable)
        or _lookup_path("LOCAL_DATA_PATH_CFPB", getenv, get_variable)
        or str(Path.home() / "runtime_data/apps/datasets/CCA/complains_datasets")
    )
    return Path(raw).expanduser()


def resolve_imports_dir(lift_root: Path) -> Path:
    """``LOCAL_DATA_PATH_CFPB`` is the imports landing; ``CCA_LIFT_ZONE`` is parent."""
    if lift_root.name == "imports":
        return lift_root
    nested = lift_root / "imports"
    if nested.is_dir():
        return nested
    return lift_root


def find_latest_3m_batch(lift_root: Path) -> Path:
    """Return latest imports/*/dataset dir that has *3_months*.csv.zip."""
    imports = resolve_imports_dir(lift_root)
    if not imports.is_dir():
        raise FileNotFoundError(f"no imports under {lift_root}")
    latest: Path | None = None
    for dataset in sorted(imports.glob("*/dataset")):
        if list(dataset.glob("*3_months*.csv.zip")):
            latest = dataset
    if latest is None:
        raise FileNotFoundError(f"no *3_months*.csv.zip under {imports}")
    return latest


def list_3m_zips(batch_dir: Path) -> list[Path]:
    return sorted(batch_dir.glob("*3_months*.csv.zip"))


def zip_payload_bytes(zip_path: Path) -> int:
    with zipfile.ZipFile(zip_path) as zf:
        return sum(i.file_size for i in zf.infolist())


def read_csv_header_from_zip(zip_path: Path) -> list[str]:
    with zipfile.ZipFile(zip_path) as zf:
        name = zf.namelist()[0]
        with zf.open(name) as fh:
            first = fh.readline().decode("utf-8-sig", errors="replace").strip("\r\n")
    return [c.strip() for c in first.split(",")]


def pre_ingest_gate(batch_dir: Path) -> dict:
    zips = list_3m_zips(batch_dir)
    if not zips:
        raise ValueError(f"no 3m zips in {batch_dir}")
    nonempty = [z for z in zips if zip_payload_bytes(z) > 0]
    if not nonempty:
        raise ValueError(f"all 3m zips empty in {batch_dir}")
    header = read_csv_header_from_zip(nonempty[0])
    if header != EXPECTED_HEADERS:
        raise ValueError(f"header mismatch: got {header!r}")
    return {
        "batch_dir": str(batch_dir),
        "zip_count": len(zips),
        "nonempty_zip_count": len(nonempty),
        "header_ok": True,
    }


def dq_null_check_sql(table: str = DEFAULT_TARGET_TABLE) -> str:
    parts = [
        f"SELECT COUNT(*) AS total,",
    ]
    for k in MANDATORY_SQL_KEYS:
        if k == "date_received":
            parts.append(f"SUM(CASE WHEN {k} IS NULL THEN 1 ELSE 0 END) AS null_{k},")
        else:
            parts.append(
                f"SUM(CASE WHEN {k} IS NULL OR TRIM(CAST({k} AS STRING)) = '' THEN 1 ELSE 0 END) AS null_{k},"
            )
    # drop trailing comma on last
    sql = " ".join(parts).rstrip(",") + f" FROM {table}"
    return sql


def spark_container_name(getenv=os.getenv) -> str:
    return (getenv("CCA_ICEBERG_SPARK_CONTAINER") or DEFAULT_SPARK_CONTAINER).strip()
