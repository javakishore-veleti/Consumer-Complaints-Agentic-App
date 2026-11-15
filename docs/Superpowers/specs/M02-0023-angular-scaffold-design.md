# M02-0023 (#62) Angular app scaffold (consumer-complaints-admin)

Decisions: D5, D54 and **D65** in `Middleware/ConsumerComplaintsHandsOn/DESIGN.md`. Decided without the user present (D54 MVP, D65); review and reverse if needed.

**Numbering note:** D63 and D64 are claimed by story #57 (download DAG / short facade packages) on a parallel branch; this story records **D65** so the numbers do not collide when both merge. D64 does not affect the Angular scaffold.

## Goal

A runnable Angular admin app under `Portals/consumer-complaints-admin/` that **builds and serves**. Later stories will call `GET /mios/status` (#45 done) and start-workflow (#42). This story only scaffolds the app, proves it serves, and locks the layout + TypeScript ctx convention.

## Approaches considered

| | Approach | Trade-off |
|---|---|---|
| A | Nx / Angular workspace monorepo at repo root | Heavy for one MVP app; fights the existing root `package.json` scripts style |
| B (chosen) | `ng new consumer-complaints-admin` under `Portals/` (standalone app, latest stable Angular CLI) | Matches PRODUCT_FEATURES name; one app folder; root scripts `cd` into it like the middleware scripts |
| C | Hand-rolled Vite + Angular without CLI | Fragile; no standard `ng serve` / schematics for later portal stories |

## D65 (standing)

1. **Layout:** every browser portal lives under repository-root `Portals/<app-name>/`. The first app is **`Portals/consumer-complaints-admin/`** (npm package / Angular project name `consumer-complaints-admin`). `Portals/README.md` replaces the empty `Portals/README.d` placeholder and points at the apps.
2. **Stack:** **Angular 22.x** (latest stable CLI at design time: `@angular/cli` **22.2.7**). `engines.node` is `^22.22.3 \|\| ^24.15.0 \|\| >=26.0.0` (Angular 22 floor). Use the CLI defaults that match that major: standalone components, application builder, TypeScript strict, no SSR for MVP.
3. **API base URL:** `proxy.conf.json` for `ng serve` forwards `/api` → `http://127.0.0.1:8000` (Middleware default `API_HOST`/`API_PORT`). App code reads `apiBaseUrl` from environment (`'/api'` in dev via proxy; overridable later). No live API call required for this story's acceptance.
4. **Ctx pattern (D5 on TypeScript):** portal methods take **one** `XxxCtx` (`req` + `resp`) and return a **number** (same integer codes as Python: `SUCCESS = 0`, `FAILURE = 1`, … in a small `core/return-codes.ts`). Results go on `ctx.resp`. Scaffold ships the types plus one tiny home/health helper that uses the pattern; full facades wait for later stories.
5. **Out of MVP:** auth, nav chrome, MIO accordions (#64), start-workflow UI, calling `/mios/status`, Angular Material theme polish, SSR, Nx.

## Layout

| Path | Role |
|---|---|
| `Portals/README.md` | Index of portal apps (replaces `README.d`) |
| `Portals/consumer-complaints-admin/` | Angular app root (`ng new` output, committed with `package-lock.json`) |
| `Portals/consumer-complaints-admin/proxy.conf.json` | Dev proxy `/api` → FastAPI on `127.0.0.1:8000` |
| `Portals/consumer-complaints-admin/src/environments/` | `apiBaseUrl` (and future flags) |
| `Portals/consumer-complaints-admin/src/app/core/` | `return-codes.ts`, ctx type stubs, example health helper |
| `Portals/consumer-complaints-admin/src/app/home/` | Home/health page that proves the app serves |
| `Portals/consumer-complaints-admin/README.md` | How to install, serve, build; Node version; proxy note |
| Root `package.json` scripts | `local:portal:admin:start`, `local:portal:admin:build`, `local:portal:admin:test` |
| Root `.gitignore` | `Portals/**/node_modules/`, `Portals/**/.angular/`, `Portals/**/dist/` (and usual Angular caches) |

## Acceptance (story)

- [ ] App builds (`ng build` / root `local:portal:admin:build`)
- [ ] App serves (`ng serve` / root `local:portal:admin:start`); home/health page loads in a browser

## Home / health page

Minimal route `/` (default): title **Consumer Complaints Admin**, short line that the scaffold is up, and the configured `apiBaseUrl` shown as text (so env/proxy wiring is visible without calling the API). No cards, no Material dashboard, no API fetch in this story.

## Root npm scripts

Match existing `local:*` style in root `package.json`:

```json
"local:portal:admin:start": "npm --prefix Portals/consumer-complaints-admin start",
"local:portal:admin:build": "npm --prefix Portals/consumer-complaints-admin run build",
"local:portal:admin:test": "npm --prefix Portals/consumer-complaints-admin test -- --watch=false --browsers=ChromeHeadless"
```

(`start` must pass `--proxy-config proxy.conf.json` via the app's `package.json` script.)

## Tests

- Unit: return-codes constants and one ctx helper (Vitest or the CLI's default unit runner for Angular 22 — use whatever `ng new` configures; keep one small spec).
- Build: `npm run local:portal:admin:build` from repo root must exit 0.
- Serve: manual or short `ng serve` + curl of `/` in the plan; not a Python CI job in this story.

## Docs to update when built

| File | Change |
|---|---|
| `DESIGN.md` | D65 row (this story); next decision D66 |
| `Milestone_02.md` | next decision D66 |
| `docs/PRODUCT_FEATURES.md` | portal row → scaffold Done / in progress as appropriate |
| `ARCHITECTURE.md` | mention `Portals/consumer-complaints-admin/` in the high-level picture or tree if a repo-root tree exists; otherwise a one-line pointer is enough |
| Root `README.md` | optional one-liner under tooling pointing at the portal scripts |

## Out of scope

- Calling `GET /mios/status` or start-workflow.
- Python changes (D64 irrelevant here).
- Auth, shared UI library, multiple portals.
- Committing `node_modules` or `.angular` cache.
