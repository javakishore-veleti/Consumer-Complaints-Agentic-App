# Data Architecture — CCAA Enterprise

**Document type:** Data architecture specification  
**Status:** Living draft — Lift + Raw (Bronze) + Refined (Silver) + Curated (Gold) specified; Taxonomy / Vectors / Mode 2 orchestration follow in M41-0002 / M41-0003  
**Stories:** M40-0001 #310 (Lift + Raw); M41-0001 #314 (Refined + Curated)  
**Related:** `docs/Project_Management/PROJECT_CHARTER.md`; `docs/Complaints_Data_Classification_Indexing_Brainstorming.md`; Iceberg Docker runtime #311 (`CICD/Local/iceberg/`)

**Empirical calibration (Lift Zone profiling):**

| Slice | Rows (N) | U_prod `(Product, Sub-product)` | U_sig `(Product, Sub-product, Issue, Sub-issue, Tags)` | % Cross-Cutting |
|---|---:|---:|---:|---:|
| 3-month | 1,970,702 | 55 | 2,924 | 0.345% |
| Full archive | 19,170,856 | 127 | 8,438 | 0.764% |

**Mode snap:** **Mode 2 — Semantic Signature Registry + Hybrid Rules / NLI** (full cascade documented in M41-0003 #316).

---

## Table of contents

1. [Purpose & scope](#1-purpose--scope)
2. [Medallion overview (Bronze → Silver → Gold)](#2-medallion-overview-bronze--silver--gold)
3. [Lift Zone (local CSV zip landing)](#3-lift-zone-local-csv-zip-landing)
4. [Apache Iceberg Raw Data Zone (Bronze)](#4-apache-iceberg-raw-data-zone-bronze)
5. [Refined Data Zone (Silver)](#5-refined-data-zone-silver)
6. [Curated Data Zone (Gold)](#6-curated-data-zone-gold)
7. [Database Taxonomy Control Plane](#7-database-taxonomy-control-plane)
8. [Mode 2, Vector Store, orchestration & Query AST](#8-mode-2-vector-store-orchestration--query-ast)
9. [Document control](#9-document-control)

---

## 1. Purpose & scope

This document defines the **canonical data architecture** for ingesting ~2M+ CFPB consumer complaint records into a portable lakehouse that supports local development and multi-cloud promotion (S3 / ADLS / GCS).

**Scope of this revision (M41-0001 #314):** expand the living spec with **Refined (Silver)** and **Curated (Gold)** Iceberg zone models — 24-column and 31-column contracts, ZIP-3 hygiene, deterministic `signature_id`, Money Topics + parent-org enrichment, and size targets — while **preserving** the existing Lift Zone and Raw/Bronze sections.

Database-first Taxonomy Control Plane, Mode 2 classification cascade, Vector DB Store, Airflow DAG plane, and Query AST Gateway land in sibling M41 stories (#315 / #316).

---

## 2. Medallion overview (Bronze → Silver → Gold)

| Zone | Namespace / tables | Responsibility | Primary tech |
|---|---|---|---|
| **Lift Zone** | Filesystem zips | Durable local copies of CFPB CSV zip inputs produced by existing download/filter workflow endpoints | Local filesystem folder (workflow-managed) |
| **Raw / Bronze** | `raw.cfpb_complaints_<slice>` + quarantine | Immutable Iceberg tables; all-string business columns + audit lineage; no business transforms | Apache Iceberg + ZSTD Parquet + PySpark |
| **Refined / Silver** | `refined.cfpb_complaints_<slice>` | Typed **24-column** facts; ZIP-3 hygiene; deterministic `signature_id` | Iceberg + PySpark |
| **Curated / Gold** | `curated.cfpb_complaints_<slice>` | Typed **31-column** business SoR: Money Topics + parent org (~220 MB / ~2 GB) | Iceberg + broadcast registry join |
| **Vector serving (later)** | Compact catalogs | Semantic routing indexes (not the fact SoR) | Chroma / multi-cloud (M41-0003) |

Data flows **unidirectionally**: **Lift → Raw → Refined → Curated** → Vector serving caches / DuckDB analytics.

All five slices (`3m`, `6m`, `9m`, `12m`, `all`) share identical table templates per zone, **ZSTD Level 3**, `write.distribution-mode=hash`, and Iceberg hidden partitioning on **`months(date_received)`**.

---

## 3. Lift Zone (local CSV zip landing)

The **Lift Zone** is the operational staging area **outside** the Iceberg warehouse where Airflow (or equivalent) workflow endpoints already store downloaded / filtered CFPB **CSV zip** inputs.

### 3.1 Architectural role

- **Source of truth for files, not tables:** Lift Zone holds opaque zip artifacts (e.g., 3-month filter zip, “all complaints” zip). It is **not** queryable Iceberg storage.
- **No re-download required for Raw backfills:** Raw Zone ingestion reads from Lift Zone paths for the active dataset slice (`3m`, `6m`, `9m`, `12m`, `all`).
- **Ephemeral unzip staging is separate:** Airflow unpacks into `/tmp/airflow_stage/<run_id>/` for a single run; the Lift Zone zip remains durable for replay.

### 3.2 Local path (CCAA today)

| Role | Path |
|---|---|
| **Host Lift Zone root** | `$HOME/runtime_data/apps/datasets/CCA/complains_datasets/` (Airflow binds this tree; imports live under it) |
| **In Spark Iceberg container** | `/lift` (read-only bind from `CICD/Local/iceberg/docker-compose.yaml`) |
| **Override** | Env `CCA_LIFT_ZONE` when starting the Iceberg compose stack |

### 3.3 Relationship to Raw Zone

```text
[CFPB source / download workflows]
            │
            ▼
[Lift Zone: local folder of CSV .zip files by dataset slice]
            │
            ▼  Airflow Sensor → Unzip → Pre-ingestion gate
[Ephemeral staging CSV]
            │
            ▼  PySpark Bronze hydration (cca-spark-iceberg)
[Apache Iceberg Raw Data Zone: raw.cfpb_complaints_* ]
```

### 3.4 Infra runtime (M40-0002 #311)

Spark + Iceberg Docker stack lives at `CICD/Local/iceberg/` (quickstart-aligned). Operator guide: `CICD/Local/iceberg/README.md`. Start with `docker compose up -d` from that directory (or `CICD/Local/docker-all-up.sh iceberg`).

---

## 4. Apache Iceberg Raw Data Zone (Bronze)

From a solution architecture perspective, the **Raw Data Zone (Bronze Layer)** is your immutable, zero-loss landing foundation. Its primary responsibility is to capture incoming CFPB zipped CSV drops into local Apache Iceberg tables cleanly, atomically, and with full operational lineage—without applying business transformations that could break ingestion or obscure source data.

In keeping with the architectural focus, this specification covers the logical design, storage topology, ingestion mechanics, data quality gates, and Day-2 lifecycle management **without code implementations**.

### 4.1 Architectural Principles of the Raw Data Zone

- **Immutability & Replayability:** Once written, raw business values are never altered in place. If a downstream Silver or Gold rule has a bug, you replay from the Raw Data Zone without re-downloading source files.
- **Schema-on-Write Lenience (All-String Business Columns):** Except for the primary partition date (`date_received`), every source field is stored as a `STRING`. If an upstream CFPB export introduces a new category label, unexpected null, or non-standard ZIP code, the Raw ingestion job still succeeds rather than failing the pipeline.
- **Dataset Isolation via Shared Template:** Your five dataset windows (`3m`, `6m`, `9m`, `12m`, `all`) live in five separate Iceberg tables instantiated from a single canonical DDL template. This isolates blast radius while keeping queries, tooling, and Airflow tasks 100% uniform.
- **Local-to-Cloud Storage Parity:** Using Apache Iceberg over ZSTD-compressed Parquet files on local storage (or MinIO) mirrors AWS S3, Azure ADLS Gen2, and GCP GCS identically.

### 4.2 Physical Storage & Catalog Topology

#### Catalog & Namespace Layout

- **Iceberg Catalog:** Local Hadoop/Filesystem catalog (or JDBC/REST catalog in Docker) rooted at `./warehouse/raw/`.
- **Namespace:** `raw`
- **Table Inventory (Identical DDL & Partition Spec):**
  - `raw.cfpb_complaints_3m`
  - `raw.cfpb_complaints_6m`
  - `raw.cfpb_complaints_9m`
  - `raw.cfpb_complaints_12m`
  - `raw.cfpb_complaints_all`

#### Physical Directory Structure

```text
./warehouse/raw/
├── cfpb_complaints_3m/
│   ├── metadata/          # Iceberg manifest lists, snap-files, & versioned table metadata JSON
│   └── data/
│       └── date_received_month=2026-08/
│           └── part-00000-<uuid>.zstd.parquet
├── cfpb_complaints_6m/
├── cfpb_complaints_9m/
├── cfpb_complaints_12m/
└── cfpb_complaints_all/
```

### 4.3 Canonical Raw Table Data Model (16 Source + 5 Audit Columns)

Every table in the `raw` namespace enforces this exact **21-column** schema:

The raw data model enforces a strict 21-column Iceberg schema across all tables, combining **16 source fields** (stored as `STRING` or `DATE` to preserve formatting and prevent ingestion failures) with **5 pipeline-injected system audit columns** (`_dataset_slice`, `_source_zip_file`, `_ingest_ts`, `_airflow_run_id`, and a deterministic SHA-256 `_row_hash`) for full traceability.

| Kind | Columns (conceptual) |
|---|---|
| **Source (16)** | CFPB complaint fields as exported (including `date_received` as DATE for partitioning; remaining business fields as STRING) |
| **Audit (5)** | `_dataset_slice`, `_source_zip_file`, `_ingest_ts`, `_airflow_run_id`, `_row_hash` |

Follow-on stories may publish the exhaustive 16-name field list aligned to the live CFPB export header; the architectural contract above is authoritative for Raw Zone design.

### 4.4 Partitioning & Physical Storage Optimization

- **Hidden Partitioning:** Uses `months(date_received)` to automatically derive monthly partitions (yielding roughly ~13,000 rows or ~2.3 MB per partition on the full dataset) to balance query performance and small-file avoidance.
- **Write Distribution & Compression:** Configured with hash distribution mode to ensure one consolidated Parquet file per month per batch run, and compressed using **ZSTD Level 3** to keep the entire ~1.97M-row raw dataset compact at roughly **~350 MB**.

### 4.5 End-to-End Airflow + PySpark Ingestion Architecture

Because PySpark cannot natively split `.zip` archives across parallel worker threads, orchestration follows a deterministic **four-stage** pipeline:

1. **Airflow Sensor & Unzip Task:** Unpacks the source archive from the **Lift Zone** into an ephemeral local staging directory (`/tmp/airflow_stage/<run_id>/`).
2. **Pre-Ingestion Gate:** Validates header counts (16 columns), non-zero byte size, and required keys.
3. **PySpark Bronze Hydration:** Reads the CSV with multi-line and quote-escaping resilience, normalizes headers, parses `date_received`, and appends the 5 system audit columns and row hash.
4. **Atomic Iceberg Commit & Cleanup:** Performs an atomic partition overwrite into the target Iceberg table within a single ACID transaction, routes any bad records or null primary identifiers to a `raw.cfpb_complaints_quarantine` sidecar table, and purges staging files.

### 4.6 Data Quality Gates & Day-2 Operations

- **Data Quality Gates:** Airflow executes source-to-target count reconciliation against Iceberg snapshot summaries and runs schema/null checks to ensure **0.0% null rates** on mandatory keys (`complaint_id`, `date_received`, `product`, `company`).
- **Metadata Hygiene:** Table properties enforce retention limits (retaining the last 3 snapshots) alongside scheduled weekly maintenance tasks (`expire_snapshots` and `remove_orphan_files`) to prevent local storage bloat.

### 4.7 Runtime: Iceberg Spark Docker (#311)

Raw Zone compute runs against the containerized Spark + Iceberg stack under `CICD/Local/iceberg/` (see [Spark quickstart — reading a table](https://iceberg.apache.org/spark-quickstart/#reading-data-from-a-table)).

- **Compose:** `CICD/Local/iceberg/docker-compose.yaml` (`tabulario/spark-iceberg` + REST + object store)
- **Operator docs / Airflow connection contract:** `CICD/Local/iceberg/README.md`
- **Lift Zone mount:** host complains_datasets → `/lift` (read-only)
- **DAG note:** #311 does **not** change Airflow DAGs; future Raw ingest stories must follow the documented contract and story-start before DAG edits

---

## 5. Refined Data Zone (Silver)

### 5.1 Purpose

Type-safe analytical foundation and **deterministic `signature_id`** generation. Silver is where taxonomy discovery inputs (`DISTINCT product/sub_product`, distinct companies) are produced for the Database Taxonomy Control Plane (M41-0002). Money Topics are **not** attached here.

### 5.2 Tables

`refined.cfpb_complaints_<slice>` — same five slices as Raw (`3m` … `all`). Partition: `months(date_received)`.

### 5.3 Data model — 24 columns

| Group | Columns |
|---|---|
| **Keys & lineage** | `complaint_id` (PK), `signature_id` (SHA-256 of normalized `product\|sub_product\|issue\|sub_issue\|tags` — lower/trim/coalesce empty), `_source_row_hash`, `_refined_ts` |
| **Temporal / SLA** | `date_received` (DATE), `date_sent_to_company` (DATE when parseable), `date_received_int` (YYYYMMDD), `year_month` (YYYYMM), `forwarding_lag_days` (INT) |
| **Standardized categoricals** | `product`, `sub_product`, `issue`, `sub_issue`, `submitted_via`, `company_raw_clean`, `company_response`, `company_public_response` (nulls → `UNKNOWN` / `NONE_PROVIDED`) |
| **Booleans** | `is_timely_response`, `is_monetary_relief`, `is_older_american`, `is_servicemember` |
| **Geo hygiene (ZIP-3)** | `state` (2-letter), `zip_code_clean`, `zip_precision` (`5_DIGIT` \| `3_DIGIT_MASKED` \| `UNAVAILABLE`); `zip3` = first 3 digit chars of `zip_code` else `UNK` |

Count check: **24 columns** across the five groups above.

### 5.4 Transforms (logical)

- Read Raw → parse dates; uppercase / normalize enums; derive Tags booleans (`Older American`, `Servicemember`).
- **ZIP-3 hygiene:** mask sparse geographies (&lt; 20,000 residents policy) to 3-digit precision; never store full ZIP when policy requires masking.
- Compute `signature_id`; retain lineage to Raw via `_source_row_hash` / audit fields as needed.
- **Do not** attach Money Topics or parent-org resolution on Silver (that is Gold + registry).

### 5.5 Quality gates

- `COUNT(*)` Refined = `COUNT(*)` Raw for the slice (quarantine excluded).
- `signature_id` non-null on every refined row.
- Operator demo: `COUNT(DISTINCT signature_id)` ≈ U_sig for the slice (2,924 on 3m; 8,438 on full).

---

## 6. Curated Data Zone (Gold)

### 6.1 Purpose

Business-ready **System of Record**: Refined facts + multi-label Money Topics + parent organization resolution. **No heavy vector arrays in the fact table** — vectors live in the registry + Vector DB Store (M41-0003).

### 6.2 Tables

`curated.cfpb_complaints_<slice>` — same five slices; partition `months(date_received)`.

### 6.3 Data model — 31 columns

All **24 Refined columns** plus **7 enrichment columns**:

| Group | Columns |
|---|---|
| **Money Topics (multi-label)** | `primary_money_topic`, `secondary_money_topics` (pipe-delimited, e.g. `\|Fraud & Scams\|`), `is_fraud_scam`, `is_money_transfer`, `classification_source` |
| **Entity resolution** | `parent_org_id` (SHA-256 of normalized company / alias override), `canonical_org_name`, `org_peer_tier` |
| **Governance lineage** | `tax_version`, `classifier_version` |

Count check: **24 + 7 = 31 columns**.

### 6.4 Physical footprint (target)

| Slice | Approx. size |
|---|---|
| 3-month (1,970,702 rows) | ~220 MB |
| Full archive (19,170,856 rows) | ~2.0 GB |

### 6.5 Materialization

PySpark broadcast-joins Refined facts to Parquet snapshots of `semantic_signatures` + `organization_aliases` (exported from Postgres/Mongo Taxonomy Control Plane — M41-0002). Cache hits dominate; only new signatures trigger Mode 2 inference upstream of the join (M41-0003).

DuckDB / SparkSQL / cloud SQL engines query Curated for exact counts and KPIs — never route aggregations through vector stores.

---

## 7. Database Taxonomy Control Plane

### 7.1 Principle — database-first, zero flat files at runtime

Runtime taxonomy is **not** YAML/CSV on disk. Registries live in **PostgreSQL** (preferred local + cloud SoR) or **MongoDB** collections with the same logical schemas. Spark joins use **Parquet snapshots** exported from the SoR (broadcast-join guardrail) — never live JDBC from every worker task for 2M-class fan-out.

| Choice | Recommendation |
|---|---|
| **Primary SoR** | PostgreSQL (`taxonomy` schema) — relational FKs, migrations, strong typing |
| **Alt SoR** | MongoDB — document collections mirroring the four registries |
| **Hot cache** | Redis — signature_id → Money Topics / alias lookup for real-time paths |
| **Spark join** | Nightly/on-demand Parquet snapshot under object store / Iceberg `demo.taxonomy.*` |

### 7.2 Four registries

| Registry | Cardinality (3m / all) | Role |
|---|---|---|
| `money_topics` | **12** / 12 | Canonical CFPB Money Topic labels |
| `product_crosswalk` | ~**55** / ~**127** | `(product, sub_product)` → primary Money Topic |
| `organization_aliases` | ~**6k** | Raw company string → `parent_org_id` / canonical name |
| `semantic_signatures` | **2,924** / **8,438** | One row per 5-field U_sig + Mode 2 labels |

#### `money_topics` (sample)

| Column | Example |
|---|---|
| `money_topic_id` | `MT-CREDIT-CARDS` |
| `name` | `Credit Cards` |
| `definition_ref` | Official CFPB Money Topic definition URI / text hash |

#### `product_crosswalk` (sample)

| Column | Example |
|---|---|
| `product` | `Credit card or prepaid card` |
| `sub_product` | `General-purpose credit card or charge card` |
| `primary_money_topic` | `Credit Cards` |

#### `organization_aliases` (sample from Complaint ID **25505474** lineage)

| Column | Example |
|---|---|
| `alias_raw` | `CAPITAL ONE` / `Capital One Bank` |
| `parent_org_id` | `6d55f403495e51ed7212000a597144abed8a3c310895cb601bea4403339300c6` |
| `canonical_org_name` | `Capital One` |

#### `semantic_signatures` (sample)

| Column | Example |
|---|---|
| `signature_id` | SHA-256 of normalized `product\|sub_product\|issue\|sub_issue\|tags` |
| `primary_money_topic` | `Credit Cards` |
| `secondary_money_topics` | `\|Fraud & Scams\|` (nullable) |
| `classification_source` | `mode2-rules-v1` / `mode2-nli-v1` |
| `tax_version` | `2026.11` |

### 7.3 Population lifecycle

| Phase | What happens | Writes |
|---|---|---|
| **Day-1 seed** | Load 12 Money Topics + known crosswalk/alias seeds | `money_topics`, seed rows of `product_crosswalk` / `organization_aliases` |
| **Silver discovery** | `DISTINCT` product/sub_product + company strings from Refined | Candidate rows → `product_crosswalk` / `organization_aliases` (`NEEDS_REVIEW` until SME) |
| **Mode 2 cache** | Classify each new U_sig; upsert registry | `semantic_signatures`; Redis hot keys |

No flat-file runtime config is prescribed for these registries.

---

## 8. Mode 2, Vector Store, orchestration & Query AST

### 8.1 Mode 2 hybrid classification (accepted)

| Stage | Behavior |
|---|---|
| **1 — Rules** | `product_crosswalk` → `primary_money_topic` |
| **2 — Overlay** | Keyword / NLI cues on issue/sub_issue/tags for cross-cutting **Fraud & Scams** and **Money Transfers** → flags + optional secondary topics |
| **3 — Adjudication (later)** | Low-confidence / cache-miss → LLM teacher queue (not required for local MVP) |

**Reject Mode 1** (product 1:1 as Money Topic) — destroys cross-cutting labels. **Reject Mode 3** (classify every complaint row) — cost explosion; ML runs on U_sig only (~3k–8k).

Working product path today: `classifier_version=mode2-rules-v1` (M47); NLI overlay optional upgrade.

### 8.2 Vector DB Store — three compact catalogs

Embeddings target **512-d BGE** with **SQ8** quantization (MVP/CI may use deterministic hash embeddings). Index: **HNSW + cosine**. RAM budget: catalogs only (U_sig / aliases / fingerprints) — **never** 19M complaint narratives.

| Collection | Contents | Local | AWS | Azure | GCP |
|---|---|---|---|---|---|
| `cfpb_semantic_signatures` | U_sig text + Money Topic metadata | **Chroma** (`CCA_CHROMA_URL`) | OpenSearch k-NN | Azure AI Search | Vertex Vector Search |
| `cfpb_organization_aliases` | Alias / parent-org strings | Chroma (follow-on) | OpenSearch | AI Search | Vertex |
| `cfpb_entity_fingerprints` | Institution × ZIP-3 fingerprints | Chroma (follow-on) | OpenSearch | AI Search | Vertex |

Local working product: Chroma `cfpb_semantic_signatures` from Iceberg taxonomy (M49). JSONL under `CCA_VECTOR_STORE_PATH` remains the Middleware Intellect fallback.

### 8.3 Airflow DAG plane + Redis fast path

| DAG | Purpose |
|---|---|
| **DAG 1** | Lift → Raw hydrate (slice) |
| **DAG 2** | Raw → Refined (+ signature_id / ZIP-3) |
| **DAG 3** | Taxonomy Mode 2 upsert `semantic_signatures` |
| **DAG 4** | Refined+registry → Curated; export → Chroma signatures |

**Real-time fast path:** Redis signature / alias hits for portal/API; cache miss enqueues Mode 2 micro-batch — does not block Query AST aggregations on Curated.

Admin-triggerable hydrate workflows (M51) map 1:1 to these stages for the 3m slice.

### 8.4 Neutral Query AST Gateway

FastAPI Middleware exposes `POST /intellect/query-ast`: validate Neutral AST → SparkSQL/DuckDB against `demo.curated.cfpb_complaints_<slice>`; optional execute; **k-anonymity n ≥ 10**. Intellect portal + Risk Radar drill-down consume this gateway (M52–M53). Vector search remains a separate ladder (`POST /intellect/query`).

### 8.5 Master topology (ASCII)

```text
Lift CSV zip
  → Raw Iceberg (Bronze)
  → Refined Iceberg (Silver) ──DISTINCT──► Taxonomy SoR (Postgres/Mongo)
  → Mode 2 ──upsert──► semantic_signatures ──Parquet snap──► Curated (Gold)
                                              └─embed──► Chroma / cloud vector catalogs
Curated ◄── Query AST Gateway (FastAPI) ◄── Intellect / Risk Radar / future B2B
Redis hot cache ──signature/alias──► Gateway + Mode 2 fast path
Airflow DAG 1..4 orchestrates hydrate; Admin starts workflows via Middleware
```

---

## 9. Document control

| Field | Value |
|---|---|
| Title | Data Architecture — CCAA Enterprise |
| Current focus | Full medallion + Taxonomy Control Plane + Mode 2 / Vectors / DAG / Query AST |
| Related charter | `docs/Project_Management/PROJECT_CHARTER.md` |
| Related brainstorming | `docs/Complaints_Data_Classification_Indexing_Brainstorming.md` |
| Follow-on infra | M40-0002 #311 — Iceberg Spark Docker for Raw Zone |
| Delivered under | M40-0001 #310 (Lift + Raw); M41-0001 #314 (Refined + Curated); M41-0002 #315 (Taxonomy); M41-0003 #316 (Vectors + Mode 2 + orchestration) |
