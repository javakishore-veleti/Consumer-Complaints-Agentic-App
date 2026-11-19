# M41-0001 Refined + Curated docs Implementation Plan

> **For agentic workers:** Docs-only story. Adapt TDD as Done-when evidence checks.

**Goal:** Expand `docs/DataArchitecture.md` with Refined (24-col) and Curated (31-col) Iceberg zone specs.

**Architecture:** Append Silver/Gold sections to the living DataArchitecture doc; keep Lift + Raw intact; update TOC and medallion overview; cite empirical Mode 2 calibration table.

**Tech Stack:** Markdown only (`docs/DataArchitecture.md`, Superpowers spec/plan, Milestone_41.md).

## Global Constraints

- Docs only — never edit Middleware/, Portals/, DAGs, migrations, feature tests, PRODUCT_FEATURES.md M53, or Milestone_53.md.
- Preserve existing Lift Zone + Raw/Bronze sections (no delete).
- Empirical numbers: 3m N=1970702 U_sig=2924; full N=19170856 U_sig=8438; Mode 2.

---

## Task 1: Expand DataArchitecture.md

**Files:** `docs/DataArchitecture.md`

- [ ] Update header/status + empirical calibration table
- [ ] TOC: add Refined + Curated sections; renumber Document control
- [ ] Medallion overview: name Silver/Gold responsibilities and unidirectional flow
- [ ] Add § Refined Data Zone (Silver): 24-column model, `signature_id`, ZIP-3 hygiene
- [ ] Add § Curated Data Zone (Gold): 31-column model, Money Topics + parent org, size targets
- [ ] Preserve Lift + Raw sections verbatim in substance

**Verify:** `rg -n 'Refined|Curated|signature_id|zip|24|31|Lift Zone|Raw Data Zone' docs/DataArchitecture.md`

## Task 2: Board + commit

- [ ] Milestone_41 Superpowers rows advanced via `ccaa-milestone-log`
- [ ] Commit message form `M41-0001 #314: <summary>`
