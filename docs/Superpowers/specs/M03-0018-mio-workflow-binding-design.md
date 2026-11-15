# M03-0018 (#141) MIO↔workflow binding: All MIO + non-misleading Imports picker

Decisions: D49, D57, D63, D66, D68, D70, D71, D72, D75, D79 and **D84** in `Middleware/ConsumerComplaintsHandsOn/DESIGN.md`. Next free decision after this story is **D85**.

## Goal

Stop showing every enabled workflow on every Imports MIO card. Operators must not see `download_cfpb_all` as if it were a 3-month download. Bind workflows to MIOs in **catalog data**, seed a dedicated **All** MIO for the All-file download, and enforce the binding in the API and portal.

## Context (already built)

| Piece | Where |
|---|---|
| MIOs are labels; no code may read the name for dataset/window | D57 |
| `download_cfpb_all` downloads full CFPB zip | D63 |
| `filter_cfpb_3_months` filters All zip → 3-month slice (no download) | D70 |
| Imports lists **all** enabled workflows on every accordion | D72 / #65 |
| “Attaching a workflow to a MIO” left open | D63 |

Seeded MIOs today: Customer complaints **3 / 6 / 9 / 12** months 2026. There is **no** All MIO. Only one filter workflow exists (`filter_cfpb_3_months`).

## Approaches considered

| | Approach | Trade-off |
|---|---|---|
| A | Portal filters options by parsing MIO **name** (e.g. “3 months” → filter) | Violates D57; fragile; still no All MIO |
| B (chosen) | Catalog join `mios_workflows`; status + start use it; seed All MIO + bindings | Correct domain model; closes D63; small schema + API + portal |
| C | Hard-code workflow ids in Angular environment | Faster UI-only; bypasses catalog; breaks Mongo/SQLite parity and D49 |

## Decision D84 (summary)

1. **Table `mios_workflows`** (admin schema): `id`, `mio_id`, `workflow_id`, `created_at`. Unique `(mio_id, workflow_id)`. No DB FKs (same DAO rules as `mios_datasets`, D57): parent MIO and workflow must exist; cannot delete a parent still linked.
2. **Semantics:** A MIO’s **allowed** workflows are the join rows. Empty set ⇒ that MIO cannot be started (operator sees empty picker / disabled Start). This is honest for 6/9/12 until filter DAGs exist — do **not** invent `filter_cfpb_6_months` etc. in this story.
3. **Seed (Alembic `0011` + Mongo bootstrap):**
   - MIO **Customer complaints all 2026** (stable UUID5 like other seeds) + `mios_datasets` to the same CFPB dataset/location pattern as the month MIOs.
   - Bind **All** MIO → `download_cfpb_all` only.
   - Bind **Customer complaints 3 months 2026** → `filter_cfpb_3_months` only.
   - Leave 6 / 9 / 12 with **no** `mios_workflows` rows.
4. **`GET /mios/status`:** each entry gains `allowed_workflows`: list of `{ id, workflow_name, engine_type, engine_workflow_id, enabled }` for that MIO’s join, **enabled workflows only**, ordered by `workflow_name`. Shape matches D66 list items (no `config`). Empty list when unbound.
5. **`POST /workflows/{workflow_id}/start` with `mio_id`:** after workflow/MIO validation, if the MIO has **zero** allowed workflows, or the requested workflow is **not** in its allowed set → `INVALID_INPUT` → HTTP **422** `invalid request`. When `mio_id` is omitted, behavior unchanged (no MIO binding check).
6. **Imports (portal):** picker options = that entry’s `allowed_workflows` (not the global `GET /workflows` list). Default = sole allowed row, else first by name. Start disabled when no allowed workflow or while running (existing D72 rules). Keep `data-testid`s. Global `listWorkflows` may remain unused on Imports or be dropped from Imports init — prefer **stop loading global workflows on Imports** once status carries the list (one less call).
7. **Does not** change DAG behavior, callback secret, or D57 “names are labels” — binding is data in `mios_workflows`, never derived from the MIO name string.
8. **D72 revision:** replace “picker uses every enabled workflow / default `download_cfpb_all` on every accordion” with “picker uses `allowed_workflows` from status (D84)”. Manual refresh / no polling unchanged.

## Data flow

```text
Operator opens Imports
  → GET /mios/status
  → each card: name + status + allowed_workflows[]
  → Start → POST /workflows/{id}/start { mio_id }
       → API checks mios_workflows
       → create ingest/exec → Airflow (unchanged)
```

## Tests

- Alembic/Mongo: All MIO exists; All → download only; 3 months → filter only; 6/9/12 → no join rows.
- `GET /mios/status`: All entry’s `allowed_workflows` names `download_cfpb_all`; 3-month names `filter_cfpb_3_months`; 6-month `[]`.
- Start: All + download → 202 (Airflow mocked); All + filter → 422; 3-month + download → 422; 6-month + any → 422.
- Portal: select options per MIO match fixture `allowed_workflows`; Start disabled when `[]`.
- Existing e2e/smoke docs: start **All** MIO with `download_cfpb_all` (or 3-month with filter) as the happy path example.

## Docs to update when built

| File | Change |
|---|---|
| `DESIGN.md` | D84 row; close D63 attach-open note; revise D72; catalog table list + open items |
| `ARCHITECTURE.md` | One line: MIO allowed workflows via `mios_workflows` |
| `Milestone_03.md` | Story #141 rows; next decision D85 |
| `docs/PRODUCT_FEATURES.md` | Imports: per-MIO workflows; All vs filter |
| `docs/local-admin-e2e-happy-path.md` | Start on All MIO (or 3-month + filter) |

## Out of scope

- New filter DAGs for 6 / 9 / 12 months.
- Admin CRUD UI for `mios_workflows` (seed + DAO only).
- Changing Airflow DAG code or download/filter logic.
- Polling, DB Ingest, cloud engines.
- Deriving windows from MIO names.

## Acceptance mapping

| Acceptance (issue) | Design section |
|---|---|
| D84 in DESIGN; D63/D72 updated | Decision D84 §1–8 |
| Alembic + Mongo seed | §3 |
| status `allowed_workflows` | §4 |
| start 422 unbound | §5 |
| Imports picker | §6 |
| Tests + docs | Tests / Docs |
