# M01-0074 — README introduction, architecture summary, GitHub About

Decisions: documentation only (no DESIGN.md D##). Parent: Epic #1 · Feature #6. Next free decision unchanged.

## Problem

Clones see an empty GitHub **About** and a README that jumps straight into npm/container commands. The product purpose (CFPB complaints → admin Imports → async workflows → Mongo → later Intellect) and overall architecture are buried in long docs.

## Decision (summary)

1. Set repository **About** description: functional-first, lightly technical (portal, middleware, Airflow, pluggable ops store, Mongo complaints, Intellect later). No folder lists.
2. README gains **Introduction** and **Overall architecture** (capability / data-flow narrative + enterprise diagram image). Keep Superpowers CAUTION and Development tooling below.
3. Diagram: solid connectors only; committed at `docs/Design/ccaa-enterprise-architecture.jpg`.
4. Do **not** paste Middleware folder trees into README (those stay in ARCHITECTURE.md).

## Acceptance mapping

| Criterion | Where |
|---|---|
| About description | `gh repo edit --description` |
| Introduction + architecture | `README.md` |
| Enterprise image | `docs/Design/ccaa-enterprise-architecture.jpg` |
| Spec/plan | this file + plan |
| Milestone | `Milestone_01.md` Phase 8 |
