# Data Architecture — CCAA Enterprise

**Document type:** Data architecture specification  
**Status:** Living draft — Raw Data Zone (Iceberg Bronze) specified first  
**Story:** M40-0001 #310  
**Related:** `docs/Project_Management/PROJECT_CHARTER.md`; `docs/Complaints_Data_Classification_Indexing_Brainstorming.md`; planned Iceberg Docker infra #311

---

## Table of contents

1. [Purpose & scope](#1-purpose--scope)
2. [Medallion overview (Bronze → Silver → Gold)](#2-medallion-overview-bronze--silver--gold)
3. [Lift Zone (local CSV zip landing)](#3-lift-zone-local-csv-zip-landing)
4. [Apache Iceberg Raw Data Zone (Bronze)](#4-apache-iceberg-raw-data-zone-bronze)
5. [Document control](#5-document-control)

---

## 1. Purpose & scope

This document defines the **canonical data architecture** for ingesting ~2M+ CFPB consumer complaint records into a portable lakehouse that supports local development and multi-cloud promotion (S3 / ADLS / GCS).

**Initial scope of this revision:** the **Lift Zone** (local workflow zip inputs) and the **Apache Iceberg Raw Data Zone (Bronze)** — immutable, zero-loss landing tables fed by Airflow + PySpark from already-local CSV zip endpoints.

Silver (semantic signatures / classification) and Gold (enriched vector lake) zones are outlined only at overview level until dedicated sections are added under follow-on stories.

---

## 2. Medallion overview (Bronze → Silver → Gold)

| Zone | Responsibility | Primary tech |
|---|---|---|
| **Lift Zone** | Durable local copies of CFPB CSV zip inputs produced by existing download/filter workflow endpoints | Local filesystem folder (workflow-managed) |
| **Raw / Bronze** | Immutable Iceberg tables; all-string business columns + audit lineage; no business transforms | Apache Iceberg + ZSTD Parquet + PySpark |
| **Silver** | Deduped semantic signatures, taxonomy joins, enrichment registry | Iceberg / Parquet + ML enrichment |
| **Gold** | Business facts + portable embeddings + flat filter metadata for vector fan-out | Parquet/Iceberg + vector stores |

Data flows **unidirectionally**: Lift → Raw → Silver → Gold → Vector serving caches.

---

## 3. Lift Zone (local CSV zip landing)

The **Lift Zone** is the operational staging area **outside** the Iceberg warehouse where Airflow (or equivalent) workflow endpoints already store downloaded / filtered CFPB **CSV zip** inputs.

### 3.1 Architectural role

- **Source of truth for files, not tables:** Lift Zone holds opaque zip artifacts (e.g., 3-month filter zip, “all complaints” zip). It is **not** queryable Iceberg storage.
- **No re-download required for Raw backfills:** Raw Zone ingestion reads from Lift Zone paths for the active dataset slice (`3m`, `6m`, `9m`, `12m`, `all`).
- **Ephemeral unzip staging is separate:** Airflow unpacks into `/tmp/airflow_stage/<run_id>/` for a single run; the Lift Zone zip remains durable for replay.

### 3.2 Relationship to Raw Zone

```text
[CFPB source / download workflows]
            │
            ▼
[Lift Zone: local folder of CSV .zip files by dataset slice]
            │
            ▼  Airflow Sensor → Unzip → Pre-ingestion gate
[Ephemeral staging CSV]
            │
            ▼  PySpark Bronze hydration
[Apache Iceberg Raw Data Zone: raw.cfpb_complaints_* ]
```

### 3.3 Infra dependency (planned)

Standing up Spark + Iceberg for this path is tracked as **M40-0002 #311** (Apache Iceberg Spark Docker container), aligned with the [Iceberg Spark quickstart](https://iceberg.apache.org/spark-quickstart/#reading-data-from-a-table). That story wires Airflow PySpark workers to the catalog/warehouse while continuing to read zips from the Lift Zone.

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

### 4.7 Planned runtime: Iceberg Spark Docker (#311)

Raw Zone compute is expected to run against a containerized Spark + Iceberg stack (see [Spark quickstart — reading a table](https://iceberg.apache.org/spark-quickstart/#reading-data-from-a-table)). Implementation of that container and Airflow wiring is **M40-0002 #311** and must not start until that story is story-started under Superpowers.

---

## 5. Document control

| Field | Value |
|---|---|
| Title | Data Architecture — CCAA Enterprise |
| Initial focus | Lift Zone + Apache Iceberg Raw Data Zone (Bronze) |
| Related charter | `docs/Project_Management/PROJECT_CHARTER.md` |
| Related brainstorming | `docs/Complaints_Data_Classification_Indexing_Brainstorming.md` |
| Follow-on infra | M40-0002 #311 — Iceberg Spark Docker for Raw Zone |
| Delivered under | M40-0001 #310 |
