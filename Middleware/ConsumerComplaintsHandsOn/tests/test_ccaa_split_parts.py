"""Unit tests for Middleware/Airflow-dags/ccaa/split_parts.py (D91)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from tests.conftest import REPO_ROOT

DAGS = REPO_ROOT / "Middleware" / "Airflow-dags"
if str(DAGS) not in sys.path:
    sys.path.insert(0, str(DAGS))

from ccaa import split_parts as sp  # noqa: E402


def test_list_part_files_glob(tmp_path: Path):
    (tmp_path / "complaints_part_001.csv.zip").write_bytes(b"a")
    (tmp_path / "complaints_part_002.csv.zip").write_bytes(b"b")
    (tmp_path / "other.zip").write_bytes(b"x")
    paths = sp.list_part_files(tmp_path, source_filename_glob="complaints_part_*.csv.zip")
    assert [p.name for p in paths] == [
        "complaints_part_001.csv.zip",
        "complaints_part_002.csv.zip",
    ]


def test_list_part_files_explicit(tmp_path: Path):
    (tmp_path / "a.zip").write_bytes(b"a")
    paths = sp.list_part_files(tmp_path, source_filenames=["a.zip"])
    assert paths == [tmp_path / "a.zip"]


def test_list_part_files_missing_raises(tmp_path: Path):
    with pytest.raises(FileNotFoundError, match="missing part"):
        sp.list_part_files(tmp_path, source_filenames=["nope.zip"])


def test_stage_parts_from_dir_copies(tmp_path: Path):
    src = tmp_path / "src"
    landing = tmp_path / "landing"
    src.mkdir()
    (src / "complaints_part_001.csv.zip").write_bytes(b"one")
    (src / "complaints_part_002.csv.zip").write_bytes(b"two")
    out = sp.stage_parts_from_dir(src, landing)
    assert len(out) == 2
    assert (landing / "complaints_part_001.csv.zip").read_bytes() == b"one"
    assert (landing / "complaints_part_002.csv.zip").read_bytes() == b"two"


def test_resolve_named_dir_requires_value(tmp_path: Path):
    with pytest.raises(ValueError, match="CCA_CFPB_SPLIT_SOURCE_PATH"):
        sp.resolve_named_dir(
            "CCA_CFPB_SPLIT_SOURCE_PATH",
            getenv=lambda k, default=None: default,
            get_variable=lambda k: (_ for _ in ()).throw(KeyError(k)),
        )
    got = sp.resolve_named_dir(
        "CCA_CFPB_SPLIT_SOURCE_PATH",
        getenv=lambda k, default=None: str(tmp_path) if k == "CCA_CFPB_SPLIT_SOURCE_PATH" else default,
    )
    assert got == tmp_path
