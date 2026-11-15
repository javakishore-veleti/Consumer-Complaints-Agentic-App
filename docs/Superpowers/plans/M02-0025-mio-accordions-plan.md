# M02-0025 MIO accordions with status from the API Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fill the Imports accordion shell with one expandable panel per MIO whose status comes only from `GET /mios/status`.

**Architecture:** `loadMioStatus(ctx)` uses Angular `HttpClient` against `environment.apiBaseUrl + '/mios/status'`, maps HTTP outcomes to D65 return codes, and puts the D61 JSON list on `ctx.resp`. `ImportsPage` loads on init and renders native `<details>` panels; it never invents status text.

**Tech Stack:** Angular 22 standalone, HttpClient, Vitest via `@angular/build:unit-test`, Node 22 via nvm.

## Global Constraints

- Spec: `docs/Superpowers/specs/M02-0025-mio-accordions-design.md`. Decisions: D5, D54, D61, D65, D69, **D71**.
- Work only under `.worktrees/m02-0025-mio-accordions` on branch `m02-0025-mio-accordions-with-status`.
- Use Node 22 (`nvm use 22`) before every `ng` / `npm` command.
- Commit messages: `M02-0025 #64: <imperative summary>` (single line). Author from git config (javakishore-veleti). Strip AI trailers before push.
- Do not add a start-workflow button or polling. Do not add Angular Material or new npm dependencies.
- Do not change Python / Middleware (endpoint already exists).

---

## File map

| Path | Responsibility |
|---|---|
| `Portals/consumer-complaints-admin/src/app/core/mio-status.ts` | D61-shaped types + `loadMioStatus` |
| `Portals/consumer-complaints-admin/src/app/core/mio-status.spec.ts` | HttpClientTesting for SUCCESS/FAILURE |
| `Portals/consumer-complaints-admin/src/app/app.config.ts` | `provideHttpClient()` |
| `Portals/consumer-complaints-admin/src/app/datasets/imports/imports-page.ts` | Load + signals |
| `Portals/consumer-complaints-admin/src/app/datasets/imports/imports-page.html` | Accordion panels |
| `Portals/consumer-complaints-admin/src/app/datasets/imports/imports-page.css` | Panel styles |
| `Portals/consumer-complaints-admin/src/app/datasets/imports/imports-page.spec.ts` | Page render tests |
| `Middleware/ConsumerComplaintsHandsOn/DESIGN.md` | D70; next D71 |
| `docs/Project_Management/Issues/Milestone_02.md` | next decision D72; workflow |
| `docs/PRODUCT_FEATURES.md` | F1/F2 / portal status note |

---

### Task 1: Failing tests for `loadMioStatus`

**Files:**
- Create: `Portals/consumer-complaints-admin/src/app/core/mio-status.spec.ts`
- Create: `Portals/consumer-complaints-admin/src/app/core/mio-status.ts` (minimal stub only after red)

**Interfaces:**
- Consumes: `environment.apiBaseUrl`, `SUCCESS` / `FAILURE` from `return-codes.ts`
- Produces: `loadMioStatus(http, ctx): Promise<number>`; types `MioStatusEntry`, `MioStatusCtx`

- [ ] **Step 1: Write failing mio-status spec**

```typescript
import { TestBed } from '@angular/core/testing';
import { HttpClient, provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { FAILURE, SUCCESS } from './return-codes';
import { loadMioStatus, MioStatusCtx } from './mio-status';

describe('loadMioStatus', () => {
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

  it('maps 200 list to SUCCESS and entries', async () => {
    const ctx: MioStatusCtx = { req: {}, resp: { entries: [], error: '' } };
    const pending = loadMioStatus(http, ctx);
    const req = httpMock.expectOne('/api/mios/status');
    expect(req.request.method).toBe('GET');
    req.flush([
      {
        id: 'm1',
        name: 'Customer complaints 3 months 2026',
        description: 'seed',
        latest_ingest: {
          id: 'i1',
          mio_id: 'm1',
          status: 'failed',
          message: 'disk full',
          rows_loaded: null,
          batch_count: null,
          increment_marker: null,
          requested_at: '2026-11-14T00:00:00Z',
          started_at: null,
          finished_at: null,
          executions: [],
        },
      },
    ]);
    await expect(pending).resolves.toBe(SUCCESS);
    expect(ctx.resp.entries.length).toBe(1);
    expect(ctx.resp.entries[0].latest_ingest?.status).toBe('failed');
    expect(ctx.resp.entries[0].latest_ingest?.message).toBe('disk full');
    expect(ctx.resp.error).toBe('');
  });

  it('maps HTTP error to FAILURE without inventing entries', async () => {
    const ctx: MioStatusCtx = { req: {}, resp: { entries: [], error: '' } };
    const pending = loadMioStatus(http, ctx);
    httpMock.expectOne('/api/mios/status').flush('boom', {
      status: 500,
      statusText: 'Server Error',
    });
    await expect(pending).resolves.toBe(FAILURE);
    expect(ctx.resp.entries).toEqual([]);
    expect(ctx.resp.error.length).toBeGreaterThan(0);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run (from repo root, Node 22):

```bash
source ~/.nvm/nvm.sh && nvm use 22
npm run local:portal:admin:test -- --include='**/mio-status.spec.ts'
```

Expected: FAIL (module `./mio-status` missing or `loadMioStatus` undefined).

- [ ] **Step 3: Minimal `mio-status.ts` implementation**

```typescript
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { environment } from '../../environments/environment';
import { FAILURE, SUCCESS } from './return-codes';

export interface MioStatusExecution {
  id: string;
  workflow_id: string;
  workflow_name: string;
  engine_type: string;
  engine_workflow_id: string;
  engine_run_id: string | null;
  status: string;
  message: string | null;
  mios_ingest_log_id: string | null;
  requested_at: string;
  started_at: string | null;
  finished_at: string | null;
}

export interface MioStatusIngest {
  id: string;
  mio_id: string;
  status: string;
  message: string | null;
  rows_loaded: number | null;
  batch_count: number | null;
  increment_marker: string | null;
  requested_at: string;
  started_at: string | null;
  finished_at: string | null;
  executions: MioStatusExecution[];
}

export interface MioStatusEntry {
  id: string;
  name: string;
  description: string | null;
  latest_ingest: MioStatusIngest | null;
}

export interface MioStatusReq {}
export interface MioStatusResp {
  entries: MioStatusEntry[];
  error: string;
}
export interface MioStatusCtx {
  req: MioStatusReq;
  resp: MioStatusResp;
}

export async function loadMioStatus(http: HttpClient, ctx: MioStatusCtx): Promise<number> {
  const url = `${environment.apiBaseUrl}/mios/status`;
  try {
    const entries = await firstValueFrom(http.get<MioStatusEntry[]>(url));
    ctx.resp.entries = entries ?? [];
    ctx.resp.error = '';
    return SUCCESS;
  } catch {
    ctx.resp.entries = [];
    ctx.resp.error = 'Failed to load MIO status';
    return FAILURE;
  }
}
```

- [ ] **Step 4: Run tests — expect PASS**

```bash
npm run local:portal:admin:test -- --include='**/mio-status.spec.ts'
```

- [ ] **Step 5: Commit**

```bash
git add Portals/consumer-complaints-admin/src/app/core/mio-status.ts \
  Portals/consumer-complaints-admin/src/app/core/mio-status.spec.ts
git commit -m "M02-0025 #64: add loadMioStatus ctx helper for GET /mios/status"
```

Strip AI trailers if present via `commit-tree` / `update-ref`.

---

### Task 2: Failing Imports page tests, then wire accordions

**Files:**
- Modify: `imports-page.spec.ts`, `imports-page.ts`, `imports-page.html`, `imports-page.css`
- Modify: `app.config.ts` (`provideHttpClient`)

**Interfaces:**
- Consumes: `loadMioStatus`, `MioStatusEntry`
- Produces: rendered `[data-testid="mio-accordion"]` panels

- [ ] **Step 1: Replace imports-page.spec.ts with failing accordion tests**

```typescript
import { TestBed } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { HttpClient, provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ImportsPage } from './imports-page';

describe('ImportsPage', () => {
  let httpMock: HttpTestingController;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ImportsPage],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('renders the accordion shell host', () => {
    const fixture = TestBed.createComponent(ImportsPage);
    fixture.detectChanges();
    httpMock.expectOne('/api/mios/status').flush([]);
    fixture.detectChanges();
    const host = fixture.debugElement.query(By.css('[data-testid="imports-accordion-shell"]'));
    expect(host).toBeTruthy();
  });

  it('renders one accordion per MIO with API status verbatim', async () => {
    const fixture = TestBed.createComponent(ImportsPage);
    fixture.detectChanges();
    httpMock.expectOne('/api/mios/status').flush([
      {
        id: 'm1',
        name: 'Customer complaints 3 months 2026',
        description: null,
        latest_ingest: {
          id: 'i1',
          mio_id: 'm1',
          status: 'failed',
          message: 'disk full',
          rows_loaded: null,
          batch_count: null,
          increment_marker: null,
          requested_at: '2026-11-14T00:00:00Z',
          started_at: null,
          finished_at: null,
          executions: [],
        },
      },
      {
        id: 'm2',
        name: 'Customer complaints all',
        description: null,
        latest_ingest: null,
      },
    ]);
    await fixture.whenStable();
    fixture.detectChanges();
    const panels = fixture.debugElement.queryAll(By.css('[data-testid="mio-accordion"]'));
    expect(panels.length).toBe(2);
    expect(panels[0].nativeElement.textContent).toContain('Customer complaints 3 months 2026');
    expect(panels[0].nativeElement.textContent).toContain('failed');
    expect(panels[0].nativeElement.textContent).toContain('disk full');
    expect(panels[1].nativeElement.textContent).toContain('No ingest yet');
  });

  it('shows load error without fabricating status rows', async () => {
    const fixture = TestBed.createComponent(ImportsPage);
    fixture.detectChanges();
    httpMock.expectOne('/api/mios/status').flush('boom', {
      status: 500,
      statusText: 'Server Error',
    });
    await fixture.whenStable();
    fixture.detectChanges();
    expect(fixture.debugElement.queryAll(By.css('[data-testid="mio-accordion"]')).length).toBe(0);
    const err = fixture.debugElement.query(By.css('[data-testid="mio-status-error"]'));
    expect(err).toBeTruthy();
    expect(err.nativeElement.textContent.length).toBeGreaterThan(0);
  });
});
```

- [ ] **Step 2: Run — expect FAIL** (no panels / error testid)

```bash
npm run local:portal:admin:test -- --include='**/imports-page.spec.ts'
```

- [ ] **Step 3: Implement page + `provideHttpClient`**

`app.config.ts`:

```typescript
import { ApplicationConfig, provideBrowserGlobalErrorListeners } from '@angular/core';
import { provideHttpClient } from '@angular/common/http';
import { provideRouter } from '@angular/router';
import { routes } from './app.routes';

export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),
    provideRouter(routes),
    provideHttpClient(),
  ],
};
```

`imports-page.ts`:

```typescript
import { Component, OnInit, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { loadMioStatus, MioStatusCtx, MioStatusEntry } from '../../core/mio-status';
import { SUCCESS } from '../../core/return-codes';

@Component({
  selector: 'app-imports-page',
  templateUrl: './imports-page.html',
  styleUrl: './imports-page.css',
})
export class ImportsPage implements OnInit {
  private readonly http = inject(HttpClient);
  protected readonly entries = signal<MioStatusEntry[]>([]);
  protected readonly error = signal('');
  protected readonly loading = signal(true);

  async ngOnInit(): Promise<void> {
    const ctx: MioStatusCtx = { req: {}, resp: { entries: [], error: '' } };
    const code = await loadMioStatus(this.http, ctx);
    this.loading.set(false);
    if (code === SUCCESS) {
      this.entries.set(ctx.resp.entries);
      this.error.set('');
    } else {
      this.entries.set([]);
      this.error.set(ctx.resp.error || 'Failed to load MIO status');
    }
  }
}
```

`imports-page.html`:

```html
<section aria-labelledby="imports-heading">
  <h1 id="imports-heading">Imports</h1>
  <p>Download status for each managed information object.</p>
  @if (loading()) {
    <p data-testid="mio-status-loading">Loading MIO status…</p>
  }
  @if (error()) {
    <p data-testid="mio-status-error" role="alert">{{ error() }}</p>
  }
  <div
    data-testid="imports-accordion-shell"
    class="accordion-shell"
    role="region"
    aria-label="MIO accordion shell"
  >
    @for (mio of entries(); track mio.id) {
      <details data-testid="mio-accordion" class="mio-accordion">
        <summary>
          <span class="mio-name">{{ mio.name }}</span>
          <span class="mio-status">
            @if (mio.latest_ingest; as ingest) {
              {{ ingest.status }}
            } @else {
              No ingest yet
            }
          </span>
        </summary>
        <div class="mio-body">
          @if (mio.description) {
            <p>{{ mio.description }}</p>
          }
          @if (mio.latest_ingest; as ingest) {
            @if (ingest.message) {
              <p class="mio-message">{{ ingest.message }}</p>
            }
            <dl class="mio-meta">
              <div><dt>Requested</dt><dd>{{ ingest.requested_at }}</dd></div>
              @if (ingest.started_at) {
                <div><dt>Started</dt><dd>{{ ingest.started_at }}</dd></div>
              }
              @if (ingest.finished_at) {
                <div><dt>Finished</dt><dd>{{ ingest.finished_at }}</dd></div>
              }
              @if (ingest.rows_loaded !== null && ingest.rows_loaded !== undefined) {
                <div><dt>Rows loaded</dt><dd>{{ ingest.rows_loaded }}</dd></div>
              }
            </dl>
            @if (ingest.executions.length) {
              <ul class="mio-executions">
                @for (ex of ingest.executions; track ex.id) {
                  <li>
                    {{ ex.workflow_name }} — {{ ex.status }}
                    @if (ex.message) {
                      ({{ ex.message }})
                    }
                  </li>
                }
              </ul>
            }
          }
        </div>
      </details>
    }
  </div>
</section>
```

Extend `imports-page.css` with `.mio-accordion`, `.mio-name`, `.mio-status`, `.mio-body` spacing (plain CSS only).

- [ ] **Step 4: Run portal tests — expect PASS**

```bash
npm run local:portal:admin:test
npm run local:portal:admin:build
```

- [ ] **Step 5: Commit**

```bash
git add Portals/consumer-complaints-admin/src/app/app.config.ts \
  Portals/consumer-complaints-admin/src/app/datasets/imports/
git commit -m "M02-0025 #64: render MIO accordions from GET /mios/status"
```

---

### Task 3: Record D70 and product docs

**Files:**
- Modify: `Middleware/ConsumerComplaintsHandsOn/DESIGN.md` (append D70 after D69)
- Modify: `docs/Project_Management/Issues/Milestone_02.md` (next decision **D71**)
- Modify: `docs/PRODUCT_FEATURES.md` (portal / F1 / F2 notes)

- [ ] **Step 1: Add D70 row** (exact decision text from the design doc summary).
- [ ] **Step 2: Set next decision to D71** in Milestone_02.md.
- [ ] **Step 3: PRODUCT_FEATURES** — portal row: MIO status [Done] (#64); start still Planned (#65). F1 note Imports status wired; F2 status-from-API slice Done for display.
- [ ] **Step 4: Commit**

```bash
git add Middleware/ConsumerComplaintsHandsOn/DESIGN.md \
  docs/Project_Management/Issues/Milestone_02.md \
  docs/PRODUCT_FEATURES.md
git commit -m "M02-0025 #64: record D70 MIO accordion status decision"
```

---

## Self-review

1. **Spec coverage:** D70 load/render/error/null-ingest/no-guess → Tasks 1–2; docs → Task 3; no start button → constrained out.
2. **Placeholders:** none.
3. **Types:** `MioStatusEntry` / `latest_ingest` / `executions` match D61 / OpenAPI field names used in tests and templates.
