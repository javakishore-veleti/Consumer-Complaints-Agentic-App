# M02-0026 Start workflow button and status refresh Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add per-MIO start-workflow controls and manual status refresh on Imports, calling D66/D68/D61 endpoints without inventing status.

**Architecture:** Ctx helpers `listWorkflows` and `startWorkflow` mirror `loadMioStatus` (HttpClient + D65 return codes). `ImportsPage` loads workflows + status on init; each accordion offers a workflow select, Start (disabled while running), and Refresh (re-GET `/mios/status`). No polling, no Material, no Middleware changes.

**Tech Stack:** Angular 22 standalone, HttpClient, Vitest via `@angular/build:unit-test`, Node 22 via nvm.

## Global Constraints

- Spec: `docs/Superpowers/specs/M02-0026-start-workflow-button-design.md`. Decisions: D5, D54, D61, D65, D66, D68, D69, D71, **D72**.
- Work only under `.worktrees/m02-0026-start-workflow-button` on branch `m02-0026-start-workflow-button-status`.
- Use Node 22 (`nvm use 22`) before every `ng` / `npm` command.
- Commit messages: `M02-0026 #65: <imperative summary>` (single line). Author from git config (javakishore-veleti). Strip AI trailers before push.
- Do not add Angular Material, polling, or new npm dependencies.
- Do not change Python / Middleware (endpoints already exist).

---

## File map

| Path | Responsibility |
|---|---|
| `Portals/consumer-complaints-admin/src/app/core/workflow-list.ts` | D66 types + `listWorkflows` |
| `Portals/consumer-complaints-admin/src/app/core/workflow-list.spec.ts` | HttpClientTesting SUCCESS/FAILURE |
| `Portals/consumer-complaints-admin/src/app/core/start-workflow.ts` | D68 start helper |
| `Portals/consumer-complaints-admin/src/app/core/start-workflow.spec.ts` | 202 / 422 / failure |
| `Portals/consumer-complaints-admin/src/app/datasets/imports/imports-page.ts` | Load, start, refresh, disable |
| `Portals/consumer-complaints-admin/src/app/datasets/imports/imports-page.html` | Controls |
| `Portals/consumer-complaints-admin/src/app/datasets/imports/imports-page.css` | Control styles |
| `Portals/consumer-complaints-admin/src/app/datasets/imports/imports-page.spec.ts` | Page interaction tests |
| `Middleware/ConsumerComplaintsHandsOn/DESIGN.md` | D72; next D73 |
| `docs/Project_Management/Issues/Milestone_02.md` | next D73; #65 workflow; open Q |
| `docs/PRODUCT_FEATURES.md` | F1/F2 / portal Done for #65 |

---

### Task 1: `listWorkflows` helper (TDD)

**Files:**
- Create: `Portals/consumer-complaints-admin/src/app/core/workflow-list.spec.ts`
- Create: `Portals/consumer-complaints-admin/src/app/core/workflow-list.ts`

**Interfaces:**
- Consumes: `environment.apiBaseUrl`, `SUCCESS` / `FAILURE`
- Produces: `listWorkflows(http, ctx): Promise<number>`; types `WorkflowListEntry`, `WorkflowListCtx`

- [ ] **Step 1: Write failing workflow-list spec**

```typescript
import { TestBed } from '@angular/core/testing';
import { HttpClient, provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { FAILURE, SUCCESS } from './return-codes';
import { listWorkflows, WorkflowListCtx } from './workflow-list';

describe('listWorkflows', () => {
  let http: HttpClient;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    http = TestBed.inject(HttpClient);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('maps 200 list to SUCCESS and workflows', async () => {
    const ctx: WorkflowListCtx = { req: {}, resp: { workflows: [], error: '' } };
    const pending = listWorkflows(http, ctx);
    const req = httpMock.expectOne('/api/workflows');
    expect(req.request.method).toBe('GET');
    req.flush([
      {
        id: 'w1',
        workflow_name: 'download_cfpb_all',
        engine_type: 'apache_airflow',
        engine_workflow_id: 'download_cfpb_all',
        enabled: true,
      },
    ]);
    await expect(pending).resolves.toBe(SUCCESS);
    expect(ctx.resp.workflows.length).toBe(1);
    expect(ctx.resp.workflows[0].workflow_name).toBe('download_cfpb_all');
    expect(ctx.resp.error).toBe('');
  });

  it('maps HTTP error to FAILURE without inventing workflows', async () => {
    const ctx: WorkflowListCtx = { req: {}, resp: { workflows: [], error: '' } };
    const pending = listWorkflows(http, ctx);
    httpMock.expectOne('/api/workflows').flush('boom', {
      status: 500,
      statusText: 'Server Error',
    });
    await expect(pending).resolves.toBe(FAILURE);
    expect(ctx.resp.workflows).toEqual([]);
    expect(ctx.resp.error.length).toBeGreaterThan(0);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

```bash
source ~/.nvm/nvm.sh && nvm use 22
npm run local:portal:admin:test -- --include='**/workflow-list.spec.ts'
```

Expected: FAIL (module missing).

- [ ] **Step 3: Implement `workflow-list.ts`**

```typescript
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { environment } from '../../environments/environment';
import { FAILURE, SUCCESS } from './return-codes';

export interface WorkflowListEntry {
  id: string;
  workflow_name: string;
  engine_type: string;
  engine_workflow_id: string;
  enabled: boolean;
}

export interface WorkflowListReq {}
export interface WorkflowListResp {
  workflows: WorkflowListEntry[];
  error: string;
}
export interface WorkflowListCtx {
  req: WorkflowListReq;
  resp: WorkflowListResp;
}

export async function listWorkflows(http: HttpClient, ctx: WorkflowListCtx): Promise<number> {
  const url = `${environment.apiBaseUrl}/workflows`;
  try {
    const workflows = await firstValueFrom(http.get<WorkflowListEntry[]>(url));
    ctx.resp.workflows = workflows ?? [];
    ctx.resp.error = '';
    return SUCCESS;
  } catch {
    ctx.resp.workflows = [];
    ctx.resp.error = 'Failed to load workflows';
    return FAILURE;
  }
}
```

- [ ] **Step 4: Run tests — expect PASS**

- [ ] **Step 5: Commit** `M02-0026 #65: add listWorkflows portal helper for D66`

---

### Task 2: `startWorkflow` helper (TDD)

**Files:**
- Create: `Portals/consumer-complaints-admin/src/app/core/start-workflow.spec.ts`
- Create: `Portals/consumer-complaints-admin/src/app/core/start-workflow.ts`

**Interfaces:**
- Consumes: `SUCCESS`, `FAILURE`, `INVALID_INPUT`
- Produces: `startWorkflow(http, ctx): Promise<number>` with `ctx.req.workflowId`, optional `ctx.req.mioId`, `ctx.resp.executionId`

- [ ] **Step 1: Write failing start-workflow spec**

```typescript
import { TestBed } from '@angular/core/testing';
import { HttpClient, provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { FAILURE, INVALID_INPUT, SUCCESS } from './return-codes';
import { startWorkflow, StartWorkflowCtx } from './start-workflow';

describe('startWorkflow', () => {
  let http: HttpClient;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    http = TestBed.inject(HttpClient);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('maps 202 to SUCCESS and executionId with mio_id body', async () => {
    const ctx: StartWorkflowCtx = {
      req: { workflowId: 'w1', mioId: 'm1' },
      resp: { executionId: '', error: '' },
    };
    const pending = startWorkflow(http, ctx);
    const req = httpMock.expectOne('/api/workflows/w1/start');
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ mio_id: 'm1' });
    req.flush({ execution_id: 'e1' }, { status: 202, statusText: 'Accepted' });
    await expect(pending).resolves.toBe(SUCCESS);
    expect(ctx.resp.executionId).toBe('e1');
    expect(ctx.resp.error).toBe('');
  });

  it('maps 422 to INVALID_INPUT', async () => {
    const ctx: StartWorkflowCtx = {
      req: { workflowId: 'w1', mioId: 'm1' },
      resp: { executionId: '', error: '' },
    };
    const pending = startWorkflow(http, ctx);
    httpMock.expectOne('/api/workflows/w1/start').flush(
      { detail: 'invalid request' },
      { status: 422, statusText: 'Unprocessable Entity' },
    );
    await expect(pending).resolves.toBe(INVALID_INPUT);
    expect(ctx.resp.executionId).toBe('');
    expect(ctx.resp.error.length).toBeGreaterThan(0);
  });

  it('maps other HTTP errors to FAILURE', async () => {
    const ctx: StartWorkflowCtx = {
      req: { workflowId: 'w1', mioId: 'm1' },
      resp: { executionId: '', error: '' },
    };
    const pending = startWorkflow(http, ctx);
    httpMock.expectOne('/api/workflows/w1/start').flush('boom', {
      status: 500,
      statusText: 'Server Error',
    });
    await expect(pending).resolves.toBe(FAILURE);
    expect(ctx.resp.error.length).toBeGreaterThan(0);
  });
});
```

- [ ] **Step 2: Run — expect FAIL**

- [ ] **Step 3: Implement `start-workflow.ts`**

```typescript
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { environment } from '../../environments/environment';
import { FAILURE, INVALID_INPUT, SUCCESS } from './return-codes';

export interface StartWorkflowReq {
  workflowId: string;
  mioId?: string;
}
export interface StartWorkflowResp {
  executionId: string;
  error: string;
}
export interface StartWorkflowCtx {
  req: StartWorkflowReq;
  resp: StartWorkflowResp;
}

interface StartWorkflowApiBody {
  execution_id: string;
}

export async function startWorkflow(http: HttpClient, ctx: StartWorkflowCtx): Promise<number> {
  const url = `${environment.apiBaseUrl}/workflows/${encodeURIComponent(ctx.req.workflowId)}/start`;
  const body =
    ctx.req.mioId !== undefined && ctx.req.mioId !== null && ctx.req.mioId !== ''
      ? { mio_id: ctx.req.mioId }
      : {};
  try {
    const data = await firstValueFrom(
      http.post<StartWorkflowApiBody>(url, body, { observe: 'body' }),
    );
    ctx.resp.executionId = data?.execution_id ?? '';
    ctx.resp.error = '';
    return SUCCESS;
  } catch (err) {
    ctx.resp.executionId = '';
    if (err instanceof HttpErrorResponse && err.status === 422) {
      ctx.resp.error = 'Invalid start request';
      return INVALID_INPUT;
    }
    ctx.resp.error = 'Failed to start workflow';
    return FAILURE;
  }
}
```

- [ ] **Step 4: Run — expect PASS**

- [ ] **Step 5: Commit** `M02-0026 #65: add startWorkflow portal helper for D68`

---

### Task 3: Imports page start + refresh UI (TDD)

**Files:**
- Modify: `imports-page.ts`, `imports-page.html`, `imports-page.css`, `imports-page.spec.ts`

**Interfaces:**
- Consumes: `listWorkflows`, `startWorkflow`, `loadMioStatus`, `SUCCESS`
- Produces: per-MIO select/start/refresh; `isStartDisabled(mio)`; selected workflow map

- [ ] **Step 1: Extend `imports-page.spec.ts` with failing cases**

Add tests (keep existing ones; after init flush both `/api/mios/status` and `/api/workflows` — order may vary; use `httpMock.match` or expect both):

```typescript
  function flushInit(
    status: unknown[] = [],
    workflows: unknown[] = [
      {
        id: 'w1',
        workflow_name: 'download_cfpb_all',
        engine_type: 'apache_airflow',
        engine_workflow_id: 'download_cfpb_all',
        enabled: true,
      },
    ],
  ): void {
    const pending = httpMock.match((r) => r.url.includes('/mios/status') || r.url.includes('/workflows'));
    for (const req of pending) {
      if (req.request.url.includes('/mios/status')) {
        req.flush(status);
      } else {
        req.flush(workflows);
      }
    }
  }

  it('disables Start when latest_ingest status is started', async () => {
    const fixture = TestBed.createComponent(ImportsPage);
    fixture.detectChanges();
    flushInit([
      {
        id: 'm1',
        name: 'Customer complaints all',
        description: null,
        latest_ingest: {
          id: 'i1',
          mio_id: 'm1',
          status: 'started',
          message: null,
          rows_loaded: null,
          batch_count: null,
          increment_marker: null,
          requested_at: '2026-11-14T00:00:00Z',
          started_at: '2026-11-14T00:01:00Z',
          finished_at: null,
          executions: [],
        },
      },
    ]);
    await settle();
    fixture.detectChanges();
    const btn = fixture.debugElement.query(By.css('[data-testid="mio-start-workflow"]'));
    expect(btn.nativeElement.disabled).toBe(true);
  });

  it('starts workflow with mio_id then refreshes status', async () => {
    const fixture = TestBed.createComponent(ImportsPage);
    fixture.detectChanges();
    flushInit([
      {
        id: 'm1',
        name: 'Customer complaints all',
        description: null,
        latest_ingest: null,
      },
    ]);
    await settle();
    fixture.detectChanges();
    const btn = fixture.debugElement.query(By.css('[data-testid="mio-start-workflow"]'));
    expect(btn.nativeElement.disabled).toBe(false);
    btn.nativeElement.click();
    await settle();
    const startReq = httpMock.expectOne('/api/workflows/w1/start');
    expect(startReq.request.method).toBe('POST');
    expect(startReq.request.body).toEqual({ mio_id: 'm1' });
    startReq.flush({ execution_id: 'e1' }, { status: 202, statusText: 'Accepted' });
    await settle();
    httpMock.expectOne('/api/mios/status').flush([
      {
        id: 'm1',
        name: 'Customer complaints all',
        description: null,
        latest_ingest: {
          id: 'i2',
          mio_id: 'm1',
          status: 'requested',
          message: null,
          rows_loaded: null,
          batch_count: null,
          increment_marker: null,
          requested_at: '2026-11-15T00:00:00Z',
          started_at: null,
          finished_at: null,
          executions: [],
        },
      },
    ]);
    await settle();
    fixture.detectChanges();
    expect(fixture.debugElement.query(By.css('.mio-status')).nativeElement.textContent).toContain(
      'requested',
    );
  });

  it('Refresh status reloads GET /mios/status', async () => {
    const fixture = TestBed.createComponent(ImportsPage);
    fixture.detectChanges();
    flushInit([
      {
        id: 'm1',
        name: 'Customer complaints all',
        description: null,
        latest_ingest: null,
      },
    ]);
    await settle();
    fixture.detectChanges();
    fixture.debugElement.query(By.css('[data-testid="mio-refresh-status"]')).nativeElement.click();
    await settle();
    httpMock.expectOne('/api/mios/status').flush([
      {
        id: 'm1',
        name: 'Customer complaints all',
        description: null,
        latest_ingest: {
          id: 'i3',
          mio_id: 'm1',
          status: 'completed',
          message: null,
          rows_loaded: 1,
          batch_count: null,
          increment_marker: null,
          requested_at: '2026-11-15T00:00:00Z',
          started_at: '2026-11-15T00:01:00Z',
          finished_at: '2026-11-15T00:02:00Z',
          executions: [],
        },
      },
    ]);
    await settle();
    fixture.detectChanges();
    expect(fixture.debugElement.query(By.css('.mio-status')).nativeElement.textContent).toContain(
      'completed',
    );
  });
```

Update existing tests to call `flushInit` (or flush both endpoints) so they still pass.

- [ ] **Step 2: Run page tests — expect FAIL**

- [ ] **Step 3: Implement page wiring**

`imports-page.ts` sketch:

```typescript
// signals: entries, error, loading, workflows, selectedByMio, startingMioIds, actionError
// ngOnInit: Promise.all listWorkflows + loadMioStatus; defaultSelected = download_cfpb_all or first enabled
// isStartDisabled(mio): no selection OR starting OR status in requested|started
// onStart(mio): startWorkflow then refreshStatus
// refreshStatus(): loadMioStatus only
```

HTML: inside `.mio-body`, after existing meta/executions:

```html
<div class="mio-actions">
  <label>
    Workflow
    <select
      data-testid="mio-workflow-select"
      [value]="selectedWorkflowId(mio.id)"
      (change)="onWorkflowChange(mio.id, $event)"
    >
      @for (wf of enabledWorkflows(); track wf.id) {
        <option [value]="wf.id">{{ wf.workflow_name }}</option>
      }
    </select>
  </label>
  <button
    type="button"
    data-testid="mio-start-workflow"
    [disabled]="isStartDisabled(mio)"
    (click)="onStart(mio)"
  >
    Start workflow
  </button>
  <button type="button" data-testid="mio-refresh-status" (click)="onRefresh()">
    Refresh status
  </button>
  @if (actionError()) {
    <p data-testid="mio-action-error" role="alert">{{ actionError() }}</p>
  }
</div>
```

- [ ] **Step 4: Run all portal tests — expect PASS**

- [ ] **Step 5: Commit** `M02-0026 #65: wire Imports start and refresh controls`

---

### Task 4: Docs D72 + verification

**Files:**
- Modify: `DESIGN.md`, `Milestone_02.md`, `PRODUCT_FEATURES.md`

- [ ] **Step 1: Add D72 to DESIGN.md** (after D71). Set next decision notes to D73. Soften D71 item (4) “No start button…” to note superseded by D72 for #65.

- [ ] **Step 2: Milestone_02.md** — next decision D73; note #65 open question closed as manual refresh (D72).

- [ ] **Step 3: PRODUCT_FEATURES.md** — portal start Done (#65 / D72); F1/F2 start Done; fix #64 refs from D70 → D71.

- [ ] **Step 4: Verify**

```bash
source ~/.nvm/nvm.sh && nvm use 22
npm run local:portal:admin:test
npm run local:portal:admin:build
```

Expected: both exit 0.

- [ ] **Step 5: Commit** `M02-0026 #65: record D72 portal start and refresh decision`
