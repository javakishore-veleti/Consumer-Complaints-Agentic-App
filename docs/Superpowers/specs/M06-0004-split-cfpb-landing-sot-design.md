# M06-0004 / M06-0005 / M06-0006 (#172 / #173 / #174) Split CFPB landing + SoT ingest

## Decisions (D91)

1. **Split parts replace the monolith for All download/ingest.** Default pattern: `complaints_part_*.csv.zip` under catalog landing `LOCAL_DATA_PATH_CFPB`. No hardcoded Downloads paths.
2. **Stage-first for local.** `download_cfpb_all` with `source_mode=split` copies matching parts from env **`CCA_CFPB_SPLIT_SOURCE_PATH`** into the landing dir (or downloads each URL in optional `source_urls`). Monolith HTTP download remains available when `source_mode=monolith` (or unset + no stage/urls).
3. **Ingest loops parts.** `ingest_cfpb_all` resolves files via `source_filenames` list, else `source_filename_glob`, else single `source_filename` (legacy). Reuses `ingest_complaints_zip` per file; sums `rows_loaded` / `batch_count`.
4. **Seeds:** Alembic `0017` + Mongo bootstrap update download/ingest configs; seed AppEndpoint `cfpb_stage_split_to_local` (`CCA_CFPB_SPLIT_SOURCE_PATH` → `LOCAL_DATA_PATH_CFPB`). Upsert-list the new env name.
5. **Out of scope:** filter_cfpb_3_months still uses monolith `complaints.csv.zip`; pgvector/PySpark (M07); retrieval ladder (M08).

## Acceptance

- Unit tests for list/stage helpers and multi-zip ingest without the full 19M corpus.
- Schema tests assert split config + new AppEndpoint.
- Paths only via env/catalog names.
