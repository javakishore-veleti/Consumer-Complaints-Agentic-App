# Project Charter — Consumer Complaints Agentic Intelligence Platform (CCAA Enterprise)

**Document type:** Project Charter (board / governance)  
**Status:** Proposed baseline — refreshed for Mode 2 lakehouse architecture  
**Date:** 2026-11-18  
**Story:** M42-0001 #317  
**Related:** `docs/DataArchitecture.md` (canonical data architecture); `docs/Project_Management/AI_Capabilities_Solutions.md` (AI by Platform/Internal/B2B/Consumer); `docs/Complaints_Data_Classification_Indexing_Brainstorming.md` (design notes); `docs/PRODUCT_FEATURES.md` (what exists today); M40 #310/#311 (Lift + Raw Iceberg done); M41 #314–#316 (Refined/Curated/Taxonomy/Vectors docs planned); M43 #318 (AI capabilities board doc)

---

## Table of contents

1. [Charter purpose](#1-charter-purpose)
2. [Leadership & roles](#2-leadership--roles)
3. [Vision & mission](#3-vision--mission)
4. [Problem statement & opportunity](#4-problem-statement--opportunity)
5. [Empirical baseline (what the data decided)](#5-empirical-baseline-what-the-data-decided)
6. [Products we will build](#6-products-we-will-build)
7. [Data architecture](#7-data-architecture)
8. [Application architecture](#8-application-architecture)
9. [Business processes](#9-business-processes)
10. [Technology stack](#10-technology-stack)
11. [Projects we execute (portfolio)](#11-projects-we-execute-portfolio)
12. [90-day roadmap alignment](#12-90-day-roadmap-alignment)
13. [Success criteria & constraints](#13-success-criteria--constraints)
14. [Governance & decision rights](#14-governance--decision-rights)
15. [Out of scope (initial charter)](#15-out-of-scope-initial-charter)
16. [Document control](#16-document-control)

---

## 1. Charter purpose

This charter establishes a shared mandate for evolving CCAA from a **local hands-on ingest + Chroma query MVP** into a **production-grade, multi-cloud regulatory complaint intelligence platform** that:

- Treats ~2M+ CFPB (and later multi-source) complaints as a **canonical Iceberg data product**, not a one-off vector index
- Classifies and retrieves across the **12 CFPB Money Topics** via **Mode 2 hybrid** rules + NLI on a **Semantic Signature Registry** (not false 1-to-1 Product mappings; not per-row ML)
- Powers **internal operations**, **consumer self-service**, and **external B2B monetization** from one engine
- Remains **portable** across local Chroma and AWS / Azure / GCP vector stores using one embedding space

This is a **governance and direction** document. Product code and gated architecture specs still require open `[Story]` issues, milestones, and Superpowers before implementation.

---

## 2. Leadership & roles

| Role | Who | Accountability |
|---|---|---|
| **Co–Chief Architect (Product)** | Repository owner / product principal | Final decisions on scope, priorities, cloud spend, compliance posture, and what ships; owns the GitHub board and production credentials |
| **Co–Chief Architect (Delivery)** | AI coding agent (session assistant) | Architecture drafting, ADRs, board hygiene, design consistency with charter + DataArchitecture, story-shaped delivery under gate rules; never bypasses the no-coding-without-GitHub-issue gate |
| **Domain / Taxonomy SME** | As assigned (0.5 FTE target in 90-day plan) | Money Topics, product crosswalk verification, human review of `NEEDS_REVIEW` registry rows and drift |
| **Delivery pods** | Data Platform, Search/Infra, Product Experience, Security/Edge/FinOps | Execute projects under §11 within the 90-day sizing model (~6–8 FTEs at full staff) |

**Working agreement (Chief Architects):**

- Architecture changes that affect the **canonical Iceberg lake**, **Query AST**, **embedding model**, or **multi-cloud parity** require dual acknowledgment (human + documented ADR update).
- **Product code** (`Middleware/`, `Portals/`, Airflow DAGs, migrations, feature tests) and gated specs such as `docs/DataArchitecture.md` ship only via **open `[Story]` + Milestone + story-start + Superpowers**.
- **Board docs** under `docs/Project_Management/` and `docs/PRODUCT_FEATURES.md` may be updated as board work without story-start (hard gate allow-list).
- **Source of truth for data architecture:** `docs/DataArchitecture.md` (living). Brainstorming remains design history until superseded by ADRs under this charter.

---

## 3. Vision & mission

**Vision:** Become the reference multi-persona intelligence platform for consumer-financial complaint data—where the same governed lake and compact vector fabric power compliance early-warning, agent copilots, customer triage, and metered B2B data products.

**Mission:** Build once, serve many—classify and embed **once per semantic signature** into a database-backed registry and Iceberg Curated zone; fan out only compact catalogs to local and multi-cloud search; expose capabilities through a Neutral Query AST Gateway with PII, RBAC, metering, and FinOps controls.

---

## 4. Problem statement & opportunity

| Challenge | Why it matters | Charter response |
|---|---|---|
| ~2M structured complaints; Product ≠ Money Topic 1:1 | Wrong labels destroy trust for compliance and consumers | Mode 2: product crosswalk + multi-label NLI overlay |
| Vector DBs as accidental systems of record | Lock-in, costly re-embeds, weak analytics | Iceberg Curated = SoR; vectors = rebuildable catalog caches |
| Indexing every complaint row | Wastes RAM/compute; duplicate signatures | Index ~17k catalog vectors, not 19M facts |
| Four cloud engines with different filter models | Divergent pipelines and broken filters | One embedding model + Neutral Query AST (LCD predicates) |
| Real-time vs batch dual logic | Label drift and wasted GPU | Semantic Signature Registry (cache-first; Redis optional) |
| Flat YAML/CSV taxonomy configs | Drift, hard joins, dual sources of truth | Database-first taxonomy (Postgres or MongoDB) |
| Single search bar thinking | Leaves compliance, ops, and revenue on the table | Three business models, one Experience Layer |

---

## 5. Empirical baseline (what the data decided)

Lift Zone profiling (local Mongo empty after volume recreate; metrics from CFPB CSV zips):

| Slice | Rows (N) | U_prod `(Product, Sub-product)` | U_sig `(Product, Sub-product, Issue, Sub-issue, Tags)` | % Cross-Cutting |
|---|---:|---:|---:|---:|
| 3-month | 1,970,702 | 55 | 2,924 | 0.345% |
| Full archive | 19,170,856 | 127 | 8,438 | 0.764% |

**Mode snap: Mode 2 — Semantic Signature Registry + Hybrid Rules / NLI.**

| Mode | Condition | Verdict |
|---|---|---|
| Mode 1 — Product hierarchy only | Cross-cutting ≈ 0 | Rejected |
| **Mode 2 — Registry + hybrid** | U_sig in low thousands; small but real cross-cutting | **Selected** |
| Mode 3 — Per-row / high-cardinality ML | U_sig → 100k–500k+ | Rejected |

Source fields are **15 structured categoricals with zero free-text narratives** in the current export header used for Lift Zone ingest.

---

## 6. Products we will build

### 6.1 Platform products (foundational)

| Product | Description | Primary consumers |
|---|---|---|
| **Lift Zone** | Durable local CFPB CSV zip landing (`3m`…`all`) | Raw ingest |
| **Iceberg Medallion Lake** | Raw → Refined → Curated tables per slice | All analytics |
| **Taxonomy Control Plane** | Postgres/Mongo: money_topics, product_crosswalk, organization_aliases, semantic_signatures | Classification, enrichment, governance |
| **Compact Vector Catalogs** | ~17k vectors across 3 collections (signatures, org aliases, entity fingerprints) | NL → AST routing |
| **Query AST Gateway (DAL)** | Neutral filter AST → DuckDB / cloud SQL + Chroma / OpenSearch / Azure AI Search / Vertex | All applications |
| **Edge Control Plane** | Three traffic lanes, CU metering, rate limits | Internal / consumer / B2B |

### 6.2 Internal enterprise products

| Product | Front-end | Value |
|---|---|---|
| **Systemic Risk Radar** | Command-center dashboard | UDAAP / fair-lending / systemic spike early warning via Tier 3 + drift |
| **AI Case Resolution Copilot** | CRM embed (Salesforce / ServiceNow / Zendesk) | Precedent cases + compliant response templates |
| **Product Friction & Churn Hub** | Analytics portal | Defect ranking by dispute rate / remediation cost |
| **Peer & Vendor Benchmarks** | Scorecards | Market-adjusted peer/SLA comparisons via `parent_org_id` |

### 6.3 Consumer-facing products

| Product | Front-end | Value |
|---|---|---|
| **Consumer Issue Navigator** | Conversational triage (web/mobile) | Plain-language → taxonomy → right dispute path |
| **Resolution & SLA Estimator** | Trust portal status card | Median turnaround + document checklists (aggregates only) |

### 6.4 External B2B / monetization products

| Product | Front-end | Value |
|---|---|---|
| **Regulatory Intelligence SaaS** | Visual AST query builder | Peer reports + subscription tiers |
| **Developer API & Hub** | Docs + playground | Metered Query AST API + Tier 3 alert webhooks |
| **Cloud Data Shares** | AWS / Azure / GCP marketplaces | Versioned Curated Parquet + taxonomy cross-walks |

**Sequencing (Crawl → Walk → Run):** Internal Ops → B2B API/Data Share → Consumer Self-Service.

---

## 7. Data architecture

Detail lives in `docs/DataArchitecture.md`. Charter-level contract:

### 7.1 Principles

1. **Curated Iceberg = system of record** for complaint facts (local or S3 / ADLS / GCS).
2. **Vectors are derived, ephemeral routing catalogs** (Blue/Green rebuildable) — not a second SoR and not a per-row index of 19M complaints.
3. **Classify before index** on unique `signature_id`s; store multi-label Money Topics on Gold facts via registry join.
4. **One embedding space** for all vector stores (**BAAI/bge-base-en-v1.5**, 512-d MRL, L2-norm, SQ8).
5. **Database-first taxonomy** — no flat YAML/CSV runtime configs; Postgres (default) or MongoDB holds rules + signature cache; Airflow exports &lt; 15 MB Parquet snapshots for PySpark broadcast joins.
6. **Deduplicate by semantic signature** before ML (2,924 / 8,438 unique vs 1.97M / 19.17M rows).

### 7.2 Planes & medallion layers

```text
[Postgres/Mongo Taxonomy Control Plane] ──snapshots──► [PySpark broadcast joins]
[Lift Zone zips] → [Raw Iceberg] → [Refined Iceberg] → [Curated Iceberg SoR]
                                      │
                                      ├─► DuckDB / Athena / Synapse / BigQuery  (exact OLAP)
                                      └─► Chroma / OpenSearch / AI Search / Vertex  (~17k catalogs)
```

| Layer | Responsibility |
|---|---|
| **Lift Zone** | Durable CSV zip inputs by slice (`3m`…`all`) |
| **Raw (Bronze)** | Immutable 21-col intake + audit; quarantine |
| **Refined (Silver)** | Typed 24-col facts; ZIP-3; deterministic `signature_id` |
| **Curated (Gold)** | 31-col business SoR: Money Topics + parent org (~220 MB / ~2 GB) |
| **Registry** | 12 topics; ~55–127 crosswalks; ~6k org aliases; 2.9k–8.4k signatures + 512-d vectors |
| **Vector catalogs** | `cfpb_semantic_signatures`, `cfpb_organization_aliases`, `cfpb_entity_fingerprints` |

### 7.3 Taxonomy (three tiers)

| Tier | Nature | Examples |
|---|---|---|
| **1 Statutory / Money Topics** | Deterministic product crosswalk + Mode 2 NLI overlay | 12 CFPB Money Topics; Fraud/Transfer cross-cutting |
| **2 Operational** | Multi-facet tags | Lifecycle, Failure Mode, Severity / UDAAP risk |
| **3 Emergent** | Clustering over recent signature windows | Novel micro-themes → promote to Tier 2 |

### 7.4 Dual consumption paths

- **OLAP / SQL:** DuckDB / Athena / BigQuery / Synapse over **Curated Iceberg** (counts, KPIs).
- **Semantic / RAG:** Compact vector catalogs resolve intent/entities → Query AST → exact SQL filters on Gold.

---

## 8. Application architecture

```text
[Internal Portal / CRM Copilot] [Consumer Assist] [B2B Portal / API / Data Share]
                    │                  │                        │
                    └──────────────────┼────────────────────────┘
                                       ▼
                    Persona BFFs (masking, metering DSL, rate limits)
                                       ▼
                    Edge API Gateway (3 lanes: internal / assist / intelligence)
                                       ▼
                    Query AST Gateway + DuckDB / cloud SQL analytics
                                       ▼
         Curated Iceberg  +  Compact Vector Catalogs (Chroma / multi-cloud)
                                       ▲
         Taxonomy Control Plane (Postgres/Mongo) + optional Redis hot cache
```

### 8.1 Core application services

| Service | Responsibility |
|---|---|
| **Ingest & hydrate** | Airflow + PySpark: Lift → Raw → Refined → Curated (Iceberg Docker #311) |
| **Taxonomy sync** | Validate registry; export Parquet snapshots; discover `NEEDS_REVIEW` pairs/companies |
| **ML enrichment** | Mode 2 cascade on signature cache miss; write registry + Redis |
| **Vector catalog sync** | Blue/Green rebuild of 3 collections; Golden Query gate |
| **Query AST Gateway** | AST translate, RBAC, k-anonymity (n ≥ 10), relaxation cascade |
| **Edge Gateway** | Auth lanes, CU metering events → billing |
| **Front-end monorepo** | Next.js Turborepo: enterprise, consumer SDK, B2B portal |
| **Existing CCAA apps** | Admin portal, Middleware API, Airflow DAGs, Intellect MVP — migrate toward this target under gated stories |

### 8.2 Trust boundaries

1. Vault ↔ Lake: only scrubbed text enters analytics/vectors (when narratives return upstream).
2. Lake ↔ Vector DBs: unidirectional Blue/Green hydrate of **catalogs only**.
3. Gateway ↔ Front ends: no raw DB credentials in clients.

---

## 9. Business processes

| Process | Trigger | Outcome |
|---|---|---|
| **Historical / slice backfill** | DAG 2–3 for `3m`…`all` | Lift → Raw → Refined → Mode 2 enrich → Curated |
| **Taxonomy / registry sync** | DAG 1 | Validate DB rules; export Parquet snapshots |
| **Signature enrichment** | New `signature_id` (anti-join) | Mode 2 classify + embed → registry upsert → Gold join |
| **Vector catalog release** | DAG 4 | Staging rebuild → 100-case Golden Query gate → blue/green cutover |
| **Daily / micro-batch ingest** | CFPB poll / webhook | Redis/registry hit (~99%) or Mode 2 miss → Gold + catalog upsert |
| **Taxonomy change** | Update Postgres/Mongo row (`HUMAN_VERIFIED` / version bump) | Metadata-only Gold refresh + vector metadata patch (no re-embed if text unchanged) |
| **Model / embedder change** | `classifier_version` / embedder tag | Re-embed affected signatures → new catalog partition → Blue/Green |
| **Drift response** | Cache-miss spike / uncategorized alerts | Human review → crosswalk or Tier 2 promotion |
| **Right-to-erasure** | Deletion request | Tombstone (immediate) + async Parquet/index purge |
| **Compliance investigation** | Risk Radar alert | Shared AST filter state → curated drill-down |
| **Agent assist** | Ticket open | Copilot fetches precedents via AST filters |
| **Consumer triage** | Plain-language input | Taxonomy map + SLA card; no foreign narratives |
| **B2B monetization** | API / marketplace subscribe | CU metering / data share entitlement |
| **FinOps reclaim** | 48h post-cutover | Blue index orphan reaper; cold tier demotion |

---

## 10. Technology stack

| Domain | Choices (charter baseline) |
|---|---|
| **Lake / tables** | Apache Iceberg over ZSTD Parquet (local / MinIO / S3 / ADLS / GCS) |
| **Lift Zone** | Local CSV zip tree (`$CCA_LIFT_ZONE` / complains_datasets) |
| **Local analytics** | DuckDB |
| **Batch / orch** | Docker Airflow + PySpark (Iceberg Spark stack `CICD/Local/iceberg/`) |
| **Taxonomy / signature registry** | **PostgreSQL (default)** or **MongoDB**; optional **Redis** hot cache — **no flat YAML/CSV runtime configs** |
| **Classification** | Mode 2: product crosswalk + DeBERTa-v3 zero-shot NLI overlay; optional LLM/human adjudication |
| **Embeddings** | BAAI/bge-base-en-v1.5 → 512-d Matryoshka + L2 + SQ8 |
| **Local vectors** | ChromaDB Docker (3 catalog collections) |
| **Cloud vectors** | AWS OpenSearch Serverless; Azure AI Search; GCP Vertex AI Vector Search |
| **Gateway** | FastAPI Query AST; Kong/Envoy/APIM edge |
| **Observability** | OpenTelemetry → Prometheus/Grafana or Datadog |
| **Metering** | Event bus + Lago/Orb/Stripe Billing |
| **Front end** | Next.js + TypeScript + Turborepo; Tailwind/Shadcn; ECharts/Tremor; embeddable web component copilot |
| **PII** | ZIP-3 masking; k-anonymity n ≥ 10; Presidio/NER when narratives exist; KMS vault |
| **Current repo anchors** | Angular Admin, FastAPI Middleware, Airflow, Intellect, Chroma MVP — bridge under §11 |

---

## 11. Projects we execute (portfolio)

Each **project** below becomes one or more GitHub Milestones + `[Story]` issues. No product coding without story-start.

### P0 — Charter & board alignment

- Publish / refresh this charter against empirical Mode 2 architecture (#317)
- Keep `PRODUCT_FEATURES.md` as “what exists today”; charter as “where we are going”
- Keep `DataArchitecture.md` as living data SoT (M40 done; M41 expands Refined/Curated/Taxonomy/Vectors)

### P1 — Medallion Lake & Taxonomy Foundation

- Lift Zone + Raw Iceberg (**done:** M40 #310/#311)
- Refined + Curated Iceberg specs & implementation stories
- Database Taxonomy Control Plane (12 Money Topics, crosswalk, org aliases, semantic_signatures)
- DuckDB analytics over Curated; 3m / all slice parity

### P2 — Enrichment & Compact Vector Catalogs

- Mode 2 classification container `v1.x`
- Semantic Signature Registry populate + Redis fast path
- Chroma collections hydrate; release_manifest; Blue/Green local

### P3 — Query AST Gateway & Golden Suite

- Neutral AST LCD operators; RBAC; k-anonymity; relaxation cascade
- Adapters: DuckDB + Chroma first; Golden Query Suite (100 cases)

### P4 — Multi-Cloud Fan-Out & Blue/Green CI/CD

- OpenSearch / Azure AI Search / Vertex adapters
- Hub-and-spoke Curated Parquet sync; Hot/Cold FinOps

### P5 — Observability, Drift & Security Hardening

- OTel golden signals; signature cache-miss / centroid drift; tombstones
- Edge three-lane gateway; CU metering skeleton

### P6 — Internal Experience MVP

- Systemic Risk Radar (minimal viable)
- Case Resolution Copilot embed (one CRM target)

### P7 — B2B Surface MVP

- Developer portal + metered intelligence API
- Optional first cloud data share

### P8 — Consumer Surface MVP

- Issue Navigator + SLA estimator (aggregates only)

### P9 — Existing CCAA continuity

- Preserve Admin / Middleware / Airflow / Intellect value
- Incremental stories to align MIOs, ingest, and index DAGs with Curated + Gateway (never big-bang rewrite without stories)

---

## 12. 90-day roadmap alignment

| Phase | Days | Focus | Primary projects |
|---|---|---|---|
| **1 Foundation** | 1–30 | Complete DataArchitecture docs (M41); implement Refined/Curated + registry; local 2M Curated parity | P0, P1, start P2 |
| **2 Abstraction** | 31–60 | Mode 2 + Chroma catalogs; Query AST + Golden Suite; Redis fast path | P2, P3, start P5 |
| **3 Multi-cloud & products** | 61–90 | Cloud vector adapters, Blue/Green, FinOps; Internal UI MVP | P4, P5, P6 |

Full design detail: brainstorming §§30 / §36; data contract: `docs/DataArchitecture.md`.

---

## 13. Success criteria & constraints

### Success (charter-level)

- [ ] Curated Iceberg is the only fact SoR; any vector catalog rebuildable from registry in minutes for 2M-class workloads
- [ ] ML runs on U_sig (≈3k–8k), not N (≈2M–19M)
- [ ] Same 512-d vectors searchable locally and across at least one cloud target with ≥95% Recall@10 vs flat baseline on Golden Suite
- [ ] Money Topics + cross-cutting Fraud/Transfer usable in AST without Product 1:1 fiction
- [ ] Internal MVP (Radar or Copilot) used by a real workflow owner
- [ ] Gate discipline unbroken for product code and gated architecture specs

### Constraints

- Regulatory data sensitivity → ZIP-3 / k-anonymity; consumer UIs never show others’ narratives
- Cost → single-hub inference on signatures; SQ8; hot/cold; no per-cloud re-embed; no 19M-row vector index
- Team capacity → sequence Crawl→Walk→Run; prefer 6–8 FTE model when staffing up
- Existing MVP → evolve via stories; do not abandon working Admin/Airflow paths abruptly

---

## 14. Governance & decision rights

| Decision class | Authority |
|---|---|
| Scope cut / delay of a product (P6–P8) | Co–Chief Architect (Product) |
| ADR change to lake, AST, embedding, or cloud parity | Co–Chief Architects (human sign-off required) |
| Story acceptance / merge to main | Per Superpowers + PR review; human owns prod |
| Taxonomy label promotions / `NEEDS_REVIEW` → `VERIFIED` | Domain SME + Architect acknowledgment |
| Spend (GPU batch, multi-cloud HA) | Co–Chief Architect (Product) |

**Board rule (hard):** Middleware / Portals / DAGs / migrations / `docs/DataArchitecture.md` require open `[Story]` + Milestone + `/ccaa-story-start`. Board docs under `docs/Project_Management/` and `docs/PRODUCT_FEATURES.md` follow the hard gate allow-list.

---

## 15. Out of scope (initial charter)

- Replacing CFPB as the sole initial public corpus (future multi-source is allowed later)
- Real-time sub-second streaming for all historical rows (micro-batch + signature cache is the design)
- Per-vendor proprietary embedding spaces as primary (Titan/Gecko/Ada as SoT)
- Postgres or MongoDB as the **primary data lake** (they are the **taxonomy/registry control plane only**)
- Flat YAML/CSV files as the runtime taxonomy source of truth
- Indexing all complaint rows into the vector store
- Shipping consumer or B2B products before Internal Stage 1 validation

---

## 16. Document control

| Field | Value |
|---|---|
| Title | Project Charter — CCAA Enterprise Intelligence Platform |
| Co–Chief Architects | Product principal; Delivery AI agent (roles, not named individuals) |
| Data architecture SoT | `docs/DataArchitecture.md` |
| Design notes | `docs/Complaints_Data_Classification_Indexing_Brainstorming.md` |
| Current product inventory | `docs/PRODUCT_FEATURES.md` |
| Empirical mode | Mode 2 (U_sig 2,924 / 8,438; cross-cutting &lt; 1%) |
| Related milestones | M40 (Lift/Raw done); M41 (DataArchitecture expansion); M42 (this charter refresh) |
| Delivered under | M42-0001 #317 |

**Charter acceptance:** Pending confirmation by Co–Chief Architect (Product) (edit Status to **Accepted** when ready).
