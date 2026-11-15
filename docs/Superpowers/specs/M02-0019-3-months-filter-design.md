# M02-0019 (#58) 3 months dataset: filter the All file by Date received

Decisions: D11, D42, D43, D44, D51, D54, D57, D62, D63, D67 and **D70** in `Middleware/ConsumerComplaintsHandsOn/DESIGN.md`. Decided without the user present (D70); review and reverse if needed.

**Numbering note:** On `origin/main` after #63 the next free decision is **D70**. This story claims **D70** for the 3-month filter workflow. If a parallel story needs a decision, it must take **D71+**.

## Goal

An Airflow DAG that derives the CFPB "last 3 months" dataset from the already-landed All zip by filtering on `Date received`. The whole file is read (it is not date-sorted). The workflow is registered in `app_workflows`, reuses D63 landing resolution and D67 status callbacks, and does not invent portal UI.

## Approaches considered

| | Approach | Trade-off |
|---|---|---|
| A | Hardcode All path + 3-month cutoff in the DAG | Fast; rejects D51 / D57 / D63 (catalog + env) |
| B | Separate dataset code + location for the 3-month slice | Clean catalog story later; extra seed and open "time window" item for this story |
| C (chosen) | One workflow `filter_cfpb_3_months` with `dataset_code: CFPB`; read All zip and write filtered zip under the same `local` landing (D63); window in `config.months` | Smallest MVP (D54); no new catalog rows; portal start (#42) already works once seeded |

## Decision D70 (summary)

1. **Workflow** `filter_cfpb_3_months`, `engine_type=apache_airflow`, `engine_workflow_id=filter_cfpb_3_months` (DAG id), seeded by Alembic `0009`.
2. **Config** (non-secret JSON):
   - `dataset_code` (required): `"CFPB"` — loads the dataset's `local` location like D63.
   - `months` (required): `3`.
   - `source_filename` (default `complaints.csv.zip`): All file under the landing dir (produced by `download_cfpb_all`).
   - `output_filename` (default `complaints_3_months.csv.zip`): filtered zip written beside the All file.
   - `date_column` (default `Date received`).
   - `expected_row_count` (optional int): when set, the filter task fails if the kept row count differs (ops check against the CFPB site figure). **Not seeded** — the public figure drifts; CI uses fixtures.
3. **Window:** keep rows whose `Date received` (parsed as `YYYY-MM-DD`) is on or after `as_of_date` minus `months` calendar months. `as_of_date` defaults to the UTC calendar date of the run; optional `dag_run.conf.as_of_date` (`YYYY-MM-DD`) overrides for reproducible tests/ops. Invalid/blank dates in a row are dropped (not kept).
4. **IO:** stream the CSV member inside the source zip with stdlib `zipfile` + `csv` (no pandas). Write a new zip containing one CSV member with the same basename as `output_filename` without `.zip` (or `complaints_3_months.csv` when the output ends in `.csv.zip`). Create parent dirs; replace atomically via a temp file in the landing dir.
5. **Landing:** resolve `LOCAL_DATA_PATH_*` exactly as D63 (`resolve_landing_dir` / env else Variable). **No http download in this DAG** — All must already be on disk.
6. **Run conf:** `{"execution_id": "<uuid>"}` required (D51). Optional `as_of_date`. Optional `mio_id` ignored for MVP.
7. **Callbacks (D67):** same topology as `download_cfpb_all` — `resolve_and_filter` reports `started` then filters; `notify_finished` with `trigger_rule=all_done` reports `completed` / `failed`. Reuse `ccaa.status_callback`.
8. **Helpers:** new `Middleware/Airflow-dags/ccaa/filter_by_date.py` (stdlib only). Reuse `ccaa.db_reader` for config + landing. **Must not import `app.*`.**
9. **Row-count acceptance:** the helper returns `rows_kept` (and `rows_read`). Unit tests assert fixture counts. Manual / ops: compare `rows_kept` to the CFPB site "Last 3 months" figure (DESIGN.md snapshot: **2,036,290** at decision time) or set `expected_row_count` when pinning a known export.

## Layout

| Path | Role |
|---|---|
| `Middleware/Airflow-dags/ccaa/filter_by_date.py` | Stream zip/CSV; calendar-month cutoff; write filtered zip |
| `Middleware/Airflow-dags/filter_cfpb_3_months.py` | DAG (`dag_id="filter_cfpb_3_months"`) + D67 tasks |
| `alembic/versions/0009_seed_filter_cfpb_3_months_workflow.py` | Seed `app_workflows` |
| `tests/test_ccaa_filter_by_date.py` | Unit tests (fixture zip, window, optional expected count) |
| `tests/test_filter_cfpb_3_months_dag_file.py` | Path / topology / no `app.` imports |
| `tests/test_schema.py` (+ list/postgres assertions) | Seed present; downgrade removes it |

## Runtime flow

```text
dag_run.conf.execution_id (+ optional as_of_date)
        │
        ▼
resolve_and_filter
        │  POST status=started (D67)
        │  CCA_DB_URL → load_execution_config → dataset_code, months, filenames
        │  load_dataset_locations → local env name → resolve_landing_dir
        │  filter_zip_by_date_received(source → output)
        │  optional expected_row_count check
        ▼
notify_finished (ALL_DONE) → completed | failed
```

### Helper contract

```python
def subtract_calendar_months(d: date, months: int) -> date: ...

@dataclass(frozen=True)
class FilterByDateResult:
    rows_read: int
    rows_kept: int
    cutoff: date
    as_of: date
    dest: Path

def filter_zip_by_date_received(
    source_zip: Path,
    dest_zip: Path,
    *,
    months: int,
    as_of: date,
    date_column: str = "Date received",
) -> FilterByDateResult:
    """Read every data row; keep Date received >= cutoff. Raises if source missing or column absent."""
```

## Seed (migration `0009`)

Fixed id: `uuid.uuid5(uuid.NAMESPACE_URL, "ccaa/m02-0019/filter_cfpb_3_months")` → `4d3f1ee0-0b02-51cb-8959-2499896cc20e`.

| Column | Value |
|---|---|
| workflow_name | `filter_cfpb_3_months` |
| engine_type | `apache_airflow` |
| engine_workflow_id | `filter_cfpb_3_months` |
| config | `{"dataset_code":"CFPB","months":3,"source_filename":"complaints.csv.zip","output_filename":"complaints_3_months.csv.zip","date_column":"Date received"}` |
| enabled | true |

## Tests

| Test | Asserts |
|---|---|
| Unit: cutoff math | `2026-11-15` − 3 months → `2026-08-15`; end-of-month clamp |
| Unit: filter | Fixture zip with in/out-of-window + bad dates → kept count and output CSV |
| Unit: expected count | When `expected_row_count` mismatches → raises |
| Path: DAG file | `dag_id`, `notify_finished`, `ALL_DONE`/`all_done`, status callback; no `from app.` |
| Schema: `0009` | Seed row present after upgrade; gone after downgrade to `0008` |
| List / Postgres | Seeded workflows include both `download_cfpb_all` and `filter_cfpb_3_months` (ordered by name) |

## Out of scope

- Portal UI / MIO time-window catalog modeling (still open in DESIGN.md).
- Downloading the All file (story #57).
- Changing D60 callback shape or volume fields.
- pandas / Spark / chunked parallel filter.
- Pinning `expected_row_count` in the seed (figure drifts).
