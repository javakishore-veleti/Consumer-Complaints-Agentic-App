# M17-0001 — Filter lands UTC import run; 3-month MIO ingest/index

## Decision
1. `filter_cfpb_3_months` uses `prepare_run_folder` like download: outputs under `…/imports/<YYYY-MM-DD-HH-MM-SS>/dataset/`, registers `dataset_import_runs` (staging → landed/failed).
2. Bind to **Customer complaints 3 months 2026**: `ingest_cfpb_imports_wrapper`, `index_cfpb_pgvector`, `index_cfpb_chroma`, `index_cfpb_redis` (reuse existing workflow rows; new `mios_workflows` rows only).
3. DB Ingest on that MIO uses wrapper + selected import run(s). No All-MIO required for this path.

## Non-goals
- Dataset tags (#247), Admin rename (#246), full runbook rewrite (#244).
