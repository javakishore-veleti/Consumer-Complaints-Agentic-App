# 2026-11-17 — Timestamped import runs + selective Mongo ingest

**Milestone:** M11 - Import runs and selective Mongo ingest  
**Status:** Design approved in chat (sections 1–2); awaiting written-spec review before implementation plans.

## Problem

1. Staging copies part zips **flat** into `LOCAL_DATA_PATH_CFPB` and **overwrites** on re-run — a later 3‑month (or any) batch clobbers the previous landing files.
2. There is no durable registry of “what was imported” vs “what was ingested to Mongo.”
3. Ingest today is “run `ingest_cfpb_all` against the flat landing,” not “operator selects one or more import runs.”
4. Iteration over multiple imports must live in **Airflow**, not Middleware.
5. Landing storage must stay **pluggable** later (local path today; S3 / file server / etc. later).

## Goals

- Each import/stage run creates a **UTC** folder `YYYY-MM-DD-HH-MM-SS` (name = **workflow start time**) under the landing root, with:
  - `_metadata/` — JSON describing the run and optional **source snapshot** window
  - `dataset/` — actual part files (`complaints_part_*.csv.zip` today)
- Optional **source snapshot start/end** (date + hour + minute) captured **when initiating the import/stage workflow**, with default rules below.
- Operational **import registry** table tracks each run and whether it has been ingested to Mongo.
- **Mongo ingest** start UI: list imports with checkboxes; already ingested → no checkbox / disabled; Middleware **and** DAGs reject re-ingest.
- Operator chooses **sequential (default)** or **parallel** when **initiating the Mongo ingest workflow**.
- Middleware starts a **wrapper DAG** with `{ import_ids[], mode }`; wrapper triggers a **core ingest DAG** once per import (one folder / location ref).

## Non-goals (this design)

- Implementing S3 / remote stores (only define location abstraction).
- Changing Intellect / vector index beyond “they still read Mongo after ingest.”
- Monolith zip + `filter_cfpb_3_months` as the primary localhost path (unchanged elsewhere).

## Decisions (locked)

| Topic | Choice |
|---|---|
| Run folder name | **A** — UTC `YYYY-MM-DD-HH-MM-SS` = **workflow start** of import/stage |
| Timestamps in metadata | **UTC** |
| Source snapshot fields | Optional start/end with HH:MM (SS optional in JSON as `:00` if UI has no seconds) |
| Snapshot defaults | See § Snapshot default rules |
| Ingest selection | UI multi-select of registry rows; not “silent latest” |
| Already ingested | Hide/disable checkbox; Middleware + DAG hard-reject |
| Orchestration | Wrapper DAG + core ingest DAG; iteration in Airflow |
| Sequential vs parallel | UI option on **Mongo ingest** start; **sequential default** |
| Storage | Registry stores `location_kind` + `location_ref` (`local_path` first) |

## Snapshot default rules

When initiating import/stage:

| Provided | Effective source window |
|---|---|
| Neither start nor end | Both = workflow start time (UTC) |
| End only | Start = end |
| Start only | End = now (workflow start / current UTC at initiation) |
| Both | Use both |

Folder name remains workflow start time regardless of snapshot fields.

## Landing layout (local today)

```text
LOCAL_DATA_PATH_CFPB/                    # landing root (env)
  2026-11-14-15-18-00/                   # UTC workflow start
    _metadata/
      import.json                        # see schema below
    dataset/
      complaints_part_001.csv.zip
      …
```

### `_metadata/import.json` (minimum)

```json
{
  "import_id": "<uuid>",
  "workflow_started_at": "2026-11-14T15:18:00Z",
  "workflow_completed_at": null,
  "source_snapshot_start": "2026-11-14T15:18:00Z",
  "source_snapshot_end": "2026-11-14T15:18:00Z",
  "location_kind": "local_path",
  "location_ref": "/absolute/…/LOCAL_DATA_PATH_CFPB/2026-11-14-15-18-00",
  "part_glob": "complaints_part_*.csv.zip",
  "part_count": 0
}
```

Update `workflow_completed_at`, `part_count`, and registry status when stage finishes (success/fail via existing callback patterns).

## Import registry (operational DB)

New admin-schema table (name TBD, e.g. `dataset_import_runs`):

| Column | Purpose |
|---|---|
| `id` | Stable id (UUID) — what UI/DAGs pass |
| `run_folder_name` | `YYYY-MM-DD-HH-MM-SS` |
| `location_kind` | `local_path` \| later `s3` \| … |
| `location_ref` | Opaque reference resolved by kind |
| `source_snapshot_start` / `source_snapshot_end` | UTC |
| `status` | `landed` \| `ingesting` \| `ingested` \| `failed` (exact enum in impl) |
| `workflow_started_at` / `workflow_completed_at` | UTC |
| `ingested_at` | UTC nullable |
| `mio_id` / `execution_id` | Optional links to existing catalog/exec log |
| `created_at` / `updated_at` | UTC |

**Ingest eligibility:** only rows not yet `ingested` (and not currently `ingesting`) may be selected.

## Import/stage flow

1. Operator starts import/stage workflow; optional snapshot start/end on that start form.
2. DAG (or first task) creates run folder + `_metadata` + `dataset`, inserts registry row (`landed` pending / in progress).
3. Stage copies parts from `CCA_CFPB_SPLIT_SOURCE_PATH` (or future source) into `dataset/`.
4. On success: finalize metadata + registry `landed`; on failure: `failed`.

## Mongo ingest flow

1. UI lists registry imports; checkboxes only for eligible rows; control for **sequential (default)** / **parallel**.
2. Middleware `POST` start (wrapper workflow): body includes `import_ids[]` + `mode`. Validate all ids exist and are eligible; else **422**.
3. Create exec log as today; start **wrapper DAG** with conf `{ execution_id, import_ids, mode }`.
4. Wrapper:
   - **sequential:** trigger core DAG per id, wait for each before next
   - **parallel:** trigger all core DAGs (respect Airflow pool/concurrency)
5. Core ingest DAG: resolve location → read `dataset/` parts → load Mongo; callback status; set registry `ingested` / `failed`. Re-check eligibility at start (reject if already ingested).

## Admin UI

- **Import/stage start:** optional snapshot datetime fields (date + HH:MM).
- **Mongo ingest start:** multi-select list + sequential/parallel (this workflow’s initiation UI — DB Ingest page preferred to match product split of Imports vs ingest).

## Middleware responsibilities

- Persist/list registry; enforce eligibility on ingest start.
- Pass ids + mode to wrapper only — **no** loop starting N core DAGs.
- Callbacks update exec/ingest logs **and** registry ingest fields.

## Airflow responsibilities

- Wrapper owns iteration and sequential/parallel behavior.
- Core owns one-import Mongo load.
- Both enforce “not already ingested” using registry (via API or read-only operational DB per existing D51 rules — prefer API callbacks for writes).

## Migration / compatibility

- Flat files already under landing are **out of band**; operators re-stage into a run folder or a one-time migration story (optional follow-up).
- Existing `ingest_cfpb_all` becomes core ingest (or is replaced by a new DAG id seeded in registry) — implementation plan chooses rename vs new id.

## Open items (small; resolve in plan)

1. Exact table/DAG/workflow ids and seed bindings to which MIO.
2. Whether `ingesting` locks a row against double-submit.
3. One-time migration of any flat `imports/*.zip` (yes/no).

## Approval

- Section 1 (landing + metadata + registry): approved in chat  
- Section 2 (UI + wrapper/core DAGs + reject rules): approved in chat  
- Written spec: **pending user review of this file**
