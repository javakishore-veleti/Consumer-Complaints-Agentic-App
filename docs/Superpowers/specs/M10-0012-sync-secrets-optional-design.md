# M10-0012 (#219) Sync secrets optional upsert names

## Problem
`POST /management/airflow/upsert-secrets` returns HTTP 422 when any listed name is empty in the process env. Localhost SQLite leaves `CCA_DB_URL` unset; split staging may leave `CCA_CFPB_SPLIT_SOURCE_PATH` unset — Sync fails even when required secrets are present.

## Decision
1. `Airflow_Variables_Upsert.txt` supports a section marker `# optional` (case-insensitive). Names **after** that marker are optional.
2. Empty env for an **optional** name → outcome `skipped` (not `missing`); does **not** fail the Sync.
3. Empty env for a **required** name (before `# optional`) → outcome `missing` → HTTP 422 (unchanged).
4. Present optional names still upsert like required ones (`created` / `updated`).
