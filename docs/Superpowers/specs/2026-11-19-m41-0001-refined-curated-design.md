# M41-0001 / #314 — DataArchitecture Refined + Curated Iceberg zones design

## Goal
Expand `docs/DataArchitecture.md` with full **Refined (Silver)** and **Curated (Gold)** Iceberg zone specifications while preserving existing Lift Zone + Raw/Bronze content.

## Empirical calibration (authoritative for this doc)

| Slice | N | U_prod | U_sig | % Cross-Cutting |
|---|---:|---:|---:|---:|
| 3-month | 1,970,702 | 55 | 2,924 | 0.345% |
| Full archive | 19,170,856 | 127 | 8,438 | 0.764% |

Mode snap: **Mode 2** (documented fully in M41-0003; referenced here for size targets).

## Design decisions

1. **Preserve, don't rewrite Lift/Raw.** Keep § Lift Zone and § Apache Iceberg Raw Data Zone (Bronze) text; only extend TOC, medallion overview, and purpose/scope.
2. **Refined = 24 columns.** Typed facts + ZIP-3 hygiene + deterministic `signature_id` = SHA-256 of normalized `product|sub_product|issue|sub_issue|tags`. No Money Topics on Silver.
3. **Curated = 31 columns.** All 24 Refined + Money Topics multi-label + parent org + tax/classifier versions. Size targets ~220 MB (3m) / ~2.0 GB (all). Vectors stay out of the fact table.
4. **Unidirectional flow.** Lift → Raw → Refined → Curated (Taxonomy/Vectors deferred to #315/#316).
5. **Docs only.** No Middleware / Portals / DAG / migration / product test edits.

## Out of scope
Database Taxonomy Control Plane schemas (#315); Mode 2 cascade, Vector DB Store, DAG plane, Query AST Gateway (#316).
