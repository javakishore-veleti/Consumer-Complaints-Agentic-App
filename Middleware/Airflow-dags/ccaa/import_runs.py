"""UTC import run folders + snapshot defaults (M11). No app.* imports."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

FOLDER_FMT = "%Y-%m-%d-%H-%M-%S"
PART_GLOB = "complaints_part_*.csv.zip"
LOCATION_LOCAL_PATH = "local_path"
METADATA_NAME = "import.json"


def ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def parse_utc(value: str | datetime | None) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return ensure_utc(value)
    text = str(value).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    return ensure_utc(datetime.fromisoformat(text))


def folder_name_for(workflow_started_at: datetime) -> str:
    return ensure_utc(workflow_started_at).strftime(FOLDER_FMT)


def resolve_snapshot_window(
    workflow_started_at: datetime,
    *,
    source_snapshot_start: datetime | str | None = None,
    source_snapshot_end: datetime | str | None = None,
) -> tuple[datetime, datetime]:
    """Apply M11 snapshot default rules. Folder name still uses workflow_started_at."""
    started = ensure_utc(workflow_started_at)
    start = parse_utc(source_snapshot_start)
    end = parse_utc(source_snapshot_end)
    if start is None and end is None:
        return started, started
    if start is None:
        return end, end  # type: ignore[return-value]
    if end is None:
        return start, started
    return start, end


def prepare_run_folder(landing_root: Path, workflow_started_at: datetime) -> Path:
    """Create `<landing>/<UTC>/_metadata` and `dataset`. Returns the run folder."""
    root = Path(landing_root)
    run = root / folder_name_for(workflow_started_at)
    (run / "_metadata").mkdir(parents=True, exist_ok=True)
    (run / "dataset").mkdir(parents=True, exist_ok=True)
    return run


def dataset_dir(run_folder: Path) -> Path:
    return Path(run_folder) / "dataset"


def metadata_path(run_folder: Path) -> Path:
    return Path(run_folder) / "_metadata" / METADATA_NAME


def build_import_metadata(
    *,
    import_id: str | None = None,
    workflow_started_at: datetime,
    source_snapshot_start: datetime,
    source_snapshot_end: datetime,
    location_ref: str,
    location_kind: str = LOCATION_LOCAL_PATH,
    part_glob: str = PART_GLOB,
    part_count: int = 0,
    workflow_completed_at: datetime | None = None,
) -> dict[str, Any]:
    def _iso(value: datetime | None) -> str | None:
        if value is None:
            return None
        return ensure_utc(value).strftime("%Y-%m-%dT%H:%M:%SZ")

    return {
        "import_id": import_id or str(uuid4()),
        "workflow_started_at": _iso(workflow_started_at),
        "workflow_completed_at": _iso(workflow_completed_at),
        "source_snapshot_start": _iso(source_snapshot_start),
        "source_snapshot_end": _iso(source_snapshot_end),
        "location_kind": location_kind,
        "location_ref": location_ref,
        "part_glob": part_glob,
        "part_count": int(part_count),
    }


def write_import_metadata(run_folder: Path, payload: dict[str, Any]) -> Path:
    path = metadata_path(run_folder)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def read_import_metadata(run_folder: Path) -> dict[str, Any]:
    return json.loads(metadata_path(run_folder).read_text(encoding="utf-8"))
