"""Unit tests for Middleware/Airflow-dags/ccaa/import_runs.py (M11)."""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path

from tests.conftest import REPO_ROOT

DAGS = REPO_ROOT / "Middleware" / "Airflow-dags"
if str(DAGS) not in sys.path:
    sys.path.insert(0, str(DAGS))

from ccaa import import_runs as ir

STARTED = datetime(2026, 11, 14, 15, 18, 0, tzinfo=UTC)


def test_folder_name_is_utc_workflow_start():
    assert ir.folder_name_for(STARTED) == "2026-11-14-15-18-00"


def test_snapshot_defaults_neither():
    assert ir.resolve_snapshot_window(STARTED) == (STARTED, STARTED)


def test_snapshot_end_only():
    end = datetime(2026, 11, 1, 12, 0, tzinfo=UTC)
    assert ir.resolve_snapshot_window(STARTED, source_snapshot_end=end) == (end, end)


def test_snapshot_start_only():
    start = datetime(2026, 10, 1, 0, 0, tzinfo=UTC)
    assert ir.resolve_snapshot_window(STARTED, source_snapshot_start=start) == (start, STARTED)


def test_snapshot_both():
    start = datetime(2026, 10, 1, 0, 0, tzinfo=UTC)
    end = datetime(2026, 11, 1, 0, 0, tzinfo=UTC)
    assert ir.resolve_snapshot_window(
        STARTED, source_snapshot_start=start, source_snapshot_end=end
    ) == (start, end)


def test_prepare_run_folder_layout(tmp_path: Path):
    run = ir.prepare_run_folder(tmp_path, STARTED)
    assert run.name == "2026-11-14-15-18-00"
    assert (run / "_metadata").is_dir()
    assert (run / "dataset").is_dir()
    meta = ir.build_import_metadata(
        import_id="abc",
        workflow_started_at=STARTED,
        source_snapshot_start=STARTED,
        source_snapshot_end=STARTED,
        location_ref=str(run),
    )
    path = ir.write_import_metadata(run, meta)
    assert path.name == "import.json"
    loaded = ir.read_import_metadata(run)
    assert loaded["import_id"] == "abc"
    assert loaded["part_count"] == 0
