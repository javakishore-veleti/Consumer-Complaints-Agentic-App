# M04-0013 (#159) Register ingest workflow and MIO binding

## Goal

Seed `ingest_cfpb_all` in `app_workflows` and bind **All 2026** MIO via `mios_workflows` so DB Ingest (#160) can start it. Alembic `0013` + Mongo bootstrap parity.

## Seed

| Entity | UUID5 name | Id |
|---|---|---|
| Workflow | `ccaa/m04-0013/ingest_cfpb_all` | `0064095f-9f8e-5f09-94cf-3b4fe28e2b33` |
| Binding | `ccaa/m04-0013/mios-workflows-all-ingest` | `251b44d2-9aea-5d9d-b1a0-0816e8db3f80` |

Config: `{"dataset_code":"CFPB","source_filename":"complaints.csv.zip","batch_size":500}`.

Bind All MIO only (not 3 months — different landing filename).

## Out of scope

Admin DB Ingest UI (#160), AppEndpoint resolution (#161).
