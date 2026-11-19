# M45-0001 / #320 — Raw Iceberg DDL + local start/stop design

## Goal
Create Iceberg `raw` namespace table templates for five slices + quarantine, and give operators `npm run local:containers:iceberg:{start,stop,status}` plus runbook steps.

## Decisions
1. Profile `iceberg=iceberg` in `CICD/Local/profiles.map` (named service; not in default sqlite profile).
2. DDL applied via SparkSQL against `demo` catalog (tabulario quickstart) creating namespace `raw`.
3. Source columns: 15 CFPB Lift headers as STRING (except `date_received` DATE) + reserved `consumer_complaint_narrative` STRING (empty for current exports) = 16 source; + 5 audit = 21 columns.
4. Partition: `months(date_received)`. Quarantine table: same schema without requiring non-null keys.
5. Runbook `docs/Runbooks/Localhost/3m-pgvector-chroma.md` §0.1 adds iceberg stop/start npm lines; Iceberg README mirrors npm commands.

## Out of scope
Hydrate data (#321), Airflow DAG (#322), count proof (#323).
