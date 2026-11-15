# M03-0011 Admin Imports live API hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Harden Imports helpers so HTTP failures surface Middleware FastAPI `detail` (never invent status), and document a one-command portal + API local run while keeping `/api` proxy + `apiBaseUrl` working.

**Architecture:** Add `httpErrorMessage(err, fallback)` that extracts FastAPI `detail` (string or validation array). Wire it into `loadMioStatus`, `listWorkflows`, and `startWorkflow` without changing return codes or success JSON mapping. Add root npm script that starts Middleware then the admin portal; fix stale READMEs.

**Tech Stack:** Angular 22 standalone, HttpClient, `@angular/build:unit-test`, Node 22 via nvm; bash + existing `run_app.sh`.

## Global Constraints

- Spec: `docs/Superpowers/specs/M03-0011-admin-imports-live-api-design.md`. Decisions: D5, D61, D65, D66, D68, D71, D72. **No new DESIGN.md D##** (parallel tracks own D75).
- Work only under `.worktrees/m03-0011-admin-imports-live-api` on branch `m03-0011-admin-imports-live-api`.
- Use Node 22 (`nvm use 22`) before every portal `npm` / `ng` command.
- Commit messages: `M03-0011 #121: <imperative summary>` (single line). Author from git config. Strip AI trailers before push.
- Do not invent ingest/execution status enums. Do not add Angular Material or new npm dependencies.
- Do not change Python / Middleware / OpenAPI.

---

## File map

| Path | Responsibility |
|---|---|
| `Portals/consumer-complaints-admin/src/app/core/http-error-message.ts` | Extract FastAPI `detail` / fallback |
| `Portals/consumer-complaints-admin/src/app/core/http-error-message.spec.ts` | Unit tests for extractor |
| `Portals/.../mio-status.ts` (+ spec) | Use extractor on catch |
| `Portals/.../workflow-list.ts` (+ spec) | Use extractor on catch |
| `Portals/.../start-workflow.ts` (+ spec) | Use extractor for 422 and other errors |
| `package.json` (root) | `local:portal:admin:with-api` |
| `Portals/consumer-complaints-admin/README.md` | Live Imports + with-api docs |
| `Portals/README.md` / root `README.md` | Point at with-api |
| `Portals/consumer-complaints-admin/angular.json` | Optional serve `proxyConfig` |
| `Middleware/.../ARCHITECTURE.md` | Brief Admin UI proxy note |

---

### Task 1: `httpErrorMessage` helper (TDD)

**Files:**
- Create: `Portals/consumer-complaints-admin/src/app/core/http-error-message.spec.ts`
- Create: `Portals/consumer-complaints-admin/src/app/core/http-error-message.ts`

**Interfaces:**
- Consumes: `HttpErrorResponse` from `@angular/common/http`
- Produces: `httpErrorMessage(err: unknown, fallback: string): string`

- [ ] **Step 1: Write failing tests**

```typescript
import { HttpErrorResponse } from '@angular/common/http';
import { httpErrorMessage } from './http-error-message';

describe('httpErrorMessage', () => {
  it('returns string detail from FastAPI body', () => {
    const err = new HttpErrorResponse({
      error: { detail: 'engine start failed' },
      status: 502,
      statusText: 'Bad Gateway',
    });
    expect(httpErrorMessage(err, 'fallback')).toBe('engine start failed');
  });

  it('joins validation-array detail msgs', () => {
    const err = new HttpErrorResponse({
      error: { detail: [{ msg: 'field a' }, { msg: 'field b' }] },
      status: 422,
      statusText: 'Unprocessable Entity',
    });
    expect(httpErrorMessage(err, 'fallback')).toBe('field a; field b');
  });

  it('uses fallback when body has no detail', () => {
    const err = new HttpErrorResponse({
      error: 'boom',
      status: 500,
      statusText: 'Server Error',
    });
    expect(httpErrorMessage(err, 'Failed to load')).toBe('Failed to load');
  });

  it('uses fallback for non-HTTP errors', () => {
    expect(httpErrorMessage(new Error('x'), 'Failed to load')).toBe('Failed to load');
  });
});
```

- [ ] **Step 2: Run test — expect FAIL**

```bash
cd Portals/consumer-complaints-admin && source ~/.nvm/nvm.sh && nvm use 22
npm test -- --watch=false --include='**/http-error-message.spec.ts'
```

- [ ] **Step 3: Implement `httpErrorMessage`**

```typescript
import { HttpErrorResponse } from '@angular/common/http';

export function httpErrorMessage(err: unknown, fallback: string): string {
  if (!(err instanceof HttpErrorResponse)) {
    return fallback;
  }
  const detail = err.error?.detail;
  if (typeof detail === 'string' && detail.trim() !== '') {
    return detail;
  }
  if (Array.isArray(detail)) {
    const parts = detail
      .map((item) => (item && typeof item === 'object' && 'msg' in item ? String((item as { msg: unknown }).msg) : ''))
      .filter((s) => s.trim() !== '');
    if (parts.length) {
      return parts.join('; ');
    }
  }
  return fallback;
}
```

- [ ] **Step 4: Run tests — expect PASS**

- [ ] **Step 5: Commit** `M03-0011 #121: add httpErrorMessage for FastAPI detail`

---

### Task 2: Wire helpers to surface API detail (TDD)

**Files:**
- Modify: `mio-status.ts`, `workflow-list.ts`, `start-workflow.ts` and their specs

**Interfaces:**
- Consumes: `httpErrorMessage`
- Produces: same ctx + return codes; `ctx.resp.error` equals API `detail` when present

- [ ] **Step 1: Strengthen failing assertions in specs**

In `mio-status.spec.ts` error case, flush `{ detail: 'request failed' }` and expect `ctx.resp.error === 'request failed'`.

In `workflow-list.spec.ts`, same pattern.

In `start-workflow.spec.ts`:
- 422 with `{ detail: 'invalid request' }` → `ctx.resp.error === 'invalid request'`
- Add case 502 `{ detail: 'engine start failed' }` → FAILURE + that string
- 500 without detail → still non-empty fallback

- [ ] **Step 2: Run targeted specs — expect FAIL** (still hardcoded strings)

- [ ] **Step 3: Change catch blocks to `httpErrorMessage(err, '…')`**

- [ ] **Step 4: Run targeted specs — expect PASS**

- [ ] **Step 5: Commit** `M03-0011 #121: surface Middleware detail in Imports helpers`

---

### Task 3: One-command local run + docs + optional proxyConfig

**Files:**
- Modify: root `package.json`
- Modify: `Portals/consumer-complaints-admin/README.md`, `Portals/README.md`, root `README.md`
- Modify (optional): `angular.json` serve options `proxyConfig: "proxy.conf.json"`
- Modify: `Middleware/ConsumerComplaintsHandsOn/ARCHITECTURE.md` (short Admin UI note)

- [ ] **Step 1: Add script**

```json
"local:portal:admin:with-api": "npm run local:handson:middlware:all:start && npm run local:portal:admin:start"
```

- [ ] **Step 2: Update READMEs** — remove “does not call the API yet”; document Imports `/datasets/imports`, proxy, and `npm run local:portal:admin:with-api`.

- [ ] **Step 3: Optional** set `proxyConfig` on serve default options in `angular.json`.

- [ ] **Step 4: Commit** `M03-0011 #121: document one-command portal with API`

---

### Task 4: Full verification

- [ ] **Step 1:** `npm run local:portal:admin:test` (Node 22) exit 0
- [ ] **Step 2:** `npm run local:portal:admin:build` exit 0
- [ ] **Step 3:** Milestone log + final `ccaa-commit-push 121` if anything left
- [ ] **Step 4:** PR → main; merge when green; `ccaa-story-complete 121`

---

## Out of scope (do not implement)

- Story #122 E2E Airflow path
- DESIGN.md D75+
- Middleware code changes
