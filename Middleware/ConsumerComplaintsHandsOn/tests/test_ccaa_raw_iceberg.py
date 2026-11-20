"""Unit tests for Middleware/Airflow-dags/ccaa/raw_iceberg (M45-0003 / #322)."""

from __future__ import annotations

import csv
import io
import sys
import zipfile
from pathlib import Path

import pytest

from tests.conftest import REPO_ROOT

DAGS = REPO_ROOT / "Middleware" / "Airflow-dags"
if str(DAGS) not in sys.path:
    sys.path.insert(0, str(DAGS))

from ccaa import raw_iceberg as raw  # noqa: E402


def _write_zip(path: Path, rows: list[dict[str, str]], member: str = "part.csv") -> None:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=raw.EXPECTED_HEADERS)
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(member, buf.getvalue())


def test_find_latest_3m_batch(tmp_path: Path):
    older = tmp_path / "imports" / "2026-01-01" / "dataset"
    newer = tmp_path / "imports" / "2026-02-01" / "dataset"
    older.mkdir(parents=True)
    newer.mkdir(parents=True)
    _write_zip(older / "complaints_part_001_3_months.csv.zip", [])
    _write_zip(
        newer / "complaints_part_001_3_months.csv.zip",
        [
            {
                "Date received": "2026-11-01",
                "Product": "Credit card",
                "Sub-product": "",
                "Issue": "Billing",
                "Sub-issue": "",
                "Company public response": "",
                "Company": "Acme",
                "State": "CA",
                "ZIP code": "90001",
                "Tags": "",
                "Submitted via": "Web",
                "Date sent to company": "2026-11-02",
                "Company response to consumer": "Closed",
                "Timely response?": "Yes",
                "Complaint ID": "1",
            }
        ],
    )
    assert raw.find_latest_3m_batch(tmp_path) == newer
    # LOCAL_DATA_PATH_CFPB already points at imports/ (filter landing)
    assert raw.find_latest_3m_batch(tmp_path / "imports") == newer


def test_resolve_lift_root_prefers_variable_over_home_default(tmp_path: Path):
    landing = tmp_path / "imports"
    landing.mkdir()

    def getenv(_name: str):
        return None

    def get_variable(name: str):
        if name == "LOCAL_DATA_PATH_CFPB":
            return str(landing)
        raise KeyError(name)

    assert raw.resolve_lift_root(getenv=getenv, get_variable=get_variable) == landing


def test_pre_ingest_gate_ok(tmp_path: Path):
    batch = tmp_path / "dataset"
    batch.mkdir()
    row = {h: "" for h in raw.EXPECTED_HEADERS}
    row.update(
        {
            "Date received": "2026-11-01",
            "Product": "Credit card",
            "Company": "Acme",
            "Complaint ID": "9",
        }
    )
    _write_zip(batch / "complaints_part_001_3_months.csv.zip", [row])
    info = raw.pre_ingest_gate(batch)
    assert info["nonempty_zip_count"] == 1
    assert info["header_ok"] is True


def test_pre_ingest_gate_rejects_bad_header(tmp_path: Path):
    batch = tmp_path / "dataset"
    batch.mkdir()
    path = batch / "complaints_part_001_3_months.csv.zip"
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("x.csv", "a,b\n1,2\n")
    with pytest.raises(ValueError, match="header mismatch"):
        raw.pre_ingest_gate(batch)


def test_dq_null_check_sql_mentions_mandatory_keys():
    sql = raw.dq_null_check_sql("demo.raw.cfpb_complaints_3m")
    assert "demo.raw.cfpb_complaints_3m" in sql
    for k in raw.MANDATORY_SQL_KEYS:
        assert k in sql
