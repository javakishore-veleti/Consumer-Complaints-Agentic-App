"""Filter a zipped CFPB CSV by Date received (calendar-month window). Stdlib only."""

from __future__ import annotations

import calendar
import csv
import io
import zipfile
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path


@dataclass(frozen=True)
class FilterByDateResult:
    rows_read: int
    rows_kept: int
    cutoff: date
    as_of: date
    dest: Path


def subtract_calendar_months(d: date, months: int) -> date:
    if months < 0:
        raise ValueError("months must be >= 0")
    year = d.year
    month = d.month - months
    while month <= 0:
        month += 12
        year -= 1
    day = min(d.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def _parse_received(value: str) -> date | None:
    text = (value or "").strip()
    if not text:
        return None
    # CFPB uses YYYY-MM-DD; tolerate a trailing time fragment.
    head = text[:10]
    try:
        return datetime.strptime(head, "%Y-%m-%d").date()
    except ValueError:
        return None


def _first_csv_member(zf: zipfile.ZipFile) -> str:
    names = [n for n in zf.namelist() if not n.endswith("/") and n.lower().endswith(".csv")]
    if not names:
        raise ValueError("zip has no CSV member")
    return names[0]


def _member_name_for_dest(dest_zip: Path) -> str:
    name = dest_zip.name
    if name.endswith(".csv.zip"):
        return name[: -len(".zip")]
    if name.endswith(".zip"):
        return f"{name[:-4]}.csv"
    return f"{name}.csv"


def filter_zip_by_date_received(
    source_zip: Path,
    dest_zip: Path,
    *,
    months: int,
    as_of: date,
    date_column: str = "Date received",
) -> FilterByDateResult:
    if months < 1:
        raise ValueError("months must be >= 1")
    if not source_zip.is_file():
        raise FileNotFoundError(f"source zip not found: {source_zip}")

    cutoff = subtract_calendar_months(as_of, months)
    dest_zip.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest_zip.with_name(f".{dest_zip.name}.tmp")
    if tmp.exists():
        tmp.unlink()

    rows_read = 0
    rows_kept = 0
    member_out = _member_name_for_dest(dest_zip)

    try:
        with zipfile.ZipFile(source_zip, "r") as zin, zipfile.ZipFile(
            tmp, "w", compression=zipfile.ZIP_DEFLATED
        ) as zout:
            member_in = _first_csv_member(zin)
            with zin.open(member_in, "r") as raw_in:
                text_in = io.TextIOWrapper(raw_in, encoding="utf-8", newline="")
                reader = csv.DictReader(text_in)
                if reader.fieldnames is None or date_column not in reader.fieldnames:
                    raise ValueError(f"CSV missing required column: {date_column}")
                with zout.open(member_out, "w") as raw_out:
                    text_out = io.TextIOWrapper(raw_out, encoding="utf-8", newline="")
                    writer = csv.DictWriter(text_out, fieldnames=reader.fieldnames)
                    writer.writeheader()
                    for row in reader:
                        rows_read += 1
                        received = _parse_received(row.get(date_column, ""))
                        if received is None or received < cutoff:
                            continue
                        writer.writerow(row)
                        rows_kept += 1
                    text_out.flush()
                    text_out.detach()
        tmp.replace(dest_zip)
    except Exception:
        if tmp.exists():
            tmp.unlink()
        raise

    return FilterByDateResult(
        rows_read=rows_read,
        rows_kept=rows_kept,
        cutoff=cutoff,
        as_of=as_of,
        dest=dest_zip,
    )


def assert_expected_row_count(rows_kept: int, expected_row_count: int) -> None:
    if rows_kept != expected_row_count:
        raise ValueError(
            f"rows_kept={rows_kept} does not match expected_row_count={expected_row_count}"
        )


def _is_filter_input(path: Path) -> bool:
    name = path.name.lower()
    return name.endswith(".csv") or name.endswith(".zip")


def list_filter_inputs(path: Path) -> list[Path]:
    """Return input files: one file, or every *.csv / *.zip in a directory (non-recursive)."""
    if path.is_file():
        if not _is_filter_input(path):
            raise ValueError(f"unsupported filter input file: {path}")
        return [path]
    if path.is_dir():
        found = sorted(p for p in path.iterdir() if p.is_file() and _is_filter_input(p))
        if not found:
            raise FileNotFoundError(f"no .csv or .zip files in folder: {path}")
        return found
    raise FileNotFoundError(f"filter input path not found: {path}")


def filtered_output_name(source: Path) -> str:
    """Map an input basename to a zipped filtered output name under landing."""
    name = source.name
    lower = name.lower()
    if lower.endswith(".csv.zip"):
        stem = name[: -len(".csv.zip")]
        return f"{stem}_3_months.csv.zip"
    if lower.endswith(".zip"):
        stem = name[: -len(".zip")]
        return f"{stem}_3_months.csv.zip"
    if lower.endswith(".csv"):
        stem = name[: -len(".csv")]
        return f"{stem}_3_months.csv.zip"
    return f"{name}_3_months.csv.zip"


def filter_path_by_date_received(
    source: Path,
    dest_zip: Path,
    *,
    months: int,
    as_of: date,
    date_column: str = "Date received",
) -> FilterByDateResult:
    """Filter a .zip (CSV inside) or a plain .csv into dest_zip."""
    if source.is_file() and source.name.lower().endswith(".csv") and not source.name.lower().endswith(
        ".csv.zip"
    ):
        # Plain CSV: wrap as a one-member zip then reuse zip filter.
        tmp_zip = dest_zip.parent / f".{source.stem}.src.zip"
        if tmp_zip.exists():
            tmp_zip.unlink()
        try:
            with zipfile.ZipFile(tmp_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
                zf.write(source, arcname=source.name)
            return filter_zip_by_date_received(
                tmp_zip,
                dest_zip,
                months=months,
                as_of=as_of,
                date_column=date_column,
            )
        finally:
            if tmp_zip.exists():
                tmp_zip.unlink()
    return filter_zip_by_date_received(
        source,
        dest_zip,
        months=months,
        as_of=as_of,
        date_column=date_column,
    )
