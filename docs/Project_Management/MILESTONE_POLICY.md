# Milestone policy — working product first

**Status:** Active (2026-11-19)  
**Applies to:** All new GitHub Milestones from M45 forward

## Rule

Every **GitHub Milestone** must deliver a **working product increment** an operator or user can demo — not documentation alone.

| Allowed as a milestone | Not allowed as a standalone milestone |
|---|---|
| Tables populated / queryable | “Write DataArchitecture.md only” |
| DAG runs end-to-end | “Refresh charter only” |
| API/UI path that works | “Append brainstorming only” |
| Registry + classification producing labels | Spec-only / ADR-only milestones |
| Vector catalog searchable | “Board hygiene” as the only outcome |

**Docs, ADRs, Superpowers specs/plans** still happen — as **stories or acceptance criteria inside** a product milestone (via the full 12-step Superpowers path → `docs/Superpowers/specs` + `plans`). They do **not** get their own milestone unless tied to a shippable product outcome.

## Done-when (product)

A milestone is closable only when:

1. A named runtime artifact works (Iceberg table with rows, DAG success, API response, UI screen, Chroma query, etc.)
2. Operator proof is recorded (command output, runbook step, or Golden case)
3. Stories used `/ccaa-story-start` → full Superpowers path → `/ccaa-story-complete`
4. Gate held: no product code without milestoned `[Story]` + story-start

## Current product spine (after M40 runtime/docs)

| Milestone | Working product outcome |
|---|---|
| **M45** | `raw.cfpb_complaints_3m` populated from Lift Zone; count reconcile |
| **M46** | `refined.cfpb_complaints_3m` with `signature_id` + ZIP-3; queryable |
| **M47** | Taxonomy DB + Mode 2 fills `semantic_signatures` for 3m U_sig |
| **M48** | `curated.cfpb_complaints_3m` Money Topics + parent org; DuckDB group-by works |
| **M49** | Chroma `cfpb_semantic_signatures` searchable (catalog, not 19M rows) |
| **M50** | Query AST Gateway answers ≥1 Golden query against Curated |
| **M51** | Admin Lakehouse workflows: UI → Middleware → Airflow → callback status (per-stage hydrate_*) |
| **M52+** | Internal MVP / edge / multi-cloud / B2B / consumer — each with a demoable slice |

M40 = Raw **docs** + Iceberg **Docker** only. **Raw hydrate = M45** (product).

## Doc-only milestones (M33–M44)

Historical board/docs milestones may remain for audit. **Do not open new ones.** Prefer closing completed doc stories and folding remaining architecture writing into the next **product** milestone’s Superpowers brainstorming/plan steps.
