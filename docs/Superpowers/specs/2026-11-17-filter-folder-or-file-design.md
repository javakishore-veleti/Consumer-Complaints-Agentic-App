# M10-0023 (#238) — filter_cfpb_3_months: folder or single file

## Goal

Airflow DAG `filter_cfpb_3_months` must accept either a **directory** or a **specific `.zip` / `.csv` file**, detect which at runtime, and filter by `Date received` (last N months, default 3).

## Behavior

1. Resolve input path (in order):
   - workflow `config.source_path` if set
   - else env/Airflow Variable named by `config.source_path_env` (default `CCA_CFPB_SPLIT_SOURCE_PATH`)
   - else `LOCAL_DATA_PATH_CFPB` / `config.source_filename` (legacy fallback, default `complaints.csv.zip`)
2. **If path is a file** (`.csv` or `.zip`): filter that one file.
3. **If path is a directory**: non-recursively take every `*.csv` and `*.zip` (including `*.csv.zip`); ignore other names and subfolders.
4. Write one filtered `*_3_months.csv.zip` per input under the landing dir (`LOCAL_DATA_PATH_CFPB`).
5. Empty folder or missing path → fail with a clear error.

## Out of scope

- Changing MIO bindings / Admin UI
- Recursive directory walk
- Non-CSV zip members beyond the existing “first CSV in zip” rule

## Approved by

User (2026-11-17): Airflow checks folder vs file and behaves accordingly; inputs are `.zip` or `.csv`.
