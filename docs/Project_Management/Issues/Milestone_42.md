# Milestone M42 - Project Charter refresh (DataArchitecture alignment)

**Scope:** Board docs only — refresh `PROJECT_CHARTER.md` to align with Mode 2 lakehouse architecture. No product code.

**Status: Open.** Stories left to build: 1 (awaiting commit-push + story-complete). Stories already done: 0.

**GitHub Milestone:** M42 - Project Charter refresh (DataArchitecture alignment) (api id 43)

## 1. Build order

| # | Issue | Key | Type | Title |
|---|---|---|---|---|
| 1 | #317 | M42-0001 | Story | Docs: refresh Project Charter for DataArchitecture alignment |

## 2. Superpowers workflow

| Issue | Step | Command | Status | Started | Completed |
|---|---|---|---|---|---|
| #317 | 1 | story-start | Board allow-list path (Project_Management) | 2026-11-18 20:04 | 2026-11-18 20:04 |
| #317 | 2 | worktree → implement | Done (charter rewrite on main board path) | 2026-11-18 20:04 | 2026-11-18 20:06 |
| #317 | 3 | commit-push | Not started | — | — |
| #317 | 4 | story-complete | Not started | — | — |

## 3. Alignment notes captured in charter

- Empirical Mode 2 (1.97M / 19.17M; U_sig 2,924 / 8,438; cross-cutting &lt; 1%)
- Lift → Raw → Refined → Curated Iceberg; database-first taxonomy (no flat YAML/CSV)
- Compact vector catalogs (~17k); Curated Iceberg = fact SoR
- Portfolio links M40 (done) and M41 (DataArchitecture expansion)
