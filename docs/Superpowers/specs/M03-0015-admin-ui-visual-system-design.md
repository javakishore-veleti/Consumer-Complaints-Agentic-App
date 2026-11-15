# M03-0015 (#135) Professional Admin UI visual system (shell + Imports)

Decisions: **D80** (primary), D65, D69 (chrome/routes; UI-kit ban withdrawn), D71, D72 in `Middleware/ConsumerComplaintsHandsOn/DESIGN.md`. Architecture: `ARCHITECTURE.md` §3.1.

## Goal

Give `Portals/consumer-complaints-admin` a **production** ops-console look: Tailwind CSS, Able Pro–class shell (primary-blue top bar, white left rail, white work area), shared alerts/forms, favicon and title. Keep live Middleware behavior and existing `data-testid`s. No fake analytics dashboard.

## Context

| Already built | Gap |
|---|---|
| D65 Angular 22 portal, `/api` proxy | Student gray CSS, system fonts, dashed accordion shell |
| D69 DataSets top + Imports left nav | Looks like a scaffold, not a product |
| D71/D72/#121 Imports list/start/refresh + real API errors | Error text is plain `<p>`; no alert/banner pattern |
| D80 recorded in DESIGN/ARCHITECTURE | Spec + implementation for this story |

## Approaches considered

| | Approach | Trade-off |
|---|---|---|
| A | Hand-rolled CSS tokens only | Allowed by withdrawn D69 wording; slow to look professional; weak form/alert kit |
| B (chosen) | **Tailwind CSS** + small shared UI primitives (alert, button, badge) + Able Pro–class layout | One modern kit; matches D80; no Material required |
| C | Bootstrap 5 theme | Faster “admin kit” look but dated; harder to match Able Pro blue shell crisply with Angular |

**Chosen: B.** Do not install Bootstrap alongside Tailwind.

## Design

### 1. Tooling

- Add Tailwind CSS v4 (or current stable Angular-compatible setup) to `Portals/consumer-complaints-admin`.
- Wire via `@tailwindcss/postcss` / project PostCSS (or the Angular 22 recommended Tailwind path at implement time).
- Global entry: `src/styles.css` with `@import "tailwindcss"` (or equivalent) plus CSS variables for tokens.
- Keep component CSS files only where Tailwind utilities are awkward; prefer utility classes in templates.

### 2. Design tokens (CSS variables → Tailwind theme)

| Token | Role | Target |
|---|---|---|
| `--cca-primary` | Top bar, primary buttons, active nav | Deep admin blue ≈ `#1e3a5f` |
| `--cca-primary-hover` | Hover | Slightly lighter blue |
| `--cca-surface` | Page / work area | `#f5f7fa` or white |
| `--cca-panel` | Cards / expandable rows | `#ffffff` |
| `--cca-ink` | Body text | Dark blue-gray ≈ `#1b2430` |
| `--cca-muted` | Secondary text | Soft slate (not gray chrome bars) |
| `--cca-success` / `--cca-warning` / `--cca-danger` / `--cca-info` | Status chips + alerts | Semantic greens/ambers/reds/blues |

No black full-chrome theme. No dashed `#9ca3af` accordion shell.

### 3. App shell

**Top bar (`app.html` / `app.css`):**

- Full-width bar using `--cca-primary`; brand left (“Consumer Complaints Admin” or short product mark).
- Primary nav link **DataSets** (`data-testid="top-nav-datasets"`) in light text; active state underlined / brighter.
- Document title in `index.html`: `Consumer Complaints Admin`.
- Favicon: replace default with a simple branded favicon (SVG or PNG under `public/` / `src`).

**DataSets layout (`datasets-layout.*`):**

- White left rail with clear active state for Imports (`data-testid="left-nav-imports"`).
- DB Ingest remains disabled stub (`data-testid="left-nav-db-ingest"`).
- Main content fills remaining width with comfortable padding.

**Home:** Match shell typography; short product intro + API base URL (existing content), not a widget dashboard.

### 4. Shared feedback + form primitives

Add small presentational helpers (standalone components or shared class recipes):

| Primitive | Use |
|---|---|
| Alert / banner | `error`, `actionError`, success (optional after start), info |
| Badge / chip | Ingest status from API verbatim; “No ingest yet” when null |
| Button | Primary (start), secondary (refresh); disabled + loading opacity |
| Select / label | Workflow picker |

Errors still come from `http-error-message` / `ctx.resp.error` — **never invent status enums**.

### 5. Imports page

- Keep `data-testid="imports-accordion-shell"`, `mio-accordion`, `mio-workflow-select`, `mio-start-workflow`, `mio-refresh-status`, `mio-status-loading`, `mio-status-error`, `mio-action-error`.
- Replace dashed shell with a clean list of expandable panels (native `<details>` OK, or equivalent markup that keeps the same testids).
- Summary row: MIO name + status badge.
- Body: description, meta grid, executions, workflow select + Start + Refresh — same behavior as D72.
- Loading and empty states use the alert/typography system.

### 6. Tests

- Existing Imports unit tests must pass (testid + behavior).
- Add/adjust shallow tests if new alert component has logic; prefer pure presentational markup.
- No Middleware/Python changes.

### 7. Out of scope

- Fake earnings/charts/chat widgets.
- Angular Material (unless a later story chooses it).
- Bootstrap.
- Polling, auth, new API endpoints.
- Intellect / agent stats (later milestones).

## Files (expected)

| Path | Change |
|---|---|
| `Portals/consumer-complaints-admin/package.json` | Tailwind (+ PostCSS) deps |
| `src/styles.css`, Tailwind/PostCSS config as required | Tokens + Tailwind entry |
| `src/index.html` | Title + favicon |
| `src/app/app.html`, `app.css` | Top bar shell |
| `src/app/home/*` | Home polish |
| `src/app/datasets/datasets-layout.*` | Left rail |
| `src/app/datasets/imports/imports-page.*` | List + alerts + badges |
| Optional `src/app/shared/ui/*` | Alert/badge/button helpers |
| Spec/plan under `docs/Superpowers/` | This story |
| `DESIGN.md` / `ARCHITECTURE.md` | Already D80 (refine only if implement discovers a detail) |

## Acceptance mapping

| Acceptance | Covered by |
|---|---|
| D80 in DESIGN + ARCHITECTURE | Done before implement; keep in sync |
| Spec + plan before code | This file + plan |
| Tailwind + shell; dashed chrome gone | §§1–3, §5 |
| Alerts/forms; live Imports | §§4–5 |
| Favicon/title; tests; testids | §§3, 5–6 |

## Spec self-review

- No TBD placeholders.
- Single kit (Tailwind); Able Pro **chrome** only, not full dashboard widgets.
- Behavior unchanged; visual + feedback layer only.
