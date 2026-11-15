# M02-0026 (#65) Start workflow button and status refresh

Decisions: D5, D54, D61, D65, D66, D68, D69, D71 and **D72** in `Middleware/ConsumerComplaintsHandsOn/DESIGN.md`. Decided without the user present (D72); review and reverse if needed.

**Numbering note:** On `origin/main` after #64 the next free decision is **D72**. Do not reuse D70 (3-month filter, #58) or D71 (MIO accordions, #64).

## Goal

On Imports MIO accordions (#64 / D71), add the smallest usable start-workflow control that calls `POST /workflows/{id}/start` (#42 / D68) with the accordion's `mio_id`, lists workflows via `GET /workflows` (#84 / D66) when a choice is needed, then refreshes accordion status via `GET /mios/status` (#45 / D61). No Angular Material. No polling.

## Approaches considered

| | Approach | Trade-off |
|---|---|---|
| A | Hard-code Start for `download_cfpb_all` only; no list call | Smaller UI, but breaks when the seed name changes or more workflows appear; ignores D66 |
| B (chosen) | Load enabled workflows once; per-MIO `<select>` + Start; default selection `download_cfpb_all` when present; Refresh reloads status | One extra GET; matches D43/D46/D66; still MVP-small |
| C | Auto-poll `/mios/status` after start | Settles the open question toward polling; more moving parts and flake risk for MVP (D54) |

## Decision D72 (summary)

1. **Load on Imports:** besides `loadMioStatus` (D71), call `GET {apiBaseUrl}/workflows` once on init via `listWorkflows(http, ctx)`. Keep only rows with `enabled === true` for the picker. Prefer default selection `workflow_name === "download_cfpb_all"` when that row exists; otherwise the first enabled workflow.
2. **Ctx helpers (D5 / D65):**
   - `listWorkflows(http, ctx)` → 200 list on `ctx.resp.workflows`, `SUCCESS`; HTTP/network failure → empty list, short error, `FAILURE`.
   - `startWorkflow(http, ctx)` with `ctx.req.workflowId` and optional `ctx.req.mioId` → `POST …/workflows/{id}/start` JSON `{ mio_id }` when `mioId` set. HTTP 202 → `SUCCESS` and `ctx.resp.executionId`. HTTP 422 → `INVALID_INPUT` and error text. Other failures → `FAILURE` and error text.
3. **Per-MIO controls** inside each accordion body (plain HTML/CSS, no Material):
   - Native `<select data-testid="mio-workflow-select">` of enabled workflows (label = `workflow_name`).
   - **Start** button (`data-testid="mio-start-workflow"`) posts with that MIO's `id` as `mio_id`.
   - **Refresh status** button (`data-testid="mio-refresh-status"`) re-calls `loadMioStatus` for the whole page (manual refresh; **no polling** — closes the #65 open question for MVP).
4. **Disabled while running (acceptance):** Start is disabled when (a) a start HTTP call for that MIO is in flight, or (b) that MIO's `latest_ingest.status` is `requested` or `started` (non-final per D30). Refresh stays available so the operator can clear a stuck "running" view after Airflow finishes.
5. **After 202:** immediately re-run `loadMioStatus` so the accordion shows the new ingest/execution without inventing status text.
6. **Errors:** start failure shows a short non-status error near the controls (or page-level alert); never synthesize ingest status. Workflow list failure leaves the select empty and shows the list error; Start stays disabled with no workflow chosen.
7. **Stack:** D65 / D69 / D71 — standalone components, plain CSS, no Angular Material, no new npm dependencies. No Middleware/Python changes (endpoints already built).

## Layout / files

| Path | Role |
|---|---|
| `src/app/core/workflow-list.ts` | D66-shaped types + `listWorkflows` |
| `src/app/core/workflow-list.spec.ts` | SUCCESS / FAILURE mapping |
| `src/app/core/start-workflow.ts` | D68 start helper + ctx |
| `src/app/core/start-workflow.spec.ts` | 202 / 422 / other error mapping |
| `src/app/datasets/imports/imports-page.ts` | Load list+status; start; refresh; disable rules |
| `src/app/datasets/imports/imports-page.html` | Select + Start + Refresh per accordion |
| `src/app/datasets/imports/imports-page.css` | Minimal control styles |
| `src/app/datasets/imports/imports-page.spec.ts` | Start disabled while running; refresh reloads; start posts `mio_id` |

## Display / interaction rules

| Fact | UI |
|---|---|
| Enabled workflows include `download_cfpb_all` | That option is selected by default for every MIO |
| `latest_ingest.status` is `requested` or `started` | Start disabled |
| Start HTTP in flight for that `mio.id` | Start disabled |
| Start returns 202 | Refresh status automatically; Start stays disabled if new status is still non-final |
| Operator clicks Refresh | Re-fetch `GET /mios/status` only (workflows list not reloaded unless init) |

## Tests

- Unit: `listWorkflows` 200 → SUCCESS + workflows; error → FAILURE.
- Unit: `startWorkflow` 202 → SUCCESS + executionId; 422 → INVALID_INPUT; 500 → FAILURE; request body includes `mio_id` when provided.
- Unit: Imports page — Start disabled when ingest status is `started`; Start enabled when `null` / `completed` / `failed` and a workflow is selected; clicking Start issues POST then GET status; Refresh issues GET status.
- `npm run local:portal:admin:test` and `local:portal:admin:build` (Node 22) exit 0.

## Docs to update when built

| File | Change |
|---|---|
| `DESIGN.md` | D72 row; next decision D73; note D71 out-of-scope line superseded for start/refresh |
| `Milestone_02.md` | next decision D73; workflow rows for #65; open-question note for #65 closed as refresh |
| `docs/PRODUCT_FEATURES.md` | F1/F2 / portal row: start + refresh Done (#65 / D72); fix #64 decision ref to D71 |

## Out of scope

- Polling / websockets.
- Angular Material, auth, filtering by `mio_id` on the status GET.
- Python / Middleware changes.
- Choosing dataset_location_id in the UI.
- Enabling DB Ingest (D13).
