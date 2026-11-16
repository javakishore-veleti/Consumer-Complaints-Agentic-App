# M04-0012 (#158) Local Mongo ingest DAG Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Airflow DAG upserts landed CFPB complaints into local Mongo and reports status/volume via callbacks.

**Architecture:** `ccaa/mongo_ingest.py` + `ingest_cfpb_all` DAG + extended `report_execution_status` volume fields. D86.

**Tech Stack:** Airflow PythonOperator, pymongo (lazy), stdlib csv/zipfile.

## Global Constraints

- No `from app.` in DAGs (D67).
- Complaint Mongo URI: `CCA_MONGO_COMPLAINTS_URL` (not operational URL).
- Commit form: `M04-0012 #158: <summary>`.

---

## Task 1: Helper + callback volume + DAG + tests — Done

- [x] `mongo_ingest.py` + unit tests
- [x] `ingest_cfpb_all.py` + dag file test
- [x] `status_callback` volume kwargs + test
- [x] D86 / docs / upsert inventory
