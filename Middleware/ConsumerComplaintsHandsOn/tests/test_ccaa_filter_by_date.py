"""Unit tests for Middleware/Airflow-dags/ccaa/filter_by_date (D70)."""

from __future__ import annotations

import csv
import io
import sys
import zipfile
from datetime import date
from pathlib import Path

import pytest

from tests.conftest import REPO_ROOT

DAGS = REPO_ROOT / "Middleware" / "Airflow-dags"
if str(DAGS) not in sys.path:
    sys.path.insert(0, str(DAGS))

from ccaa import filter_by_date as filter_mod  # noqa: E402


def _write_zip(path: Path, rows: list[dict[str, str]], member: str = "complaints.csv") -> None:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=["Complaint ID", "Date received", "Product"])
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(member, buf.getvalue())


def test_subtract_calendar_months_basic_and_end_of_month():
    assert filter_mod.subtract_calendar_months(date(2026, 11, 15), 3) == date(2026, 8, 15)
    assert filter_mod.subtract_calendar_months(date(2026, 3, 31), 1) == date(2026, 2, 28)
    assert filter_mod.subtract_calendar_months(date(2026, 1, 31), 1) == date(2025, 12, 31)


def test_filter_keeps_only_rows_in_window(tmp_path: Path):
    source = tmp_path / "complaints.csv.zip"
    dest = tmp_path / "complaints_3_months.csv.zip"
    _write_zip(
        source,
        [
            {"Complaint ID": "1", "Date received": "2026-08-15", "Product": "keep-boundary"},
            {"Complaint ID": "2", "Date received": "2026-08-14", "Product": "drop-before"},
            {"Complaint ID": "3", "Date received": "2026-11-01", "Product": "keep-recent"},
            {"Complaint ID": "4", "Date received": "", "Product": "drop-blank"},
            {"Complaint ID": "5", "Date received": "not-a-date", "Product": "drop-bad"},
        ],
    )
    result = filter_mod.filter_zip_by_date_received(
        source,
        dest,
        months=3,
        as_of=date(2026, 11, 15),
    )
    assert result.rows_read == 5
    assert result.rows_kept == 2
    assert result.cutoff == date(2026, 8, 15)
    assert result.dest == dest
    assert dest.is_file()

    with zipfile.ZipFile(dest) as zf:
        assert zf.namelist() == ["complaints_3_months.csv"]
        with zf.open("complaints_3_months.csv") as raw:
            text = io.TextIOWrapper(raw, encoding="utf-8")
            kept = list(csv.DictReader(text))
    assert [r["Complaint ID"] for r in kept] == ["1", "3"]


def test_filter_missing_source_raises(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        filter_mod.filter_zip_by_date_received(
            tmp_path / "missing.zip",
            tmp_path / "out.zip",
            months=3,
            as_of=date(2026, 11, 15),
        )


def test_filter_missing_date_column_raises(tmp_path: Path):
    source = tmp_path / "in.zip"
    with zipfile.ZipFile(source, "w") as zf:
        zf.writestr("complaints.csv", "Complaint ID,Product\n1,x\n")
    with pytest.raises(ValueError, match="Date received"):
        filter_mod.filter_zip_by_date_received(
            source,
            tmp_path / "out.csv.zip",
            months=3,
            as_of=date(2026, 11, 15),
        )


def test_assert_expected_row_count():
    filter_mod.assert_expected_row_count(10, 10)
    with pytest.raises(ValueError, match="expected_row_count"):
        filter_mod.assert_expected_row_count(9, 10)


def test_list_filter_inputs_single_zip_file(tmp_path: Path):
    source = tmp_path / "complaints.csv.zip"
    _write_zip(source, [{"Complaint ID": "1", "Date received": "2026-11-01", "Product": "x"}])
    assert filter_mod.list_filter_inputs(source) == [source]


def test_list_filter_inputs_directory_collects_csv_and_zip(tmp_path: Path):
    folder = tmp_path / "parts"
    folder.mkdir()
    z1 = folder / "complaints_part_001.csv.zip"
    z2 = folder / "other.zip"
    c1 = folder / "plain.csv"
    (folder / "readme.txt").write_text("skip", encoding="utf-8")
    (folder / "nested").mkdir()
    (folder / "nested" / "skip.csv").write_text("a,b\n1,2\n", encoding="utf-8")
    _write_zip(z1, [{"Complaint ID": "1", "Date received": "2026-11-01", "Product": "a"}])
    _write_zip(z2, [{"Complaint ID": "2", "Date received": "2026-11-02", "Product": "b"}])
    c1.write_text(
        "Complaint ID,Date received,Product\n3,2026-11-03,c\n",
        encoding="utf-8",
    )
    got = filter_mod.list_filter_inputs(folder)
    assert got == sorted([z1, z2, c1])


def test_list_filter_inputs_empty_dir_raises(tmp_path: Path):
    empty = tmp_path / "empty"
    empty.mkdir()
    with pytest.raises(FileNotFoundError):
        filter_mod.list_filter_inputs(empty)


def test_filter_path_handles_plain_csv(tmp_path: Path):
    source = tmp_path / "plain.csv"
    source.write_text(
        "Complaint ID,Date received,Product\n"
        "1,2026-08-15,keep\n"
        "2,2026-08-14,drop\n",
        encoding="utf-8",
    )
    dest = tmp_path / "plain_3_months.csv.zip"
    result = filter_mod.filter_path_by_date_received(
        source,
        dest,
        months=3,
        as_of=date(2026, 11, 15),
    )
    assert result.rows_kept == 1
    assert dest.is_file()
