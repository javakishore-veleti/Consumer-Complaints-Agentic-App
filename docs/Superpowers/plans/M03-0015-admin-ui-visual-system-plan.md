# M03-0015 (#135) Admin UI visual system Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Production Admin shell + Imports polish with Tailwind (D80), keeping live API behavior and `data-testid`s.

**Architecture:** Tailwind v4 via PostCSS in the Angular admin app; CSS variables for Able Pro–class tokens; shared alert/badge class recipes; restyle app shell, datasets layout, home, Imports without Middleware changes.

**Tech Stack:** Angular 22, Tailwind CSS v4 (`@tailwindcss/postcss`), Vitest unit tests.

## Global Constraints

- Keep all existing `data-testid` values on Imports/nav.
- Never invent ingest/execution status strings.
- One kit: Tailwind only (no Bootstrap, Material not required).
- No fake analytics dashboard widgets.
- Commit message form: `M03-0015 #135: <imperative summary>`.

---

### Task 1: Tailwind + design tokens

**Files:**
- Modify: `Portals/consumer-complaints-admin/package.json`
- Create: `Portals/consumer-complaints-admin/.postcssrc.json`
- Modify: `Portals/consumer-complaints-admin/src/styles.css`
- Modify: `Portals/consumer-complaints-admin/src/index.html`
- Create: `Portals/consumer-complaints-admin/public/favicon.svg`

- [ ] **Step 1:** Install `tailwindcss` and `@tailwindcss/postcss` in the admin portal.
- [ ] **Step 2:** Add `.postcssrc.json` with `@tailwindcss/postcss` plugin; set `styles.css` to `@import "tailwindcss"` plus `:root` CCA tokens from D80.
- [ ] **Step 3:** Set document title and SVG favicon.
- [ ] **Step 4:** Commit `M03-0015 #135: add Tailwind and Admin design tokens`

### Task 2: App shell + DataSets rail + home

**Files:**
- Modify: `src/app/app.html`, `app.css`
- Modify: `src/app/datasets/datasets-layout.html`, `datasets-layout.css`
- Modify: `src/app/home/home.html`, `home.css`

- [ ] **Step 1:** Restyle top bar (primary blue), brand, DataSets nav.
- [ ] **Step 2:** Restyle left rail (white, active Imports, disabled DB Ingest).
- [ ] **Step 3:** Polish home page copy/layout to match tokens (no dashboard widgets).
- [ ] **Step 4:** Commit `M03-0015 #135: restyle Admin shell and DataSets rail`

### Task 3: Imports alerts, badges, expandable list

**Files:**
- Modify: `src/app/datasets/imports/imports-page.html`, `imports-page.css`
- Modify: `imports-page.spec.ts` only if needed for new markup (keep testids)

- [ ] **Step 1:** Run existing Imports tests (baseline green).
- [ ] **Step 2:** Replace dashed shell with panel list; status badges; alert banners for errors/loading; button/select styling. Keep all `data-testid`s.
- [ ] **Step 3:** Re-run Imports unit tests; fix until green.
- [ ] **Step 4:** Commit `M03-0015 #135: polish Imports list alerts and badges`

### Task 4: Verify + docs touch

- [ ] **Step 1:** `npm test` / portal unit tests from admin package; `ng build` smoke if cheap.
- [ ] **Step 2:** Confirm D80 / ARCHITECTURE §3.1 still accurate (tweak only if needed).
- [ ] **Step 3:** Commit any doc nits; push branch for PR.
