# M03-0011 (#121) Admin Imports: live API list/start/refresh hardening

Decisions: D5, D61, D65, D66, D68, D71, D72 in `Middleware/ConsumerComplaintsHandsOn/DESIGN.md`. **No new DESIGN.md decision** for this story — parallel M03 tracks own the next free number (D75). This hardens portal error and local-run docs on top of D71/D72.

## Goal

Make `Portals/consumer-complaints-admin` Imports reliable against a **live** local Middleware: list MIOs (`GET /mios/status`), list workflows (`GET /workflows`), start (`POST /workflows/{id}/start`), and refresh. When API / Airflow / DB fails, the UI shows the **real** Middleware error text (FastAPI `detail`), never invented ingest status enums. `npm run local:portal:admin:start` keeps working via `/api` proxy; document a **one-command** portal + API local run.

## Context (already built in M02)

| Story | What exists |
|---|---|
| #64 / D71 | `loadMioStatus` + Imports accordions; status from API or “No ingest yet” when `null` |
| #65 / D72 | `listWorkflows`, `startWorkflow`, Start / Refresh, disable while `requested`/`started` |
| D65 | `environment.apiBaseUrl = '/api'`; `proxy.conf.json` → `127.0.0.1:8000` |

**Runtime already hits live HTTP** (no mock catalog). Gaps are error messages, docs, and a combined local start script.

## Approaches considered

| | Approach | Trade-off |
|---|---|---|
| A | Docs-only: document “start API then portal” | Fails acceptance “real API messages” |
| B (chosen) | Shared HTTP error extractor → `ctx.resp.error`; keep return codes; one-command npm script + README fix | Smallest change; matches D5/D65; no Middleware edits |
| C | New toast library / redesign Imports chrome | Scope creep; violates D69 plain CSS |

## Design

### 1. Surface real API errors (portal only)

Add a tiny helper (e.g. `src/app/core/http-error-message.ts`):

- Input: unknown catch value + short **fallback** string (network / non-JSON).
- If `HttpErrorResponse` and `error.error.detail` is a **string**, use that string.
- If `detail` is a **validation array** (FastAPI), join item `msg` fields (or stringify) into one line.
- Else if `statusText` is non-empty and not `"Unknown Error"`, prefer `"HTTP {status}: {statusText}"` or statusText alone.
- Else use the fallback.
- **Never** invent or rewrite ingest/execution `status` values — those stay verbatim from successful JSON bodies (D71/D72).

Wire the helper into:

| Helper | On FAILURE / INVALID_INPUT |
|---|---|
| `loadMioStatus` | Prefer API `detail` over `"Failed to load MIO status"` |
| `listWorkflows` | Prefer API `detail` over `"Failed to load workflows"` |
| `startWorkflow` | 422 / 502 / 500 / other: prefer API `detail` (e.g. `"invalid request"`, `"engine start failed"`, `"request failed"`) over hardcoded strings |

Return codes stay: `SUCCESS` / `FAILURE` / `INVALID_INPUT` (422 only for start). Imports page continues to display `ctx.resp.error` in existing `error` / `actionError` signals.

### 2. Proxy / `apiBaseUrl` (keep working)

- Keep `environment.apiBaseUrl = '/api'` and `proxy.conf.json` (`/api` → `http://127.0.0.1:8000`, pathRewrite strips `/api`).
- Keep portal `package.json` `"start": "ng serve --proxy-config proxy.conf.json"` so `npm run local:portal:admin:start` continues to proxy.
- Optional hardening (same story if cheap): set `proxyConfig` on the Angular serve target in `angular.json` so a bare `ng serve` still proxies — do not break the existing CLI flag.

### 3. One-command portal + API local run

Add a root script (name TBD in plan; preferred shape):

```text
npm run local:portal:admin:with-api
```

Behavior:

1. `npm run local:handson:middlware:all:start` (idempotent if API already up via `run_app.sh`).
2. Then `npm run local:portal:admin:start` (foreground `ng serve`).

Document in:

- `Portals/consumer-complaints-admin/README.md` — remove stale “does not call the API yet”; document Imports path `/datasets/imports`, proxy, and the with-api script.
- Root `README.md` and/or `Portals/README.md` — one line pointing at the same command.
- Brief note in `ARCHITECTURE.md` §8 or adjacent that Admin UI uses proxy `/api` → Middleware `:8000` (no Middleware code change).

### 4. Tests (TDD)

Strengthen unit tests (HttpTestingController):

- Error responses with `{ detail: "request failed" }` / `"engine start failed"` → `ctx.resp.error` **equals** that detail (not merely non-empty).
- Network-style error without body → fallback string still set; entries/workflows empty; **no** invented status.
- Existing SUCCESS paths unchanged.
- Imports page still shows `actionError` / `error` from helpers.

Verification: `npm run local:portal:admin:test` and `npm run local:portal:admin:build` exit 0.

## Files (expected)

| Path | Change |
|---|---|
| `Portals/.../src/app/core/http-error-message.ts` (+ `.spec.ts`) | New extractor |
| `mio-status.ts` / `workflow-list.ts` / `start-workflow.ts` (+ specs) | Use extractor |
| Root `package.json` | `local:portal:admin:with-api` (or equivalent) |
| Portal / root / Portals READMEs; optionally ARCHITECTURE §8 | Document live Imports + one-command |
| `angular.json` | Optional `proxyConfig` on serve |

## Out of scope

- New DESIGN.md D## (D75 reserved for parallel tracks).
- Middleware / Python / OpenAPI changes.
- Polling, auth, Angular Material, inventing status enums.
- Story #122 E2E happy path (Airflow callback → UI) — separate story.
- Changing proxy target host/port dynamically (still 127.0.0.1:8000).

## Acceptance mapping

| Acceptance | How this design meets it |
|---|---|
| Imports works against local API without mock data | Already true at runtime; keep HTTP-only helpers; docs stop claiming “no API yet” |
| Failures surface real API messages (no invented status) | `detail` → `ctx.resp.error`; status fields only from 200/202 JSON |
| Documented one-command portal + API local run | Root npm script + README updates |
