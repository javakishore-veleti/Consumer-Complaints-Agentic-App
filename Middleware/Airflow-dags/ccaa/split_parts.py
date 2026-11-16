"""CFPB split-part landing helpers (D91). No app.* imports."""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Callable, Iterable, Sequence


DEFAULT_PART_GLOB = "complaints_part_*.csv.zip"
DEFAULT_STAGE_FROM_ENV = "CCA_CFPB_SPLIT_SOURCE_PATH"


def _first_nonblank(*values: str | None) -> str | None:
    for v in values:
        if v is not None and str(v).strip():
            return str(v).strip()
    return None


def resolve_named_dir(
    env_var_name: str,
    *,
    getenv: Callable[..., str | None] = os.getenv,
    get_variable: Callable[[str], str] | None = None,
) -> Path:
    name = (env_var_name or "").strip()
    if not name:
        raise ValueError("env_var_name is required")
    value = _first_nonblank(getenv(name), None)
    if value is None and get_variable is not None:
        try:
            value = _first_nonblank(get_variable(name))
        except Exception:
            value = None
    if not value:
        raise ValueError(f"{name} is required (env or Airflow Variable)")
    path = Path(value)
    if not path.is_dir():
        raise FileNotFoundError(f"{name} is not a directory: {path}")
    return path


def list_part_files(
    landing: Path,
    *,
    source_filenames: Sequence[str] | None = None,
    source_filename_glob: str | None = None,
    source_filename: str | None = None,
) -> list[Path]:
    """Resolve zip parts under landing. Prefer explicit list, then glob, then single name."""
    landing = Path(landing)
    if source_filenames:
        paths = [landing / str(n).strip() for n in source_filenames if str(n).strip()]
    elif source_filename_glob and str(source_filename_glob).strip():
        paths = sorted(landing.glob(str(source_filename_glob).strip()))
    elif source_filename and str(source_filename).strip():
        paths = [landing / str(source_filename).strip()]
    else:
        paths = sorted(landing.glob(DEFAULT_PART_GLOB))
    missing = [p for p in paths if not p.is_file()]
    if missing:
        raise FileNotFoundError(
            "missing part file(s): " + ", ".join(str(p) for p in missing)
        )
    if not paths:
        raise FileNotFoundError(f"no part files under {landing}")
    return paths


def stage_parts_from_dir(
    source_dir: Path,
    landing: Path,
    *,
    source_filenames: Sequence[str] | None = None,
    source_filename_glob: str = DEFAULT_PART_GLOB,
) -> list[Path]:
    """Copy matching part zips from source_dir into landing (overwrite)."""
    source_dir = Path(source_dir)
    landing = Path(landing)
    landing.mkdir(parents=True, exist_ok=True)
    if source_filenames:
        names = [str(n).strip() for n in source_filenames if str(n).strip()]
        sources = [source_dir / n for n in names]
    else:
        sources = sorted(source_dir.glob(source_filename_glob or DEFAULT_PART_GLOB))
    if not sources:
        raise FileNotFoundError(
            f"no parts matching {source_filename_glob!r} under {source_dir}"
        )
    missing = [p for p in sources if not p.is_file()]
    if missing:
        raise FileNotFoundError(
            "missing source part(s): " + ", ".join(str(p) for p in missing)
        )
    out: list[Path] = []
    for src in sources:
        dest = landing / src.name
        shutil.copy2(src, dest)
        out.append(dest)
    return out


def stage_parts_from_urls(
    urls: Iterable[str],
    landing: Path,
    *,
    download: Callable[[str, Path], Path],
) -> list[Path]:
    """Download each URL into landing using basename of the URL path."""
    from urllib.parse import urlparse

    landing = Path(landing)
    landing.mkdir(parents=True, exist_ok=True)
    out: list[Path] = []
    for raw in urls:
        url = str(raw).strip()
        if not url:
            continue
        name = Path(urlparse(url).path).name or "part.csv.zip"
        dest = landing / name
        download(url, dest)
        out.append(dest)
    if not out:
        raise ValueError("source_urls is empty")
    return out
