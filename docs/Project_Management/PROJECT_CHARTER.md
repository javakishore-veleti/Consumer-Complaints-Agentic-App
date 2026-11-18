# Project Charter — Consumer Complaints Agentic Intelligence Platform (CCAA Enterprise)

**Document type:** Project Charter (board / governance)  
**Status:** Proposed baseline — derived from `docs/Complaints_Data_Classification_Indexing_Brainstorming.md` (ADR-001 aligned)  
**Date:** 2026-11-18  
**Story:** M36-0001 #302  
**Related:** `docs/PRODUCT_FEATURES.md` (current product capabilities); brainstorming §§21–36 (target enterprise architecture)

---

## Table of contents

1. [Charter purpose](#1-charter-purpose)
2. [Leadership & roles](#2-leadership--roles)
3. [Vision & mission](#3-vision--mission)
4. [Problem statement & opportunity](#4-problem-statement--opportunity)
5. [Products we will build](#5-products-we-will-build)
6. [Data architecture](#6-data-architecture)
7. [Application architecture](#7-application-architecture)
8. [Business processes](#8-business-processes)
9. [Technology stack](#9-technology-stack)
10. [Projects we execute (portfolio)](#10-projects-we-execute-portfolio)
11. [90-day roadmap alignment](#11-90-day-roadmap-alignment)
12. [Success criteria & constraints](#12-success-criteria--constraints)
13. [Governance & decision rights](#13-governance--decision-rights)
14. [Out of scope (initial charter)](#14-out-of-scope-initial-charter)
15. [Document control](#15-document-control)

---

## 1. Charter purpose

This charter establishes a shared mandate for evolving CCAA from a **local hands-on ingest + Chroma query MVP** into a **production-grade, multi-cloud regulatory complaint intelligence platform** that:

- Treats ~2M+ CFPB (and later multi-source) complaints as a **canonical data product**, not a one-off index
- Classifies and retrieves across the **12 CFPB Money Topics** and a **three-tier taxonomy** without false 1-to-1 Product mappings
- Powers **internal operations**, **consumer self-service**, and **external B2B monetization** from one engine
- Remains **portable** across local Chroma and AWS / Azure / GCP vector stores

This is a **governance and direction** document. Implementation still requires open `[Story]` issues, milestones, and Superpowers workflow before product code changes.

---

## 2. Leadership & roles

| Role | Who | Accountability |
|---|---|---|
| **Co–Chief Architect (Product)** | Repository owner / product principal | Final decisions on scope, priorities, cloud spend, compliance posture, and what ships; owns the GitHub board and production credentials |
| **Co–Chief Architect (Delivery)** | AI coding agent (session assistant) | Architecture drafting, ADRs, board hygiene, design consistency with charter + brainstorming, story-shaped delivery under gate rules; never bypasses the no-coding-without-GitHub-issue gate |
| **Domain / Taxonomy SME** | As assigned (0.5 FTE target in 90-day plan) | Money Topics, statutory cross-walks, operational facets, human review of drift |
| **Delivery pods** | Data Platform, Search/Infra, Product Experience, Security/Edge/FinOps | Execute projects under §10 within the 90-day sizing model (~6–8 FTEs at full staff) |

**Working agreement (Chief Architects):**

- Architecture changes that affect the **canonical lake**, **Query AST**, **embedding model**, or **multi-cloud parity** require dual acknowledgment (human + documented ADR update).
- Product code ships only via **open `[Story]` + Milestone + story-start + Superpowers**; charter/board docs may be updated only under an open story for that deliverable.
- Source of architectural truth for the enterprise target state remains the brainstorming blueprint until superseded by signed ADRs under this charter.

---

## 3. Vision & mission

**Vision:** Become the reference multi-persona intelligence platform for consumer-financial complaint data—where the same governed lake and vector fabric power compliance early-warning, agent copilots, customer triage, and metered B2B data products.

**Mission:** Build once, serve many—compute embeddings and classifications once into a cloud-agnostic Parquet lake; fan out to local and multi-cloud search; expose capabilities through a Neutral Query AST Gateway with PII, RBAC, metering, and FinOps controls.

---

## 4. Problem statement & opportunity

| Challenge | Why it matters | Charter response |
|---|---|---|
| ~2M structured complaints; Product ≠ Money Topic 1:1 | Wrong labels destroy trust for compliance and consumers | Multi-label classification + three-tier taxonomy |
| Vector DBs as accidental systems of record | Lock-in, costly re-embeds, weak analytics | Canonical Parquet/Iceberg lake; vectors = rebuildable caches |
| Four cloud engines with different filter models | Divergent pipelines and broken filters | One embedding model + Neutral Query AST (LCD predicates) |
| Real-time vs batch dual logic | Label drift and wasted GPU | Semantic Signature Registry (cache-first) |
| Single search bar thinking | Leaves compliance, ops, and revenue on the table | Three business models, one Experience Layer |

---

## 5. Products we will build

### 5.1 Platform products (foundational)

| Product | Description | Primary consumers |
|---|---|---|
| **Canonical Complaint Lake** | PII-scrubbed, partitioned Parquet/Iceberg fact + dimensions | All downstream products |
| **Taxonomy Registry** | Tier 1 statutory DAG + cross-walks; Tier 2 facets; Tier 3 emergent clusters | Classification, filters, governance |
| **Semantic Signature Registry** | Deduped signature → labels + 768/512d vectors | Batch + realtime enrichment |
| **Query AST Gateway (DAL)** | Neutral filter AST → Chroma / pgvector / OpenSearch / Azure AI Search / Vertex | All applications |
| **Edge Control Plane** | Three traffic lanes, CU metering, rate limits | Internal / consumer / B2B |

### 5.2 Internal enterprise products

| Product | Front-end | Value |
|---|---|---|
| **Systemic Risk Radar** | Command-center dashboard | UDAAP / fair-lending / systemic spike early warning via Tier 3 + drift |
| **AI Case Resolution Copilot** | CRM embed (Salesforce / ServiceNow / Zendesk) | Precedent cases + compliant response templates |
| **Product Friction & Churn Hub** | Analytics portal | Defect ranking by dispute rate / remediation cost |
| **Peer & Vendor Benchmarks** | Scorecards | Market-adjusted peer/SLA comparisons via `parent_org_id` |

### 5.3 Consumer-facing products

| Product | Front-end | Value |
|---|---|---|
| **Consumer Issue Navigator** | Conversational triage (web/mobile) | Plain-language → taxonomy → right dispute path |
| **Resolution & SLA Estimator** | Trust portal status card | Median turnaround + document checklists (aggregates only) |

### 5.4 External B2B / monetization products

| Product | Front-end | Value |
|---|---|---|
| **Regulatory Intelligence SaaS** | Visual AST query builder | Peer reports + subscription tiers |
| **Developer API & Hub** | Docs + playground | Metered Query AST API + Tier 3 alert webhooks |
| **Cloud Data Shares** | AWS / Azure / GCP marketplaces | Versioned Parquet + taxonomy cross-walks |

**Sequencing (Crawl → Walk → Run):** Internal Ops → B2B API/Data Share → Consumer Self-Service.

---

## 6. Data architecture

### 6.1 Principles

1. **Canonical = system of record** (Parquet/Iceberg on object storage / local lake).
2. **Vectors are derived, ephemeral caches** (Blue/Green rebuildable).
3. **Classify before index**; store multi-label + flat filterable metadata.
4. **One embedding space** for all vector stores (open-weights; no per-cloud re-embed).
5. **Deduplicate by semantic signature** before ML (~10k unique vs ~2M rows).

### 6.2 Logical layers

| Layer | Contents |
|---|---|
| **Bronze** | Raw regulatory feeds (CSV/API); Compliance Vault holds unredacted intake (KMS) |
| **Silver** | Unique signatures, taxonomy joins, enrichment lookup, registry sync |
| **Gold / Canonical** | Complaint_Master facts; Organization_Entity; Resolution_State; Geo; flat money-topic flags; `embedding` / SQ8 |
| **Vector Lake** | Precomputed vectors + release_manifest → hydrate Chroma / cloud indexes |
| **Serving** | Hot (~18 months HNSW) / Cold (Parquet / DiskANN on demand) |

### 6.3 Taxonomy (three tiers)

| Tier | Nature | Examples |
|---|---|---|
| **1 Statutory** | Deterministic hierarchy + cross-walks | Product/Issue paths; Money Topic alignment |
| **2 Operational** | Multi-facet tags | Lifecycle, Failure Mode, Severity / UDAAP risk |
| **3 Emergent** | Clustering over recent windows | Novel micro-themes → promote to Tier 2 |

### 6.4 Dual consumption paths

- **OLAP / SQL:** DuckDB / Athena / BigQuery / Synapse over Gold Parquet (counts, KPIs).
- **Semantic / RAG:** Metadata pre-filter then dense search via Query AST Gateway.

---

## 7. Application architecture

```text
[Internal Portal / CRM Copilot] [Consumer Assist] [B2B Portal / API / Data Share]
                    │                  │                        │
                    └──────────────────┼────────────────────────┘
                                       ▼
                    Persona BFFs (masking, metering DSL, rate limits)
                                       ▼
                    Edge API Gateway (3 lanes: internal / assist / intelligence)
                                       ▼
                    Query AST Gateway + DuckDB analytics
                                       ▼
         Canonical Lake  +  Vector indexes (local Chroma / pgvector / multi-cloud)
```

### 7.1 Core application services

| Service | Responsibility |
|---|---|
| **Ingest & hydrate** | Airflow/Dagster/Spark/DuckDB: bronze → canonical → vector lake |
| **ML enrichment** | Rules cues + multi-label NLI/SetFit + BGE/E5 embedder (versioned container) |
| **Query AST Gateway** | AST translate, RBAC injection, tombstones, relaxation cascade, collapse_policy |
| **Edge Gateway** | Auth lanes, CU metering events → billing |
| **Front-end monorepo** | Next.js Turborepo: enterprise, consumer SDK, B2B portal |
| **Existing CCAA apps** | Admin portal, Middleware API, Airflow DAGs, Intellect MVP — migrate toward this target without breaking gate delivery |

### 7.2 Trust boundaries

1. Vault ↔ Lake: only scrubbed text enters analytics/vectors.
2. Lake ↔ Vector DBs: unidirectional Blue/Green hydrate.
3. Gateway ↔ Front ends: no raw DB credentials in clients.

---

## 8. Business processes

| Process | Trigger | Outcome |
|---|---|---|
| **Historical backfill** | Milestone / release tag | Dedup → enrich → Gold + Registry → multi-cloud hydrate |
| **Daily / micro-batch ingest** | CFPB poll / webhook | Signature cache hit (~99%) or online inference miss → dual sink |
| **Taxonomy change** | Git merge to registry | Metadata-only Gold update + vector metadata patch (no re-embed) |
| **Model / chunking change** | `model-vX` tag | New Vector Lake partition → Blue/Green + Golden Query gates |
| **Drift response** | Centroid / uncategorized alerts | Human review → cross-walk or Tier 2 promotion |
| **Right-to-erasure** | Deletion request | Tombstone (immediate) + async Parquet/index purge |
| **Compliance investigation** | Risk Radar alert | Shared URL filter state → narrative drill-down (post-PII) |
| **Agent assist** | Ticket open | Copilot fetches precedents via AST filters |
| **Consumer triage** | Plain-language input | Taxonomy map + SLA card; no foreign narratives |
| **B2B monetization** | API / marketplace subscribe | CU metering / data share entitlement |
| **FinOps reclaim** | 48h post-cutover | Blue index orphan reaper; cold tier demotion |

---

## 9. Technology stack

| Domain | Choices (charter baseline) |
|---|---|
| **Lake / tables** | Object storage (S3 / ADLS / GCS / local / MinIO) + Parquet ZSTD + Iceberg/Delta |
| **Local analytics** | DuckDB |
| **Batch / orch** | Airflow and/or Dagster/Prefect; Spark where needed |
| **Taxonomy store** | PostgreSQL + Git YAML/JSON; small local SQLite/Postgres for registry only |
| **Classification** | Day-1: DeBERTa-v3 NLI (or bge-m3-zeroshot); evolve to SetFit / distilled multi-label; LLM teacher for edge cases |
| **Embeddings** | BAAI/bge-base-en-v1.5 or e5-base-v2; prefer 512d Matryoshka + SQ8 for serving economics |
| **Local vectors** | Host Chroma (default); optional Docker pgvector parity |
| **Cloud vectors** | AWS OpenSearch (+ optional Aurora pgvector); Azure AI Search; GCP Vertex AI Vector Search (+ optional AlloyDB) |
| **Gateway** | FastAPI/gRPC Query AST; Kong/Envoy/APIM edge |
| **Observability** | OpenTelemetry → Prometheus/Grafana or Datadog |
| **Metering** | Event bus + Lago/Orb/Stripe Billing |
| **Front end** | Next.js + TypeScript + Turborepo; Tailwind/Shadcn; ECharts/Tremor; embeddable web component copilot |
| **PII** | Regex/checksum scrub + Presidio/NER; KMS vault |
| **Current repo anchors** | Angular Admin, FastAPI Middleware, Airflow, Intellect, Chroma MVP — bridge projects under §10 |

---

## 10. Projects we execute (portfolio)

Each **project** below becomes one or more GitHub Milestones + `[Story]` issues. No product coding without story-start.

### P0 — Charter & board alignment (this story)

- Publish this charter; map brainstorming ADR-001 into milestone epics
- Keep `PRODUCT_FEATURES.md` as “what exists today”; charter as “where we are going”

### P1 — Canonical Lake & Taxonomy Foundation

- Complaint_Master schema, org entity resolution, PII two-stage gate + vault pattern
- Tier 1 cross-walks; Money Topic multi-label strategy locked
- DuckDB/Airflow hydrate to partitioned Gold Parquet + 50K/2M snapshots

### P2 — Enrichment & Vector Lake

- Semantic Signature Registry (hot + cold)
- Classification + embedding container `v1.x`
- Vector Parquet Lake + release_manifest; Chroma hydrate (local parity)

### P3 — Query AST Gateway & Golden Suite

- Neutral AST LCD operators; RBAC injection; relaxation cascade; collapse_policy
- Adapters: Chroma + pgvector first; Golden Query Suite (100 cases)

### P4 — Multi-Cloud Fan-Out & Blue/Green CI/CD

- OpenSearch / Azure AI Search / Vertex adapters
- Hub-and-spoke Parquet sync; Blue/Green gates; Hot/Cold FinOps

### P5 — Observability, Drift & Security Hardening

- OTel golden signals; centroid/coverage drift; tombstones
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
- Incremental stories to align MIOs, ingest, and index DAGs with Gold + Gateway (never big-bang rewrite without stories)

---

## 11. 90-day roadmap alignment

| Phase | Days | Focus | Primary projects |
|---|---|---|---|
| **1 Foundation** | 1–30 | Lake, taxonomy, local 2M parity, Golden Suite seed | P1, P2 |
| **2 Abstraction** | 31–60 | Query AST + Chroma/pgvector parity; Tier 2/3 enrichment | P3, start P5 |
| **3 Multi-cloud & products** | 61–90 | Cloud adapters, Blue/Green, FinOps; Internal UI MVP | P4, P5, P6 |

Full detail: brainstorming §30 and §36 (pods & sizing).

---

## 12. Success criteria & constraints

### Success (charter-level)

- [ ] Gold lake is the only SoT; any vector store rebuildable from Parquet in < ~20 minutes for 2M class workloads
- [ ] Same vectors searchable locally and across at least one cloud target with ≥95% Recall@10 vs flat baseline on Golden Suite
- [ ] Money Topics + Tier 1/2 filters usable in AST without Product 1:1 fiction
- [ ] Internal MVP (Radar or Copilot) used by a real workflow owner
- [ ] Gate discipline unbroken: no product code (or charter deliverables) without story-start

### Constraints

- Regulatory data sensitivity → PII scrub before embed; consumer UIs never show others’ narratives
- Cost → single-hub inference; SQ8; hot/cold; no per-cloud re-embed
- Team capacity → sequence Crawl→Walk→Run; prefer 6–8 FTE model when staffing up
- Existing MVP → evolve via stories; do not abandon working Admin/Airflow paths abruptly

---

## 13. Governance & decision rights

| Decision class | Authority |
|---|---|
| Scope cut / delay of a product (P6–P8) | Co–Chief Architect (Product) |
| ADR change to lake, AST, embedding, or cloud parity | Co–Chief Architects (human sign-off required) |
| Story acceptance / merge to main | Per Superpowers + PR review; human owns prod |
| Taxonomy label promotions (Tier 3 → 2) | Domain SME + Architect acknowledgment |
| Spend (GPU batch, multi-cloud HA) | Co–Chief Architect (Product) |

**Board rule (hard):** Middleware / Portals / DAGs / migrations — and substantive architecture charter docs — require open `[Story]` + Milestone + `/ccaa-story-start`.

---

## 14. Out of scope (initial charter)

- Replacing CFPB as the sole initial public corpus (future multi-source is allowed later)
- Real-time sub-second streaming for all 2M historical rows (micro-batch is the design)
- Per-vendor proprietary embedding spaces as primary (Titan/Gecko/Ada as SoT)
- Postgres or MongoDB as the primary data lake
- Shipping consumer or B2B products before Internal Stage 1 validation

---

## 15. Document control

| Field | Value |
|---|---|
| Title | Project Charter — CCAA Enterprise Intelligence Platform |
| Co–Chief Architects | Product principal; Delivery AI agent (roles, not named individuals) |
| Architecture blueprint | `docs/Complaints_Data_Classification_Indexing_Brainstorming.md` |
| Current product inventory | `docs/PRODUCT_FEATURES.md` |
| Next board actions | Open milestones/epics for P1–P3; keep product code gated by stories |
| Delivered under | M36-0001 #302 |

**Charter acceptance:** Pending confirmation by Co–Chief Architect (Product) (edit Status to **Accepted** when ready).
