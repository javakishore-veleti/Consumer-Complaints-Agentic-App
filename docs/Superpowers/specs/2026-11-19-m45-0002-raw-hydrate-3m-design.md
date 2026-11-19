# M45-0002 / #321 — PySpark Lift→Raw hydrate (3m) design

## Goal
Hydrate `demo.raw.cfpb_complaints_3m` from Lift Zone `*_3_months.csv.zip` without re-download.

## Pipeline
1. Resolve latest `/lift/imports/*/dataset` batch containing `*3_months*.csv.zip`.
2. Unzip non-empty parts into ephemeral `/tmp/cca_raw_stage/<run_id>/`.
3. Spark reads CSVs (multiLine, escape quotes); map 15 CFPB headers → snake_case; add empty `consumer_complaint_narrative`; parse `date_received`.
4. Append audit: `_dataset_slice=3m`, `_source_zip_file`, `_ingest_ts`, `_airflow_run_id`, `_row_hash` (sha2 of source cols).
5. Quarantine rows with null/blank `complaint_id` or `date_received` or `product` or `company` → `demo.raw.cfpb_complaints_quarantine`.
6. Good rows: dynamic partition overwrite into `demo.raw.cfpb_complaints_3m`.

## Operator entry
`npm run local:iceberg:hydrate-raw-3m` (requires iceberg stack up + DDL applied).
