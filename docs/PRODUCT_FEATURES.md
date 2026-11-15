# Product features

Consumer Complaints platform, built hands-on and step by step. This file lists **what the product does**.
How it is built is in [ARCHITECTURE.md](../Middleware/ConsumerComplaintsHandsOn/ARCHITECTURE.md) and the
detailed decisions are in [DESIGN.md](../Middleware/ConsumerComplaintsHandsOn/DESIGN.md).

Status legend: **[Done]** exists in the repo, **[Planned]** decided but not built, **[Open]** not decided yet.

---

## 1. Purpose

Load the public CFPB Consumer Complaint Database into a local or cloud MongoDB through an admin portal, and later
build an intelligence app on top of it. Everything is run from the admin portal; the heavy work (download, ingest)
is done asynchronously by Apache Airflow.

## 2. Applications

| App | What it is | Status |
|---|---|---|
| `consumer-complaints-admin` | Angular admin portal under `Portals/consumer-complaints-admin/`. Imports datasets, ingests them into the database, shows status; syncs system secrets to Airflow. | Imports [Done]; Sync secrets UI [Done] (#153); DB Ingest / AppEndpoints [Planned] (M04) |
| Middleware API | FastAPI service (`Middleware/ConsumerComplaintsHandsOn`). The only thing the portal talks to. | Core APIs [Done] (M02/M03); AppEndpoints + ingest/index APIs [Planned] (M04) |
| Apache Airflow | Runs the download and ingest (and later index) jobs asynchronously. | Local Docker [Done]; download/filter DAGs [Done]; ingest/index DAGs [Planned] (M04) |
| `consumer-complaints-Intellect` | Intelligence app over complaint Mongo + local vectors (RAG / agentic). | [Planned] M05 (#152) — after M04 vectors |

## 3. The data

- **Source:** the CFPB Consumer Complaint Database, free to download from the government website.
  Field reference: <https://cfpb.github.io/api/ccdb/fields.html>.
- **Fields (15):** Date received, Product, Sub-product, Issue, Sub-issue, Company public response, Company, State,
  ZIP code, Tags, Submitted via, Date sent to company, Company response to consumer, Timely response?, Complaint ID.
- **No free-text complaint narrative.** The database is structured records only.
- **Size (as of 14 Nov 2026):** 19,170,856 complaints in total; 2,036,290 in the last 3 months (8/14/2026 to 11/14/2026).
  About 93% of the last 3 months is one product, "Credit reporting or other personal consumer reports".
- **Download limits found on the CFPB site** (see the screenshots in `docs/Design/`):
  - The filtered CSV download is **limited to 100,000 complaints**, so the 3-month window (2.0M) cannot be downloaded
    with a filter. The site disables that option.
  - The only complete download is **"All complaint data"**, one large zipped CSV (about 350 MB compressed).
  - In the part of that file I sampled, rows are **not sorted by date**, so a 3-month slice means reading the whole file
    and filtering by `Date received`.
- **The dataset is never committed to this repository.** It is fetched by a registered workflow (feature F3).

![CFPB filtered download blocked](Design/ComplainData-Download-Screenshot-2.png)

## 4. Features

### F1. Admin portal navigation [In progress]
- Top-level menu **DataSets** [Done] (#63, D69).
- Left navigation under it: **Imports** [Done] (#63); **DB Ingest** visible but disabled until its screen is built (D13).
- Imports shows one accordion per MIO with status from `GET /mios/status` [Done] (#64, D71); start + refresh [Done] (#65, D72); picker is per-MIO `allowed_workflows` [Done] (#141, D84). DB Ingest will mirror that later.
- Later: more datasets / MIOs are just more accordions / rows (for example "6 months").

### F2. Imports: bring the dataset in [In progress]
- Per accordion, show whether that MIO is ingested or not, when, and if it failed, why. Status comes from
  `GET /mios/status` (#45 / D61), not from guessing [Done] (#64, D71).
- A button starts the download [Done] (#65, D72 / #141, D84): picker options come from that MIO’s `allowed_workflows` on `GET /mios/status` (All → `download_cfpb_all`; 3 months → `filter_cfpb_3_months`; 6/9/12 unbound → empty / Start disabled). Starts with `mio_id` (`POST /workflows/{id}/start`; API rejects unbound), then refreshes status (manual Refresh; no polling). Start is also disabled while the ingest is `requested`/`started`. The real work runs in Airflow.
- **One API endpoint starts any registered workflow** (D46: there is no usecase).
- The **3 months** dataset is the **All** file filtered to the last 3 months, because the site cannot export 3 months.
- The same flow works locally (3 months, small) and in the cloud (All).

### F3. Registered workflows (no data in the repo) [Planned]
Each workflow that downloads or ingests data is registered in the database, so the portal can list it and start it.

| Registry column | Meaning |
|---|---|
| Workflow name | up to 100 characters, shown in the portal |
| Workflow engine type | Apache Airflow, AWS Step Functions, or another engine |
| Engine workflow id | the engine's own id: the Airflow DAG id, the Step Functions state machine |
| Config | JSON with anything about the workflow, so a definition is reusable |

- Every execution is recorded in an execution log with the same information.
- There can be several download workflows. Each knows its own source (local, GitHub, Drive, S3, Azure Blob, GCS, plain HTTP(S) and so on), so the API has no source-location types.
- Credentials never live in the repo.
- The registry and the catalog (datasets, dataset locations, MIOs, and their ingest log) live in the admin schema `consumer_comp_admin_db` (D48, D49). The RAG layer is a later milestone (D53).

### F4. System secrets sync (C) [In progress — M04 #145]
- Fixed system names live in git-ignored `.env` (never in git, never shown in Admin UI).
- **Inventory (names only):**
  | Role | Names | Source of truth |
  |---|---|---|
  | Synced to Airflow Variables (D42) | `CCA_CALLBACK_SECRET`, `CCA_API_URL`, `CCA_DB_URL`, `LOCAL_DATA_PATH_CFPB` | `CICD/Local/airflow/Airflow_Variables_Upsert.txt` |
  | API-only (not upserted) | `CCA_AIRFLOW_API_BASE_URL`, `CCA_AIRFLOW_API_USERNAME`, `CCA_AIRFLOW_API_PASSWORD`, `CCA_OPERATIONAL_STORE`, `CCA_DATA_DIR`, `CCA_MONGO_OPERATIONAL_URL` | `.env.example` comments |
- Admin **Operations → Sync secrets** POSTs `POST /management/airflow/upsert-secrets` (#77 API, #153 UI). Outcomes only; values never rendered.
- Local only until M06.

### F5. AppEndpoints (D) [In progress — M04 #146]
- Categorized endpoints (source / ingest / index / db) with from/to refs to locations and env-var *names* (D85).
- Schema + DAO + CFPB source seed: #155. List/read API #156; thin Admin UI #157.
- Imports (then ingest/index) use AppEndpoints. Local/HTTP first; no cloud spend.

### F6. DB Ingest: load complaints into MongoDB (A) [Planned — M04 #147]
- Airflow ingest DAG writes **local Mongo** complaint docs in batches (upsert by Complaint ID).
- **DB Ingest** Admin screen mirrors Imports; only after download completed for that MIO.
- API never bulk-writes complaint documents.
- Stories: #158 DAG+callbacks, #159 register/bind, #160 Admin screen.
- Plain Python batches first; PySpark only if measured. **[Open]**

### F7. Dataset locations expansion (B) [Planned — M04 #148]
- Resolve from/to via catalog locations + AppEndpoints (local + HTTP).
- Cloud location types stub-only until local is hard (M06 later).
- Stories: #161 DAG resolution, #162 Admin clarity.

### F8. Local vector indexing (E) [Planned — M04 #149]
- Index local Mongo complaints into a **local** vector store (Docker and/or pgvector).
- Stories: #163 store+DAG, #164 register+Admin start.
- Cloud vector DBs out of scope until local path is hard.

### F9. Status tracking and history [Done for download; extends with ingest/index]
- `app_workflows_exec_log` + `mios_ingest_log` (D50); Airflow reports via API callbacks only.

### F10. Two environments, one codebase [Planned]
- **Local first — 100% until hardened** (M04/M05). **Cloud** in M06 after local DoD. Config, not code forks.

### F11. Data stores [In progress]
- **MongoDB (complaints):** local container [Done]; bulk load [Planned] M04.
- **Operational store:** SQLite default; Postgres/Mongo via `.env` [Done] M03. Will hold AppEndpoints (M04).

### F12. Database schema versioning [Done locally; cloud workflow deferred to M06]
- Alembic migrations create and evolve the operational database (Mongo ops profile uses bootstrap).
- Locally, the start script migrates/bootstraps, then starts the API.
- Cloud migrations: M06 (#24).

### F13. API contract [Done for current surface]
- Committed OpenAPI (`openapi.json`) checked in CI; regenerate when models change.

### F14. Developer experience [Done]
- Profiled local containers + portals npm scripts; `uv` for Middleware; Node 22+ for Admin.

### F15. MIO ACL (F) [Planned — M05 #151]
- Who may start which MIO (internal / partner / user). Enforce on start-workflow. After users foundation. Story #165.

### F16. Intelligence app (G) [Planned — M05 #152]
- `consumer-complaints-Intellect`: query local Mongo + local vectors. Not Admin Imports. Story #166.
- Early RAG draft on `backups/Cursor_Initial_Impl` is reference only.

## 5. Delivery status

| Item | Status |
|---|---|
| M01 foundation / M02 downloads / M03 Admin E2E | Done |
| Upsert secrets API (D42) + Admin Sync UI | Done (#77, #153); inventory docs #154 |
| AppEndpoints / DB Ingest / locations harden / local vectors | Planned M04 (#144) |
| MIO ACL + Intellect | Planned M05 (#150) |
| Cloud deployment | Planned M06 (#73) |

## 6. Milestones

| Milestone | Focus | Status |
|---|---|---|
| M01–M03 | Foundation, downloads, Admin E2E | Complete |
| **M04** | Local ops hardening: **C→D→A→B→E** (#144) | In progress |
| **M05** | Intellect + MIO ACL: **F→G** (#150) | Planned |
| M06 | Cloud deployment | Planned (#73) |

## 7. Open questions

1. ~~AppEndpoints exact columns / categories~~ — closed by D85 / #155 (`source`\|`ingest`\|`index`\|`db`).
2. Complaint Mongo connection string naming for DAGs (alongside ops store) — decide with #158.
3. Vector store choice for local MVP (pgvector vs dedicated container) — decide with #163.
4. Does Intellect share the operational database? (still open)
5. What does "Airflow" mean in the portal chrome (link vs screen)? (still open)
