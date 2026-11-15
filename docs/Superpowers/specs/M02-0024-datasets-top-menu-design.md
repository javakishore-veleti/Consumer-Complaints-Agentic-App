# M02-0024 (#63) DataSets top menu and Imports left navigation

Decisions: D5, D13, D54, D65 and **D68** in `Middleware/ConsumerComplaintsHandsOn/DESIGN.md`. Decided without the user present (D68); review and reverse if needed.

**Numbering note:** On `origin/main` the next free decision was **D68**. Story #42 (start-workflow) has not recorded a DESIGN.md decision on its branch; this story claims **D68** for the portal shell. If #42 later needs a decision, it must take the next free number after this merges.

## Goal

Give `Portals/consumer-complaints-admin` a navigable shell: top menu **DataSets**, left navigation **Imports** (with **DB Ingest** visible but not built yet), and an empty accordion host on the Imports screen so #64 can fill status without reshaping the chrome. No live MIO status API (#64) and no start button (#65).

## Approaches considered

| | Approach | Trade-off |
|---|---|---|
| A | Add Angular Material toolbar + sidenav | Extra dependency and theme work; D65 scaffold deliberately skipped Material polish |
| B (chosen) | Plain CSS shell: top nav + left nav + content, standalone routes | Matches scaffold simplicity (D54); zero new packages; enough chrome for #64/#65 |
| C | Only router links on the home page, no layout chrome | Fails PRODUCT_FEATURES F1 (top + left nav) and leaves #64 without a host |

## Decision D68 (summary)

1. **Top menu:** the admin app chrome shows a top-level **DataSets** item that routes into the DataSets area. Other top-level product areas are out of scope for this story.
2. **Left navigation:** under DataSets, left nav lists **Imports** (active, routable) and **DB Ingest** (visible, disabled stub — D13 screen comes later; no route required in this story).
3. **Routes:** `/datasets` redirects to `/datasets/imports`. Imports is a child of a DataSets layout that owns the left nav. Keep `/` as the #62 home/health page; it also shows the top menu so DataSets is always reachable.
4. **Accordion shell:** the Imports page renders a labeled host region (for example `role="region"` / heading “Imports”) with an empty accordion list container `#64` will populate. No MIO cards, no status text from the API, no start controls.
5. **Stack:** stay on D65 — standalone Angular components, plain CSS, no Angular Material, no API calls, Node engines unchanged.

## Layout

| Path | Role |
|---|---|
| `src/app/app.ts` / `app.html` | Root: top menu (brand + DataSets) + `router-outlet` |
| `src/app/datasets/datasets-layout.ts` | DataSets area: left nav + child `router-outlet` |
| `src/app/datasets/imports/imports-page.ts` | Imports screen: accordion shell placeholder |
| `src/app/app.routes.ts` | `/`, `/datasets` → redirect `imports`, `/datasets/imports` |
| `src/app/app.css` / layout CSS | Minimal top bar + left rail + content |

## Navigation behavior (acceptance)

- Clicking **DataSets** lands on Imports (`/datasets/imports`).
- On Imports, left nav highlights **Imports**; **DB Ingest** is present and not clickable (or `aria-disabled`).
- Imports content shows the accordion shell (empty host), not the home/health copy alone.
- Home (`/`) still serves the #62 health page and still exposes the DataSets top link.

## Tests

- Unit: App template exposes a DataSets link to `/datasets/imports` (or `/datasets` that redirects).
- Unit: Datasets layout exposes Imports link and a disabled DB Ingest control.
- Unit: Imports page exposes the accordion shell host (stable test id or role/heading).
- Router: `/datasets` redirects to `/datasets/imports`.
- Build: `npm run local:portal:admin:build` (Node 22) exits 0.
- Test: `npm run local:portal:admin:test` exits 0.

## Docs to update when built

| File | Change |
|---|---|
| `DESIGN.md` | D68 row; next decision D69 |
| `Milestone_02.md` | next decision D69; workflow rows for #63 as work proceeds |
| `docs/PRODUCT_FEATURES.md` | F1 / portal row note: nav shell in progress or Done for this slice |

## Out of scope

- Wiring `GET /mios/status` or rendering MIO accordions (#64).
- Start-workflow button / polling (#65).
- Enabling the DB Ingest screen (D13 later story).
- Angular Material, auth, additional top-level menus.
- Python / Middleware changes.
