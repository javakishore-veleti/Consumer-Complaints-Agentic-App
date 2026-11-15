# M02-0025 (#64) MIO accordions with status from the API

Decisions: D5, D54, D61, D65, D69 and **D70** in `Middleware/ConsumerComplaintsHandsOn/DESIGN.md`. Decided without the user present (D70); review and reverse if needed.

**Numbering note:** On this worktree after fetch from `origin/main`, DESIGN.md ends at **D69** (#63 portal chrome). Story #42 recorded **D68** (start-workflow). Next free is **D70**. Do not reuse numbers claimed on parallel branches without checking DESIGN.md first.

## Goal

Fill the Imports accordion shell (#63 / D69) with one expandable panel per MIO, showing ingest status from `GET /mios/status` (#45 / D61). Status is never invented in the UI. No start-workflow button (#65).

## Approaches considered

| | Approach | Trade-off |
|---|---|---|
| A | Angular Material expansion panel | Extra dependency; #62/#63 deliberately stayed plain CSS (D65, D69) |
| B (chosen) | Native `<details>` / `<summary>` per MIO inside the existing accordion shell; HttpClient + ctx helper for the fetch | Zero new packages; matches portal chrome; accessible expand/collapse |
| C | Always-open stacked cards, no expand | Loses accordion UX promised by PRODUCT_FEATURES F1/F2; harder for many MIOs |

## Decision D70 (summary)

1. **Load on Imports:** when `ImportsPage` initializes, call `GET {apiBaseUrl}/mios/status` (dev: `/api/mios/status` via proxy). No query filters. Provide `provideHttpClient()` in `app.config.ts`.
2. **Ctx helper (D5 / D65):** a portal method `loadMioStatus(ctx)` takes one `MioStatusCtx` (`req` + `resp`) and returns a Promise of the integer code. On HTTP 200, put the JSON list on `ctx.resp.entries` and return `SUCCESS`. On network/HTTP failure, leave entries empty (or unchanged), set `ctx.resp.error` to a short non-status message, return `FAILURE`. Never synthesize a MIO status string.
3. **Render:** one `<details data-testid="mio-accordion">` per entry in API order. Summary shows `name` and the **exact** `latest_ingest.status` when present; when `latest_ingest` is `null`, show the fixed label **No ingest yet** (that label means the API returned null — it is not a guessed status code). Expanded body shows description (if any), ingest `message`, volume fields and timestamps **only when the API provided them**, and a simple list of execution `status` / `workflow_name` / `message` from `latest_ingest.executions` (raw API values).
4. **Empty / error UI:** empty list → shell stays empty with a line that no MIOs were returned. Fetch failure → show `ctx.resp.error` (or a generic “Failed to load MIO status”) and **no** accordion rows with fabricated statuses.
5. **Stack:** stay on D65/D69 — standalone components, plain CSS, no Angular Material, no polling, no start button.

## Layout / files

| Path | Role |
|---|---|
| `src/app/core/mio-status.ts` | Types matching D61 JSON + `loadMioStatus(ctx)` HttpClient helper |
| `src/app/core/mio-status.spec.ts` | Unit tests for SUCCESS / FAILURE mapping (HttpClientTesting) |
| `src/app/datasets/imports/imports-page.ts` | Calls loader on init; holds signals for entries / error / loading |
| `src/app/datasets/imports/imports-page.html` | Accordion shell filled with `<details>` panels |
| `src/app/datasets/imports/imports-page.css` | Minimal accordion styles (no Material) |
| `src/app/datasets/imports/imports-page.spec.ts` | Renders panels from mocked loader / HttpTestingController |
| `src/app/app.config.ts` | `provideHttpClient()` |

## Display rules (acceptance: status never guessed)

| API fact | UI |
|---|---|
| HTTP 200, `latest_ingest.status` = `"failed"` (or any other string) | Show that string verbatim |
| HTTP 200, `latest_ingest` = `null` | Summary secondary text: `No ingest yet` (not a status enum value) |
| HTTP 200, `message` = `"disk full"` | Show that message in the body |
| HTTP 200, `message` = `null` | Omit message or show nothing — do not invent a reason |
| Non-200 / network error | Error banner only; zero accordion status claims |

## Tests

- Unit: `loadMioStatus` maps 200 list → SUCCESS + entries; 500/error → FAILURE + error text, empty entries.
- Unit: Imports page with mocked 200 payload renders one accordion per MIO; summary contains API status; null ingest shows `No ingest yet`; failed fetch shows error and no status rows pretending success.
- Build: `npm run local:portal:admin:build` (Node 22) exits 0.
- Test: `npm run local:portal:admin:test` exits 0.

## Docs to update when built

| File | Change |
|---|---|
| `DESIGN.md` | D70 row; next decision D71 |
| `Milestone_02.md` | next decision D71; workflow rows for #64 |
| `docs/PRODUCT_FEATURES.md` | F1/F2 / portal row: MIO status accordions Done for this slice; start still Planned (#65) |

## Out of scope

- Start-workflow button / polling (#65).
- Enabling DB Ingest (D13).
- Angular Material, auth, filtering by `mio_id`.
- Python / Middleware changes (endpoint already built in #45).
- Inventing display labels that remap API status codes (e.g. mapping `failed` → “Error”).
