"""Unit tests for Middleware/Airflow-dags/ccaa/mongo_ingest.py (D86)."""

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

from ccaa import mongo_ingest as mi  # noqa: E402


class _FakeColl:
    def __init__(self) -> None:
        self.ops: list = []
        self.indexes: list = []

    def create_index(self, keys, **kwargs):
        self.indexes.append((keys, kwargs))
        return "Complaint ID_1"

    def bulk_write(self, ops, ordered=False):
        self.ops.extend(ops)

        class Res:
            upserted_count = len(ops)
            modified_count = 0

        return Res()


def _write_zip(path: Path, rows: list[dict]) -> None:
    buf = io.StringIO()
    fields = list(rows[0].keys())
    w = csv.DictWriter(buf, fieldnames=fields)
    w.writeheader()
    w.writerows(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("complaints.csv", buf.getvalue())


def test_ingest_zip_upserts_by_complaint_id(tmp_path: Path):
    zpath = tmp_path / "complaints.csv.zip"
    _write_zip(
        zpath,
        [
            {"Complaint ID": "a1", "Product": "Credit"},
            {"Complaint ID": "a2", "Product": "Mortgage"},
        ],
    )
    coll = _FakeColl()
    result = mi.ingest_complaints_zip(
        zpath,
        coll,
        batch_size=1,
        ensure_index=True,
    )
    assert result.rows_loaded == 2
    assert result.batch_count == 2
    assert coll.indexes and coll.indexes[0][0] == "Complaint ID"
    assert coll.indexes[0][1].get("unique") is True
    assert coll.indexes[0][1].get("name") == "uniq_complaint_id"
    assert len(coll.ops) == 2
    op0 = coll.ops[0]
    filt = getattr(op0, "_filter", None)
    doc = getattr(op0, "doc", None) or getattr(op0, "_doc", None)
    assert filt == {"Complaint ID": "a1"}
    assert doc["_id"] == "a1"


def test_ingest_requires_complaint_id_column(tmp_path: Path):
    zpath = tmp_path / "bad.csv.zip"
    _write_zip(zpath, [{"Product": "x"}])
    with pytest.raises(ValueError, match="Complaint ID"):
        mi.ingest_complaints_zip(zpath, _FakeColl(), batch_size=10)


def test_resolve_complaints_mongo_url_prefers_env():
    assert (
        mi.resolve_complaints_mongo_url(
            getenv=lambda k, default=None: "mongodb://env/db" if k == "CCA_MONGO_COMPLAINTS_URL" else default,
            get_variable=lambda k: "mongodb://var/db",
        )
        == "mongodb://env/db"
    )


def test_ingest_complaints_parts_sums_batches(tmp_path: Path):
    z1 = tmp_path / "complaints_part_001.csv.zip"
    z2 = tmp_path / "complaints_part_002.csv.zip"
    _write_zip(z1, [{"Complaint ID": "a1", "Product": "Credit"}])
    _write_zip(z2, [{"Complaint ID": "a2", "Product": "Mortgage"}])
    coll = _FakeColl()
    result = mi.ingest_complaints_parts([z1, z2], coll, batch_size=10)
    assert result.rows_loaded == 2
    assert result.batch_count == 2
    assert len(coll.indexes) == 1
    assert len(coll.ops) == 2
