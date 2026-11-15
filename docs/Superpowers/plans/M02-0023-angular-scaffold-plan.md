# M02-0023 (#62) Angular app scaffold Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Scaffold `Portals/consumer-complaints-admin` so the Angular admin app builds and serves, with API proxy/env wiring and a TypeScript ctx + integer return-code stub (D5, D65).

**Architecture:** Standalone Angular 22 app under `Portals/` (D65). Dev traffic to the Middleware uses `/api` → `http://127.0.0.1:8000` via `proxy.conf.json`. Home route proves serve; no live API call yet. Ctx helpers mirror Python: one `XxxCtx`, integer codes in `core/return-codes.ts`.

**Tech Stack:** Angular **22.x** (`@angular/cli` **22.2.7** at design time), Node `^22.22.3 \|\| ^24.15.0 \|\| >=26.0.0`, TypeScript (CLI default), npm, root `package.json` scripts.

Spec: `docs/Superpowers/specs/M02-0023-angular-scaffold-design.md`. Decisions: D5, D54, D65 in `Middleware/ConsumerComplaintsHandsOn/DESIGN.md`.

## Global Constraints

- Paths are relative to the **repository root** unless a step says otherwise.
- App path exactly: `Portals/consumer-complaints-admin/`. Do not put the Angular app at the repo root.
- Use **latest stable Angular 22** via `npx -y @angular/cli@22` (or pin `22.2.7`). Implementer must use a Node that satisfies Angular 22 engines (upgrade from Node 20 if needed).
- `ng new` flags (non-interactive): `--directory=Portals/consumer-complaints-admin --routing --style=css --ssr=false --skip-git` (and defaults for standalone). Run from repo root so the folder lands correctly; if CLI insists on creating a nested name, create the directory layout so the final app root is exactly `Portals/consumer-complaints-admin`.
- Proxy: `/api` → `http://127.0.0.1:8000` (Middleware `API_HOST`/`API_PORT` defaults). App `apiBaseUrl` is `'/api'` in development.
- Every new portal method takes one ctx and returns a number (D5 / D65). Ship `SUCCESS=0`, `FAILURE=1`, `NOT_FOUND=2`, `INVALID_INPUT=3`, `CONFLICT=4` to match Python `return_codes.py`.
- Do **not** call `GET /mios/status` or start-workflow in this story.
- Do **not** commit `node_modules/`, `.angular/`, or `dist/`. Extend root `.gitignore`.
- Scratch files go in `runtime_data/tmp/`, never `/tmp` (D36).
- Commit with `/ccaa-commit-push 62` only (never a raw `git commit`). This plan author does not commit.

## File Structure

| File | Responsibility |
|---|---|
| `Portals/consumer-complaints-admin/` (create via `ng new`) | Angular app (sources, `package.json`, lockfile, `angular.json`) |
| `Portals/consumer-complaints-admin/proxy.conf.json` | Dev proxy `/api` → FastAPI |
| `Portals/consumer-complaints-admin/src/environments/environment.ts` | `apiBaseUrl: '/api'` |
| `Portals/consumer-complaints-admin/src/app/core/return-codes.ts` | Integer codes aligned with Python |
| `Portals/consumer-complaints-admin/src/app/core/health-ctx.ts` | Example `HealthReq` / `HealthResp` / `HealthCtx` + `checkHealth(ctx): number` |
| `Portals/consumer-complaints-admin/src/app/home/` | Home/health page component + route |
| `Portals/consumer-complaints-admin/README.md` | Install / serve / build / Node / proxy |
| `Portals/README.md` (create; delete `README.d`) | Index of portals |
| Root `package.json` | `local:portal:admin:{start,build,test}` |
| Root `.gitignore` | Angular/node ignores under `Portals/` |
| `Middleware/ConsumerComplaintsHandsOn/DESIGN.md` | D65 already recorded with the design step; mark built if needed |
| `docs/PRODUCT_FEATURES.md`, `ARCHITECTURE.md`, root `README.md` | Portal path present tense |

---

### Task 1: Scaffold app, ignore rules, build green

**Files:**
- Create: `Portals/consumer-complaints-admin/**` (CLI scaffold + lockfile)
- Modify: root `.gitignore`
- Delete: `Portals/README.d` only after Task 2 adds `Portals/README.md` (or replace in Task 2)
- Test: prove `package.json` exists and `npm run build` works (commands below)

**Interfaces:**
- Consumes: Node 22+ / Angular CLI 22.
- Produces: installable app that `ng build` succeeds.

- [ ] **Step 1: Write the failing layout check**

From repo root, create a throwaway check (or run inline) that fails before the app exists:

```bash
test -f Portals/consumer-complaints-admin/package.json
```

Expected: FAIL (file missing).

- [ ] **Step 2: Scaffold with Angular CLI 22**

Ensure Node satisfies `^22.22.3 || ^24.15.0 || >=26.0.0`. Then from repo root:

```bash
npx -y @angular/cli@22 new consumer-complaints-admin \
  --directory=Portals/consumer-complaints-admin \
  --routing \
  --style=css \
  --ssr=false \
  --skip-git \
  --defaults
```

If the CLI nests an extra folder, flatten so `Portals/consumer-complaints-admin/package.json` exists at that exact path. Commit the generated lockfile; do not commit `node_modules`.

- [ ] **Step 3: Extend `.gitignore`**

Add (if not already covered):

```gitignore
# Angular portals
Portals/**/node_modules/
Portals/**/.angular/
Portals/**/dist/
Portals/**/coverage/
```

- [ ] **Step 4: Install and build**

```bash
npm --prefix Portals/consumer-complaints-admin install
npm --prefix Portals/consumer-complaints-admin run build
```

Expected: PASS (exit 0).

- [ ] **Step 5: Commit**

```bash
/ccaa-commit-push 62
```

Message theme: scaffold Angular 22 app under `Portals/consumer-complaints-admin`.

---

### Task 2: Home page, proxy/env, ctx stub, root scripts, docs

**Files:**
- Create: `proxy.conf.json`, `src/environments/environment.ts`, `src/app/core/return-codes.ts`, `src/app/core/health-ctx.ts`, home component, unit spec for `checkHealth`, `Portals/README.md`, app `README.md`
- Modify: app `package.json` (`start` with proxy), `src/app/app.routes.ts`, `src/app/app.config.ts` if needed, root `package.json`, `docs/PRODUCT_FEATURES.md`, `ARCHITECTURE.md`, root `README.md` (one-liner), delete `Portals/README.d`
- Test: unit test for `checkHealth`; build; serve smoke

**Interfaces:**
- Consumes: Task 1 app.
- Produces: `/` home page; `apiBaseUrl`; `checkHealth(ctx: HealthCtx): number`; root `local:portal:admin:*` scripts.

- [ ] **Step 1: Write the failing unit test**

Create `Portals/consumer-complaints-admin/src/app/core/health-ctx.spec.ts` (or the CLI's preferred colocated name):

```typescript
import { CONFLICT, FAILURE, INVALID_INPUT, NOT_FOUND, SUCCESS } from './return-codes';
import { HealthCtx, checkHealth } from './health-ctx';

describe('checkHealth', () => {
  it('returns SUCCESS and sets ok on resp', () => {
    const ctx: HealthCtx = { req: {}, resp: { ok: false, apiBaseUrl: '' } };
    expect(checkHealth(ctx)).toBe(SUCCESS);
    expect(ctx.resp.ok).toBe(true);
    expect(ctx.resp.apiBaseUrl).toBe('/api');
  });

  it('exposes the same integer codes as Python', () => {
    expect([SUCCESS, FAILURE, NOT_FOUND, INVALID_INPUT, CONFLICT]).toEqual([0, 1, 2, 3, 4]);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

```bash
npm --prefix Portals/consumer-complaints-admin test -- --watch=false --browsers=ChromeHeadless
```

Expected: FAIL (modules missing). If the CLI uses Vitest instead of Karma, use the generated test command and adjust the runner flags only — keep the same assertions.

- [ ] **Step 3: Implement core + home + proxy/env**

`return-codes.ts`:

```typescript
export const SUCCESS = 0;
export const FAILURE = 1;
export const NOT_FOUND = 2;
export const INVALID_INPUT = 3;
export const CONFLICT = 4;
```

`health-ctx.ts` (example only — plan example, not production UI logic beyond the stub):

```typescript
import { SUCCESS } from './return-codes';
import { environment } from '../../environments/environment';

export interface HealthReq {}
export interface HealthResp {
  ok: boolean;
  apiBaseUrl: string;
}
export interface HealthCtx {
  req: HealthReq;
  resp: HealthResp;
}

/** Example portal method: one ctx in, integer out (D5 / D65). */
export function checkHealth(ctx: HealthCtx): number {
  ctx.resp.ok = true;
  ctx.resp.apiBaseUrl = environment.apiBaseUrl;
  return SUCCESS;
}
```

`environment.ts`: `{ production: false, apiBaseUrl: '/api' }`.

`proxy.conf.json`:

```json
{
  "/api": {
    "target": "http://127.0.0.1:8000",
    "secure": false,
    "changeOrigin": true,
    "pathRewrite": { "^/api": "" }
  }
}
```

Wire `package.json` `"start"` to `ng serve --proxy-config proxy.conf.json`.

Home component at `/`: heading "Consumer Complaints Admin", short scaffold line, display `apiBaseUrl` from `checkHealth` (call once on init). Keep the UI minimal (D54).

- [ ] **Step 4: Root scripts and Portals README**

Root `package.json` scripts:

```json
"local:portal:admin:start": "npm --prefix Portals/consumer-complaints-admin start",
"local:portal:admin:build": "npm --prefix Portals/consumer-complaints-admin run build",
"local:portal:admin:test": "npm --prefix Portals/consumer-complaints-admin test -- --watch=false --browsers=ChromeHeadless"
```

Write `Portals/README.md` (delete `README.d`). Write `Portals/consumer-complaints-admin/README.md` with Node engines, install, `npm start` / root scripts, proxy note.

Update `docs/PRODUCT_FEATURES.md` portal row to reflect scaffold Done. Add a one-line `Portals/consumer-complaints-admin/` mention in `ARCHITECTURE.md` and optionally root `README.md`.

- [ ] **Step 5: Run tests and build**

```bash
npm run local:portal:admin:test
npm run local:portal:admin:build
```

Expected: PASS.

- [ ] **Step 6: Serve smoke (acceptance)**

```bash
npm run local:portal:admin:start
# in another shell, after the dev server prints the local URL (usually http://localhost:4200):
curl -sS -o /dev/null -w "%{http_code}\n" http://localhost:4200/
```

Expected: `200`. Stop the server after the check.

- [ ] **Step 7: Commit**

```bash
/ccaa-commit-push 62
```

Message theme: home/health page, proxy/env, ctx stub, root portal scripts, docs.

---

## Plan self-review

1. **Spec coverage:** `Portals/consumer-complaints-admin` (Task 1); Angular 22 + Node engines (Task 1); build (Task 1); serve + home (Task 2); proxy/env (Task 2); ctx + integer codes (Task 2); root scripts + READMEs (Task 2). Out of scope left out: `/mios/status`, start-workflow, auth, Python/D64.
2. **Placeholders:** None; CLI version, proxy target, return codes, and script names are concrete.
3. **Consistency:** D65 path and naming match the spec; return codes match Python; `/ccaa-commit-push 62` after each task; no production app beyond the plan examples above.
