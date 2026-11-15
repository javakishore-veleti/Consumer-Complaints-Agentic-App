# M02-0024 DataSets top menu and Imports left navigation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add DataSets top menu and Imports left navigation (accordion shell) to `Portals/consumer-complaints-admin` so navigation works without MIO status or start-workflow UI.

**Architecture:** Root `App` hosts a plain-CSS top bar (brand + DataSets). A `DatasetsLayout` child route owns the left rail (Imports active, DB Ingest disabled). `ImportsPage` is an empty accordion host for #64. No Material, no API calls (D65, D68).

**Tech Stack:** Angular 22 standalone components, Angular Router, Vitest via `@angular/build:unit-test`, Node 22 via nvm.

## Global Constraints

- Spec: `docs/Superpowers/specs/M02-0024-datasets-top-menu-design.md`. Decisions: D5, D13, D54, D65, **D68**.
- Work only under `.worktrees/m02-0024-datasets-top-menu` on branch `m02-0024-datasets-top-menu-and-imports`.
- Use Node 22 (`nvm use 22`) before every `ng` / `npm` command.
- Commit messages: `M02-0024 #63: <imperative summary>` (single line). Author from git config (javakishore-veleti). Strip AI trailers before push.
- Do not wire `/mios/status` or a start button. Do not enable DB Ingest beyond a disabled left-nav stub.
- Do not add Angular Material or new npm dependencies.

---

## File map

| Path | Responsibility |
|---|---|
| `Portals/consumer-complaints-admin/src/app/app.ts` | Import `RouterLink`; keep outlet |
| `Portals/consumer-complaints-admin/src/app/app.html` | Top bar: brand, DataSets `routerLink` |
| `Portals/consumer-complaints-admin/src/app/app.css` | Top bar styles |
| `Portals/consumer-complaints-admin/src/app/app.routes.ts` | `/`, `/datasets` layout + redirect + imports |
| `Portals/consumer-complaints-admin/src/app/app.spec.ts` | Assert DataSets top link |
| `Portals/consumer-complaints-admin/src/app/datasets/datasets-layout.ts` | Left nav + child outlet |
| `Portals/consumer-complaints-admin/src/app/datasets/datasets-layout.html` | Imports link; disabled DB Ingest |
| `Portals/consumer-complaints-admin/src/app/datasets/datasets-layout.css` | Left rail layout |
| `Portals/consumer-complaints-admin/src/app/datasets/datasets-layout.spec.ts` | Left nav assertions |
| `Portals/consumer-complaints-admin/src/app/datasets/imports/imports-page.ts` | Accordion shell page |
| `Portals/consumer-complaints-admin/src/app/datasets/imports/imports-page.html` | Shell host markup |
| `Portals/consumer-complaints-admin/src/app/datasets/imports/imports-page.css` | Minimal page styles |
| `Portals/consumer-complaints-admin/src/app/datasets/imports/imports-page.spec.ts` | Shell host assertions |
| `Middleware/ConsumerComplaintsHandsOn/DESIGN.md` | D68; next D69 |
| `docs/Project_Management/Issues/Milestone_02.md` | next decision D69; workflow rows |
| `docs/PRODUCT_FEATURES.md` | F1 / portal nav note |

---

### Task 1: Failing tests for top menu, left nav, and Imports shell

**Files:**
- Create: `Portals/consumer-complaints-admin/src/app/datasets/datasets-layout.spec.ts`
- Create: `Portals/consumer-complaints-admin/src/app/datasets/imports/imports-page.spec.ts`
- Modify: `Portals/consumer-complaints-admin/src/app/app.spec.ts`

**Interfaces:**
- Consumes: existing `App`, `routes` (will be extended in Task 2)
- Produces: failing specs that define the shell contract

- [ ] **Step 1: Write failing App top-menu test**

Replace `app.spec.ts` with:

```typescript
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { By } from '@angular/platform-browser';
import { App } from './app';
import { routes } from './app.routes';

describe('App', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [App],
      providers: [provideRouter(routes)],
    }).compileComponents();
  });

  it('should create the app', () => {
    const fixture = TestBed.createComponent(App);
    expect(fixture.componentInstance).toBeTruthy();
  });

  it('exposes a DataSets top link to the datasets area', () => {
    const fixture = TestBed.createComponent(App);
    fixture.detectChanges();
    const link = fixture.debugElement.query(By.css('a[data-testid="top-nav-datasets"]'));
    expect(link).toBeTruthy();
    expect(link.nativeElement.textContent.trim()).toBe('DataSets');
    expect(link.attributes['routerLink'] ?? link.nativeElement.getAttribute('href')).toMatch(
      /\/datasets/,
    );
  });
});
```

- [ ] **Step 2: Write failing DatasetsLayout and ImportsPage specs**

`datasets-layout.spec.ts`:

```typescript
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { By } from '@angular/platform-browser';
import { DatasetsLayout } from './datasets-layout';

describe('DatasetsLayout', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [DatasetsLayout],
      providers: [provideRouter([])],
    }).compileComponents();
  });

  it('shows Imports as a router link and DB Ingest as disabled', () => {
    const fixture = TestBed.createComponent(DatasetsLayout);
    fixture.detectChanges();
    const imports = fixture.debugElement.query(By.css('a[data-testid="left-nav-imports"]'));
    expect(imports).toBeTruthy();
    expect(imports.nativeElement.textContent.trim()).toBe('Imports');

    const dbIngest = fixture.debugElement.query(By.css('[data-testid="left-nav-db-ingest"]'));
    expect(dbIngest).toBeTruthy();
    expect(dbIngest.nativeElement.textContent.trim()).toBe('DB Ingest');
    expect(
      dbIngest.nativeElement.getAttribute('aria-disabled') === 'true' ||
        dbIngest.nativeElement.hasAttribute('disabled'),
    ).toBe(true);
  });
});
```

`imports-page.spec.ts`:

```typescript
import { TestBed } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { ImportsPage } from './imports-page';

describe('ImportsPage', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ImportsPage],
    }).compileComponents();
  });

  it('renders the accordion shell host for later MIO status', () => {
    const fixture = TestBed.createComponent(ImportsPage);
    fixture.detectChanges();
    const host = fixture.debugElement.query(By.css('[data-testid="imports-accordion-shell"]'));
    expect(host).toBeTruthy();
  });
});
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
export NVM_DIR="$HOME/.nvm"; . "$NVM_DIR/nvm.sh"; nvm use 22
cd Portals/consumer-complaints-admin
npm test -- --watch=false
```

Expected: FAIL (missing components / missing DataSets link / missing test ids).

- [ ] **Step 4: Commit the failing tests**

```bash
git add Portals/consumer-complaints-admin/src/app/app.spec.ts \
  Portals/consumer-complaints-admin/src/app/datasets/datasets-layout.spec.ts \
  Portals/consumer-complaints-admin/src/app/datasets/imports/imports-page.spec.ts
git commit -m "M02-0024 #63: add failing portal shell navigation tests"
```

---

### Task 2: Implement shell, routes, and docs (D68)

**Files:**
- Create: `datasets-layout.ts` / `.html` / `.css`
- Create: `imports-page.ts` / `.html` / `.css`
- Modify: `app.ts`, `app.html`, `app.css`, `app.routes.ts`
- Modify: `DESIGN.md` (D68), `Milestone_02.md` (next D69), `PRODUCT_FEATURES.md`

**Interfaces:**
- Consumes: failing tests from Task 1
- Produces: navigable shell; D68 recorded

- [ ] **Step 1: Implement ImportsPage**

`imports-page.ts`:

```typescript
import { Component } from '@angular/core';

@Component({
  selector: 'app-imports-page',
  templateUrl: './imports-page.html',
  styleUrl: './imports-page.css',
})
export class ImportsPage {}
```

`imports-page.html`:

```html
<section aria-labelledby="imports-heading">
  <h1 id="imports-heading">Imports</h1>
  <p>Download status for each managed information object will appear here.</p>
  <div
    data-testid="imports-accordion-shell"
    class="accordion-shell"
    role="region"
    aria-label="MIO accordion shell"
  ></div>
</section>
```

- [ ] **Step 2: Implement DatasetsLayout**

`datasets-layout.ts`:

```typescript
import { Component } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';

@Component({
  selector: 'app-datasets-layout',
  imports: [RouterLink, RouterLinkActive, RouterOutlet],
  templateUrl: './datasets-layout.html',
  styleUrl: './datasets-layout.css',
})
export class DatasetsLayout {}
```

`datasets-layout.html`:

```html
<div class="datasets-layout">
  <nav class="left-nav" aria-label="DataSets">
    <a
      data-testid="left-nav-imports"
      routerLink="/datasets/imports"
      routerLinkActive="active"
      >Imports</a
    >
    <span data-testid="left-nav-db-ingest" aria-disabled="true" class="disabled"
      >DB Ingest</span
    >
  </nav>
  <div class="datasets-content">
    <router-outlet />
  </div>
</div>
```

- [ ] **Step 3: Wire App chrome and routes**

`app.ts` imports `RouterLink` (and optionally `RouterLinkActive`).

`app.html`:

```html
<header class="top-bar">
  <a class="brand" routerLink="/">Consumer Complaints Admin</a>
  <nav class="top-nav" aria-label="Primary">
    <a
      data-testid="top-nav-datasets"
      routerLink="/datasets"
      routerLinkActive="active"
      >DataSets</a
    >
  </nav>
</header>
<main class="app-main">
  <router-outlet />
</main>
```

`app.routes.ts`:

```typescript
import { Routes } from '@angular/router';
import { Home } from './home/home';
import { DatasetsLayout } from './datasets/datasets-layout';
import { ImportsPage } from './datasets/imports/imports-page';

export const routes: Routes = [
  { path: '', component: Home },
  {
    path: 'datasets',
    component: DatasetsLayout,
    children: [
      { path: '', pathMatch: 'full', redirectTo: 'imports' },
      { path: 'imports', component: ImportsPage },
    ],
  },
];
```

Add minimal CSS for top bar, left rail, and accordion shell (no Material).

- [ ] **Step 4: Record D68 and product notes**

Append to `DESIGN.md` after D67:

```markdown
| D68 | **Admin portal chrome: DataSets top menu and Imports left navigation (accordion shell).** (1) Top bar exposes **DataSets** into `/datasets` (redirects to `/datasets/imports`). (2) Under DataSets, left nav lists **Imports** (routable) and **DB Ingest** (visible, disabled stub until its screen is built — D13). (3) Imports hosts an empty accordion shell for #64; no `/mios/status` and no start button in this story (D54). (4) Plain CSS standalone layout under D65 — no Angular Material. Spec `docs/Superpowers/specs/M02-0024-datasets-top-menu-design.md`. Built in story #63. | Gives #64/#65 a stable host without premature API or Material work. Decided without the user present (story #63); review and reverse if needed. |
```

Set Milestone_02 “next decision number” to **D69**. Update PRODUCT_FEATURES F1 / portal row to note nav shell Done for this slice.

- [ ] **Step 5: Run tests and build on Node 22**

```bash
export NVM_DIR="$HOME/.nvm"; . "$NVM_DIR/nvm.sh"; nvm use 22
npm run local:portal:admin:test
npm run local:portal:admin:build
```

Expected: both exit 0.

- [ ] **Step 6: Commit**

```bash
git add Portals/consumer-complaints-admin/src/app \
  Middleware/ConsumerComplaintsHandsOn/DESIGN.md \
  docs/Project_Management/Issues/Milestone_02.md \
  docs/PRODUCT_FEATURES.md \
  docs/Superpowers/specs/M02-0024-datasets-top-menu-design.md \
  docs/Superpowers/plans/M02-0024-datasets-top-menu-plan.md
git commit -m "M02-0024 #63: add DataSets top menu and Imports left nav shell"
```

---

## Self-review

1. **Spec coverage:** top DataSets link, left Imports + disabled DB Ingest, `/datasets` → imports, accordion shell, no API/start — all in Tasks 1–2.
2. **Placeholders:** none.
3. **Consistency:** routes and `data-testid` names match between tests and implementation; D68 is the only new decision.

## Execution

Execute inline in this session (user asked end-to-end, no questions). After Task 2 verification, open a PR closing #63; do not merge.
