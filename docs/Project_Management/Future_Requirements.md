# Future Requirements — CCAA Enterprise

**Document type:** Board — future requirements & portfolio gap-closure track  
**Status:** Proposed backlog (not committed product scope until milestoned `[Story]` + story-start)  
**Date:** 2026-11-18  
**Story:** M44-0001 #319  
**Related:** `docs/Project_Management/PROJECT_CHARTER.md`; `docs/Project_Management/AI_Capabilities_Solutions.md`; `docs/DataArchitecture.md`; `docs/PRODUCT_FEATURES.md`

**Context:** CCAA Mode 2 lakehouse work strongly signals AI architecture / multi-cloud / agentic / MLOps leadership. Against cyber/IC AI Lead postings (e.g. Nightwing AI Lead — SOC, ATO, IC/NRO, large-team authority), several gaps remain. This document records **what must be added later** — including a parallel **Cyber SOC AI track** that reuses CCAA patterns without renaming CFPB Money Topics as “cyber.”

---

## Table of contents

1. [Purpose](#1-purpose)
2. [Current match vs gaps (summary)](#2-current-match-vs-gaps-summary)
3. [Requirements that cannot be closed by this repo alone](#3-requirements-that-cannot-be-closed-by-this-repo-alone)
4. [Future product track — Cyber SOC AI lakehouse](#4-future-product-track--cyber-soc-ai-lakehouse)
5. [Future IA / ATO-ready AI governance pack](#5-future-ia--ato-ready-ai-governance-pack)
6. [Future adversarial ML & red-team eval suite](#6-future-adversarial-ml--red-team-eval-suite)
7. [Future MLOps / DevSecOps for mission AI](#7-future-mlops--devsecops-for-mission-ai)
8. [Future leadership-scale signal (documentation)](#8-future-leadership-scale-signal-documentation)
9. [SIEM / SOAR / detection interoperability](#9-siem--soar--detection-interoperability)
10. [Recommended sequencing](#10-recommended-sequencing)
11. [Acceptance criteria (when a future milestone opens)](#11-acceptance-criteria-when-a-future-milestone-opens)
12. [Document control](#12-document-control)

---

## 1. Purpose

1. Separate **in-scope CCAA (CFPB complaint intelligence)** from **future cyber SOC AI** work that reuses the same architecture spine.  
2. List portfolio and career requirements needed to match **AI Lead** roles focused on cybersecurity operations, IC/mission partners, ATO, and large engineering orgs.  
3. Keep gate discipline: nothing here authorizes Middleware / Portals / DAG / `DataArchitecture.md` edits until an open milestoned `[Story]` is story-started.

---

## 2. Current match vs gaps (summary)

| Area | CCAA today | Future requirement |
|---|---|---|
| AI strategy & architecture | Mode 2, Iceberg medallion, registry, AST, multi-cloud vectors | Keep; extend patterns to cyber telemetry |
| Agentic AI / multi-cloud | HF / Bedrock / Azure stacks documented | Implement cyber-facing agents on same stacks |
| Governance (privacy/RBAC) | k-anonymity, taxonomy control plane | Add IA/ATO-style model security pack |
| Cyber / SOC / SIEM / SOAR | **Not present** | New cyber data products + adapters |
| DoD IA / ATO / NIST 800-171 / IC | **Not present** | Documentation + practice patterns; real ATO needs cleared program |
| Lead 50–100+ FTEs / $50M+ | Architect docs only | Career/org leadership + RACI pack in-repo |
| Adversarial ML / AI red-team | Light mention | Formal eval suite |
| On-site / clearance | N/A to repo | Personal / employer path |

---

## 3. Requirements that cannot be closed by this repo alone

These remain **out of band** for CCAA code; track them as career / employer prerequisites:

| ID | Requirement | Notes |
|---|---|---|
| FR-EXT-01 | Cleared IC / NRO / mission-partner experience | Requires sponsor / cleared role |
| FR-EXT-02 | On-site Sterling VA (or equivalent) availability | Location constraint for specific jobs |
| FR-EXT-03 | Documented technical leadership of 50+ engineers / 100+ FTE / $50M+ programs | Org leadership history |
| FR-EXT-04 | Real Authority to Operate (ATO) ownership for AI components | Classified / DoD program artifact — not faked in public repo |

**Repo stance:** Publish **ATO-ready documentation patterns** and cyber portfolio demos; never claim fake cleared ATO.

---

## 4. Future product track — Cyber SOC AI lakehouse

**Goal:** Parallel product line that reuses Lift → Raw → Refined → Curated + Semantic Signature Registry + compact vector catalogs + Query AST Gateway + agent tiers.

| ID | Requirement | Detail |
|---|---|---|
| FR-CYBER-01 | Security telemetry Lift Zone | Ingest open/public cyber datasets and/or lab telemetry (e.g. Zeek, Suricata, OS logs; UNSW-NB15 / CIC-IDS / Mordor-class corpora) as zip/parquet landing — **separate namespace from CFPB** |
| FR-CYBER-02 | Cyber Raw / Refined / Curated Iceberg | Same medallion contracts; cyber-specific schemas; quarantine; monthly (or hour) partitions as appropriate |
| FR-CYBER-03 | Detection Signature Registry | Mode 2 analog: Tier-1 deterministic rules (Sigma/YARA-like); Tier-2 ML/NLI overlays; Tier-3 HDBSCAN emergent TTPs; `signature_id` over behavior tuples — **O(U_sig) not O(N)** |
| FR-CYBER-04 | Compact cyber vector catalogs | e.g. `cyber_detection_signatures`, `cyber_asset_aliases`, `cyber_entity_fingerprints` — ~catalog scale, not full packet index |
| FR-CYBER-05 | Cyber Risk Radar agent | Same briefing-agent pattern as UDAAP Radar: &gt;2σ velocity → DuckDB cohorts → executive brief (ATT&CK-oriented language) |
| FR-CYBER-06 | SOC assist / case copilot | Signature match + historical disposition stats + playbook-grounded draft (policy RAG) |
| FR-CYBER-07 | Explicit domain boundary | Docs and tables must state **CFPB ≠ cyber**; shared architecture, different data products |

---

## 5. Future IA / ATO-ready AI governance pack

| ID | Requirement | Detail |
|---|---|---|
| FR-IA-01 | AI system security ADR | Security-by-design for registry, embedder, agents, gateway (data classification, secrets, logging, rollback) |
| FR-IA-02 | Model inventory & model cards | Every production model: purpose, data, limits, eval metrics, owner, version |
| FR-IA-03 | NIST AI RMF + 800-171 mapping template | Control matrix mapping CCAA/cyber AI components to illustrative NIST controls — labeled as **template**, not accreditation evidence |
| FR-IA-04 | Continuous monitoring plan | Cache-miss rate, FPR/FNR, drift, guardrail blocks, AST zero-hit rate |
| FR-IA-05 | Safe fallback modes | Deterministic rules-only path when NLI/LLM unavailable; Blue index keep-alive on failed Golden Suite |
| FR-IA-06 | Bias / robustness assessment checklist | Documented tests before promote; human sign-off for Tier-1 rule changes |

---

## 6. Future adversarial ML & red-team eval suite

| ID | Requirement | Detail |
|---|---|---|
| FR-ADV-01 | Prompt-injection suite vs NL-to-AST | Attempts to emit unsafe SQL/AST; gateway must refuse |
| FR-ADV-02 | Registry / training data poisoning scenarios | Detect anomalous signature floods; quarantine path |
| FR-ADV-03 | Embedding / centroid drift attacks | Synthetic signatures that shift Money Topic or detection centroids |
| FR-ADV-04 | Guardrail verification | Bedrock Guardrails / Azure Content Safety / Presidio paths in AI Capabilities stacks |
| FR-ADV-05 | Red-team report artifact | Periodic scored report with severity, repro, mitigation owner |

---

## 7. Future MLOps / DevSecOps for mission AI

| ID | Requirement | Detail |
|---|---|---|
| FR-MLOPS-01 | Golden Detection / Golden Query Suite in CI | Promote models/catalogs only after gate passes |
| FR-MLOPS-02 | CI/CD for data + models + security ops | Pipelines for registry export, embed, vector Blue/Green, rollback |
| FR-MLOPS-03 | Model monitor analog | Alert on FPR spike, cache-miss spike, latency SLO breach → auto-rollback |
| FR-MLOPS-04 | Multi-cloud promote parity | Same 512-d BGE SQ8 artifact to Chroma / OpenSearch / Azure AI Search |

---

## 8. Future leadership-scale signal (documentation)

| ID | Requirement | Detail |
|---|---|---|
| FR-LEAD-01 | Pod topology & RACI for 50-engineer AI org | How Data Platform / Search / Detection / Security / Experience pods interact |
| FR-LEAD-02 | AI engineering standards pack | Design patterns, review gates, Definition of Done for models and agents |
| FR-LEAD-03 | Hiring / skill-gap matrix | Roles: ML eng, detection eng, data eng, security eng — maps to Nightwing-style team lead narrative |
| FR-LEAD-04 | Technical risk register for AI | Model drift, adversarial ML, data quality, cost, schedule — with contingency plans |

---

## 9. SIEM / SOAR / detection interoperability

| ID | Requirement | Detail |
|---|---|---|
| FR-SIEM-01 | AST → SIEM query adapters | Translate Neutral Query AST to Elastic / OpenSearch / Splunk-style filters (LCD predicates) |
| FR-SIEM-02 | Detection framework exports | Export Tier-1 rules toward Sigma/YARA-like artifacts where applicable |
| FR-SIEM-03 | SOAR playbook stubs | Triage → enrich (registry + AST) → escalate; webhook/case create stubs for lab tools |
| FR-SIEM-04 | Correlation / anomaly models | Document LightGBM/XGBoost (or equivalent) on Curated cyber features for escalation scoring |

---

## 10. Recommended sequencing

| Wave | Focus | IDs |
|---|---|---|
| **A — Board & ADRs** | Future Requirements (this doc); IA ADR outline; domain boundary | FR-IA-01…06, FR-CYBER-07, FR-LEAD-* |
| **B — Cyber vertical slice** | Open dataset → Iceberg → Detection Registry → OpenSearch catalog → Risk Briefing Agent | FR-CYBER-01…06, FR-SIEM-01 |
| **C — Hardening** | Adversarial suite + Golden Detection CI + monitor/rollback | FR-ADV-*, FR-MLOPS-* |
| **D — Interop** | SOAR stubs, Sigma/YARA export, multi-cloud cyber promote | FR-SIEM-02…04 |
| **Parallel (career)** | Clearance path, cyber certs, real leadership roles | FR-EXT-* |

**Dependency spine:**

```text
CCAA spine (done/in progress): Iceberg + Mode 2 Registry + AST + Multi-cloud AI stacks
        │
        ▼
Future cyber track: Telemetry Lift → Cyber Medallion → Detection Registry → SIEM/SOAR adapters
        │
        ├── IA/ATO-ready pack (templates)
        ├── Adversarial eval + MLOps gates
        └── Leadership RACI / standards pack
```

---

## 11. Acceptance criteria (when a future milestone opens)

A future cyber/IA milestone is **done** only when:

- [ ] Cyber tables/namespaces are separate from CFPB complaint products  
- [ ] At least one end-to-end lab slice: ingest → Curated → vector catalog → agent brief  
- [ ] ATO-ready template pack published (explicitly non-accreditation)  
- [ ] Adversarial eval suite runs in CI with a scored report  
- [ ] SIEM AST adapter documented for at least one engine (e.g. OpenSearch)  
- [ ] No claim of cleared IC/ATO completion unless true external evidence exists  
- [ ] All product code under open `[Story]` + Milestone + story-start + Superpowers  

---

## 12. Document control

| Field | Value |
|---|---|
| Title | Future Requirements — CCAA Enterprise |
| Path | `docs/Project_Management/Future_Requirements.md` |
| Trigger | Nightwing AI Lead gap analysis (cyber/SOC/ATO/scale) |
| Transferable spine | Mode 2 registry, Iceberg medallion, AST gateway, ~catalog vectors, multi-cloud AI |
| Non-goals | Fake ATO; conflating CFPB with SOC; product code without stories |
| Delivered under | M44-0001 #319 |
