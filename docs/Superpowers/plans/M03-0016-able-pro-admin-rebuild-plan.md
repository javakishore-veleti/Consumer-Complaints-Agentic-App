# M03-0016 (#137) Able Pro Admin rebuild Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild Admin shell + Imports from Able Pro reference (D82), not a restyle.

**Architecture:** New shared UI primitives + rewritten app/datasets/imports/home templates; Tailwind + CCA tokens; live API unchanged.

**Tech Stack:** Angular 22, Tailwind CSS v4, Vitest.

## Global Constraints

- D82 rebuild — delete heritage dashed-accordion CSS approach.
- Keep or migrate `data-testid`s with tests.
- Never invent ingest status strings.
- No fake analytics widgets.
- Commit: `M03-0016 #137: <imperative summary>`.

---

### Task 1: Shared UI primitives + tokens

**Files:** create `Portals/consumer-complaints-admin/src/app/shared/ui/{ui-alert,ui-badge,ui-page-header}.*`; update `styles.css`

- [ ] Add `UiAlert`, `UiBadge`, `UiPageHeader` standalone components
- [ ] Extend `:root` tokens + `.cca-btn-*` / `.cca-select` in `styles.css`
- [ ] Commit `M03-0016 #137: add shared Able Pro UI primitives`

### Task 2: Shell + sidebar + home rewrite

**Files:** `app.html/css`, `datasets-layout.*`, `home.*`

- [ ] Rewrite top bar (Able Pro height/brand/nav)
- [ ] Rewrite 260px sidebar (identity + NAVIGATION + icons)
- [ ] Rewrite home with `UiPageHeader`
- [ ] Commit `M03-0016 #137: rebuild Admin shell and DataSets sidebar`

### Task 3: Imports panel rows

**Files:** `imports-page.html/css/ts` (+ spec if needed)

- [ ] Run Imports tests (baseline)
- [ ] Rewrite page with `UiPageHeader`, panel list, badges, alerts, action bar
- [ ] Tests green
- [ ] Commit `M03-0016 #137: rebuild Imports as Able Pro panel rows`

### Task 4: Verify + PR

- [ ] Full portal unit tests + build smoke
- [ ] Push branch; open PR; merge when green
