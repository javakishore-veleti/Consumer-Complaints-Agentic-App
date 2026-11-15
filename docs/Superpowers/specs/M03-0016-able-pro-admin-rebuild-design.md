# M03-0016 (#137) Rebuild Admin UI from Able Pro reference (not restyle)

Decisions: **D82** (primary), D80 (Tailwind kit), D65, D69 routes, D71/D72/#121 live API. Architecture §3.1.

## Goal

Replace the student/restyled accordion shell with a **new Able Pro–class ops console**: top app bar, left sidebar, page header, panel rows, shared alerts/badges/buttons. Keep live Middleware behavior. No fake analytics widgets.

## Why #135 failed

#135 kept the old `<details>` / dashed-shell markup and only changed colors. D82 requires **new structure**, not CSS on heritage templates.

## Able Pro → CCAA mapping

| Able Pro chrome | CCAA Admin |
|---|---|
| Blue top bar + brand | Top bar: mark + “Consumer Complaints Admin”; nav **DataSets** |
| Left sidebar + section labels | Sidebar under DataSets: section **Navigation**; **Imports** active; **DB Ingest** disabled |
| Soft content canvas | Main area `--cca-surface` |
| White rounded cards | Imports list = card/panel rows |
| Status / priority chips | Ingest/exec status badges (API text verbatim) |
| Form controls in cards | Workflow select + Start / Refresh in expanded panel |
| Stats / charts / chat | **Out of scope** (Intellect later) |

## Approaches

| | Approach | Trade-off |
|---|---|---|
| A | More CSS on current HTML | Rejected (D82) |
| B (chosen) | New shell + sidebar + page-header + panel-row templates; shared UI primitives; Tailwind | Matches Able Pro chrome; keeps Angular + live API |
| C | Import a commercial Able Pro theme package | License/weight; overkill |

## Design

### 1. App shell (`app.*`)

- Fixed **56px** primary-blue top bar (`--cca-primary`).
- Left: square brand mark + product name (link `/`).
- Nav: DataSets (`data-testid="top-nav-datasets"`), light text, active underline.
- Main: full remaining height; soft surface background.
- Optional right-side icon placeholders (search/bell) as inert decorative slots for Able Pro parity — no fake counts.

### 2. DataSets layout (`datasets-layout.*`)

- Flex: **sidebar 260px** white + border-right; content flex-1.
- Sidebar top: compact identity block (“Admin” / “Operations”) — Able Pro profile strip analogue without requiring a photo.
- Section label **NAVIGATION** (uppercase, muted).
- Nav items with inline SVG icons + label; active = blue tint background.
- Keep `data-testid="left-nav-imports"` and `left-nav-db-ingest"`.

### 3. Shared primitives (`src/app/shared/ui/`)

| Component | Role |
|---|---|
| `UiAlert` | error / info / warning / success banners |
| `UiBadge` | status chip |
| `UiPageHeader` | title + subtitle + actions slot |

Buttons/selects: shared CSS classes in `styles.css` / component CSS (`.cca-btn-primary`, `.cca-btn-secondary`, `.cca-select`).

### 4. Imports page (rebuild)

- `UiPageHeader`: “Imports” + subtitle; Refresh as header secondary action optional (also keep per-row Refresh for D72).
- List host keeps `data-testid="imports-accordion-shell"` (contract) but class becomes `.cca-panel-list` — **no dashed border**.
- Each MIO: panel card (`data-testid="mio-accordion"`). Prefer accessible expand: `<details>` OK if chrome is card-like (header strip + body), or button-toggle equivalent with same testids.
- Summary: name + `UiBadge` (status or “No ingest yet”).
- Body: description; warning alert for message; meta grid; executions; action bar (workflow select, Start, Refresh) with Able Pro spacing.
- Loading / errors via `UiAlert` + existing testids.

### 5. Home

- Centered or left-aligned page header inside canvas; short ops intro; API base URL in muted meta — not a widget dashboard.

### 6. Tests

- Update Imports/layout specs only as needed for new markup; keep testids where possible.
- All portal unit tests green.

### 7. Out of scope

Fake charts, earnings, chat, Angular Material, Bootstrap, Middleware changes, inventing status enums.

## Files

| Path | Action |
|---|---|
| `src/app/shared/ui/*` | Create primitives |
| `src/app/app.html`, `app.css` | Rewrite shell |
| `src/app/datasets/datasets-layout.*` | Rewrite sidebar |
| `src/app/datasets/imports/imports-page.*` | Rewrite panels |
| `src/app/home/*` | Rewrite home |
| `src/styles.css` | Tokens + shared control classes |
| Spec/plan | This story |

## Spec self-review

No TBD. Rebuild only. Able Pro chrome without analytics clutter. Live API + testids preserved or migrated with tests.
