# AI Capabilities & Solutions — CCAA Enterprise

**Document type:** Board architecture — AI capabilities, features, and solutions by product tier  
**Status:** Proposed baseline — calibrated to Mode 2 lakehouse  
**Date:** 2026-11-18  
**Story:** M43-0001 #318  
**Related:** `docs/Project_Management/PROJECT_CHARTER.md`; `docs/DataArchitecture.md`; `docs/Complaints_Data_Classification_Indexing_Brainstorming.md`; `docs/PRODUCT_FEATURES.md`

**Architecture fit (empirical):** Mode 2 Hybrid Classification over ~1.97M–19.17M narrative-free structured complaint rows, compressed to **2,924–8,438** unique Semantic Signatures. Compact vector catalogs hold **~17,000** routing vectors (`cfpb_semantic_signatures`, `cfpb_organization_aliases`, `cfpb_entity_fingerprints`) — not 19M row-level embeddings. AI strategy therefore prioritizes **NL-to-AST routing**, **behavioral clustering**, **tabular prediction**, and **agentic orchestration over Curated Iceberg** — not brute-force per-row LLM inference.

---

## Table of contents

1. [Purpose & design principles](#1-purpose--design-principles)
2. [Platform & foundational AI capabilities](#2-platform--foundational-ai-capabilities)
3. [Internal enterprise AI solutions (Stage 1)](#3-internal-enterprise-ai-solutions-stage-1)
4. [External B2B & monetization AI solutions (Stage 2)](#4-external-b2b--monetization-ai-solutions-stage-2)
5. [Consumer-facing AI solutions (Stage 3)](#5-consumer-facing-ai-solutions-stage-3)
6. [End-to-end AI capability matrix](#6-end-to-end-ai-capability-matrix)
7. [Recommended implementation sequence](#7-recommended-implementation-sequence)
8. [Multi-cloud AI stacks (overview)](#8-multi-cloud-ai-stacks-overview)
9. [Open-source & Hugging Face stack](#9-open-source--hugging-face-stack)
10. [AWS stack (Bedrock & native services)](#10-aws-stack-bedrock--native-services)
11. [Azure AI stack (Foundry & native services)](#11-azure-ai-stack-foundry--native-services)
12. [Cross-stack architecture comparison](#12-cross-stack-architecture-comparison)
13. [Document control](#13-document-control)

---

## 1. Purpose & design principles

This document maps **AI capabilities / features / solutions** across the same four tiers used in the Project Charter products:

| Tier | Audience | Rollout stage |
|---|---|---|
| **Platform & Foundational** | Data platform, gateway, registry | Foundation (with M41 DataArchitecture expansion) |
| **Internal Enterprise** | Compliance, Legal, Escalations, Product, Vendor Risk | Stage 1 |
| **External B2B & Monetization** | Fintech compliance, law firms, risk consultants | Stage 2 |
| **Consumer-Facing** | Retail consumers | Stage 3 |

**Principles:**

1. Prefer **O(U_sig)** inference (registry + catalogs) over **O(N)** row-level LLM calls.
2. Ground natural language in **compact vector catalogs**, then execute **exact SQL** on Curated Iceberg via the Neutral Query AST.
3. Keep **Curated Iceberg** as the analytical SoR; vector stores remain rebuildable routing indexes.
4. Enforce **RBAC**, **ZIP-3 / k-anonymity (n ≥ 10)**, and **no foreign narrative exposure** on consumer and B2B surfaces.

---

## 2. Platform & foundational AI capabilities

Embedded in core infrastructure (Taxonomy Control Plane, Compact Vector Catalogs, Query AST Gateway) and reused by every downstream product.

### 2.1 Mode 2 Multi-Label Neuro-Symbolic Classifier

| Field | Detail |
|---|---|
| **What** | Deterministic `product_crosswalk` rules + DeBERTa-v3 NLI / SetFit multi-label overlay evaluating all **12 CFPB Money Topics** on unique signatures |
| **Why** | Catches cross-cutting **Fraud & Scams** and **Money Transfers** inside checking / credit card rows without Product 1:1 fiction |
| **Consumes** | Semantic Signature Registry (~2.9k–8.4k rows); `money_topics`; `product_crosswalk` |
| **Powers** | Taxonomy Control Plane; daily micro-batch ingest; Consumer Issue Navigator |

### 2.2 Self-Improving LLM Teacher & Distillation Loop

| Field | Detail |
|---|---|
| **What** | Cache misses / low-confidence scores (`NEEDS_REVIEW`, NLI &lt; ~0.65) go to a frontier LLM adjudicator (e.g. Gemini 2.5 Flash / GPT-4o-mini) grounded in official Money Topic definitions; Domain SME one-click approve; periodic SetFit distillation |
| **Why** | Keeps hot-path inference local and fast while improving taxonomy coverage |
| **Consumes** | Unseen `signature_id`s; registry `NEEDS_REVIEW` queue |
| **Powers** | Taxonomy Control Plane quality; Mode 2 container upgrades |

### 2.3 Semantic-to-AST Intent & Entity Router (NL-to-AST)

| Field | Detail |
|---|---|
| **What** | LLM + tool calling over three compact catalogs (~17k vectors) grounds intent, then emits deterministic Neutral Query AST predicates for DuckDB / cloud SQL |
| **Example** | “Chase wire transfer scams in Georgia” → `cfpb_organization_aliases` → `parent_org_id`; `cfpb_semantic_signatures` → Money Transfers + Fraud & Scams → exact Curated aggregation |
| **Consumes** | `cfpb_semantic_signatures`, `cfpb_organization_aliases`, Curated Iceberg |
| **Powers** | Query AST Gateway; B2B Visual AST Copilot; Product Friction Hub |

### 2.4 Zero-Hit Automatic Query Relaxation Agent

| Field | Detail |
|---|---|
| **What** | When filters return empty sets, broaden predicates step-by-step (e.g. Sub-issue → Issue, ZIP-3 → State) and explain the broadening in plain English |
| **Why** | Prevents dead-end UX without hallucinated SQL |
| **Consumes** | Query AST Gateway; Curated Iceberg result cardinality |
| **Powers** | All AST-backed UIs (internal + B2B) |

### 2.5 Semantic Drift & Cache-Miss Anomaly Detector

| Field | Detail |
|---|---|
| **What** | Monitors embedding distance to Money Topic centroids and registry cache-miss rate spikes |
| **Why** | Early signal when CFPB taxonomy drifts or novel complaint patterns appear |
| **Consumes** | Semantic Signature Registry; embedding space |
| **Powers** | Platform ops alerts; feeds Tier 3 / Risk Radar |

---

## 3. Internal enterprise AI solutions (Stage 1)

**Personas:** Compliance, Legal, Customer Escalations, Product Management, Vendor Risk.

### 3.1 Autonomous UDAAP & Fair-Lending Risk Briefing Agent (Systemic Risk Radar)

| Field | Detail |
|---|---|
| **What** | Tier 3 UMAP + HDBSCAN micro-topic / 7-day velocity spike (&gt;2σ) triggers an agent that runs comparative DuckDB cohorts (`parent_org_id`, ZIP-3, Older American / Servicemember tags, `timely_response`) and writes an executive Alert Feed brief |
| **Techniques** | UMAP + HDBSCAN; agentic SQL synthesis; narrative generation |
| **Consumes** | Tier 3 micro-topics; `cfpb_entity_fingerprints`; Curated Iceberg |
| **UX** | Command-center Alert Feed + Cluster Velocity Map; OIDC RBAC by business unit |

### 3.2 Precedent Twin & Policy-Grounded Resolution Copilot (CRM Embed)

| Field | Detail |
|---|---|
| **What** | Maps an open Salesforce / ServiceNow ticket to nearest `signature_id`; retrieves historical resolution distributions from Curated Iceberg; pairs with internal SOP RAG; drafts compliant response templates |
| **Techniques** | Signature similarity; outcome retrieval; policy RAG; generation |
| **Consumes** | `cfpb_semantic_signatures`; Curated Iceberg; policy corpus |
| **UX** | Embedded web component (`<complaint-copilot>`) |

### 3.3 Dispute & Escalation Risk Scorer (Ticket Triage)

| Field | Detail |
|---|---|
| **What** | LightGBM / XGBoost on Curated historical outcomes scores escalation / dispute likelihood and routes high-risk tickets to senior specialists |
| **Techniques** | Gradient-boosted trees on tabular features |
| **Consumes** | Curated Iceberg (`signature_id`, `parent_org_id`, submission channel, tags, `timely_response`, outcomes) |
| **UX** | CRM / queue priority badges |

### 3.4 Conversational Release-Impact & Root-Cause Analyst (Product Friction Hub)

| Field | Detail |
|---|---|
| **What** | Governed text-to-SQL + synthesis agent for cohort questions (e.g. Prepaid Cards dispute rates before vs after Q3 across top issuers) |
| **Techniques** | NL-to-AST; DuckDB aggregations; root-cause narrative |
| **Consumes** | Curated Iceberg; Tier 2 operational facets (Lifecycle, Failure Mode) |
| **UX** | Self-service analytics portal |

### 3.5 Behavioral Peer & Servicer Outlier Clustering (Vendor Benchmarks)

| Field | Detail |
|---|---|
| **What** | Unsupervised clustering over `cfpb_entity_fingerprints` (institution × ZIP-3 distributions) plus optional SLA escalation predictor to flag abnormal servicer / collector degradation vs peers |
| **Techniques** | Entity fingerprint clustering; LightGBM / XGBoost SLA risk |
| **Consumes** | `cfpb_entity_fingerprints`; Curated Iceberg rolled up by `parent_org_id` |
| **UX** | Interactive peer scorecards |

---

## 4. External B2B & monetization AI solutions (Stage 2)

**Personas:** Fintech compliance teams, law firms, risk consultants, enterprise data buyers.

### 4.1 No-Code Visual AST Copilot (B2B SaaS Portal)

| Field | Detail |
|---|---|
| **What** | Interactive assistant converts plain-English legal / compliance questions into validated Neutral Query AST JSON; previews Compute Unit (CU) cost before Edge Gateway execution |
| **Techniques** | NL-to-AST generation; CU estimation |
| **Consumes** | Public Curated slice; vector catalogs; Edge metering (Lane 3) |
| **Monetization** | Metered CU (e.g. metadata lookup / vector search / DuckDB scan) via event bus → Lago / Stripe |

### 4.2 Natural-Language Regulatory Watchlist & Webhook Agent

| Field | Detail |
|---|---|
| **What** | Subscribers define watchlists in plain English; embedding matcher scores new Tier 3 HDBSCAN centroids against watchlists and fires webhooks on threshold trips |
| **Techniques** | Centroid / watchlist similarity; velocity thresholds |
| **Consumes** | Tier 3 cluster stream; Edge Gateway subscriptions |
| **Monetization** | Flat add-on subscription |

### 4.3 AI-Ready Feature & Embedding Enrichment Tables (Cloud Data Shares)

| Field | Detail |
|---|---|
| **What** | Versioned Curated Parquet + `product_crosswalk` + `organization_aliases` + pre-computed **512-d SQ8** signature embeddings and dispute risk features for join into external fraud / credit models |
| **Techniques** | Precomputed embeddings; entity cross-walks; packaged features (no buyer-side NLP required) |
| **Consumes** | Curated lake; Semantic Signature Registry vectors |
| **Serving** | AWS Data Exchange; Azure Marketplace; GCP Analytics Hub |

---

## 5. Consumer-facing AI solutions (Stage 3)

**Personas:** Retail consumers (web / mobile).

### 5.1 Zero-Jargon Guided Issue Navigator

| Field | Detail |
|---|---|
| **What** | Conversational triage via Mode 2 container maps everyday language to `primary_money_topic` + cross-cutting flags (`is_fraud_scam`, `is_money_transfer`) and pre-fills the correct dispute workflow |
| **Techniques** | Mode 2 inference; guided multi-turn chat |
| **Consumes** | Mode 2 registry / container; `money_topics` (Lane 2 Edge Gateway) |
| **Privacy** | No raw vector search endpoints; never exposes other consumers’ records or narratives |

### 5.2 Predictive Resolution Turnaround & Checklist Estimator

| Field | Detail |
|---|---|
| **What** | Cohort models estimate median resolution days and produce documentation checklists from matched `signature_id` + institution tier |
| **Techniques** | Tabular / cohort prediction; checklist generation |
| **Consumes** | Aggregated Curated Iceberg outcomes |
| **Privacy** | Strict **k-anonymity (n ≥ 10)** at Query AST Gateway; zero foreign narrative exposure |

---

## 6. End-to-end AI capability matrix

| Tier | AI solution / capability | Core AI / ML techniques | Data layer consumed |
|---|---|---|---|
| **Platform** | Mode 2 Classifier & Teacher Loop | DeBERTa-v3 NLI, SetFit, LLM adjudication | Semantic Signature Registry (~2.9k–8.4k) |
| **Platform** | NL-to-AST Semantic Router | BGE-512d + LLM tool calling | Compact Vector Catalogs (~17k) + AST Gateway |
| **Platform** | Query Relaxation & Drift Detectors | Rule/AST relaxation; centroid / cache-miss monitors | AST Gateway + Registry |
| **Internal** | Autonomous UDAAP Briefing Agent | UMAP + HDBSCAN + agentic SQL synthesis | Tier 3 micro-topics + Curated Iceberg |
| **Internal** | CRM Case Resolution Copilot | Signature matching + policy RAG + generation | `cfpb_semantic_signatures` + Curated Iceberg |
| **Internal** | Escalation & Vendor SLA Predictor | LightGBM / XGBoost + entity clustering | Curated Iceberg + `cfpb_entity_fingerprints` |
| **Internal** | Product Friction Root-Cause Analyst | Governed text-to-SQL + narrative synthesis | Curated Iceberg + Tier 2 facets |
| **External B2B** | Visual AST Copilot & Watchlist Agent | NL-to-AST + centroid matching | Edge metering + Tier 3 clusters |
| **External B2B** | Pre-Computed AI Feature Shares | 512-d SQ8 embeddings + entity cross-walks | Curated Parquet (cloud marketplaces) |
| **Consumer** | Guided Navigator & SLA Estimator | Mode 2 container + k-anonymous cohort stats | Mode 2 registry + Curated Iceberg (n ≥ 10) |

---

## 7. Recommended implementation sequence

| Wave | When | Prioritize |
|---|---|---|
| **Immediate** | With M41 DataArchitecture expansion / charter alignment | **NL-to-AST Router** (~17k catalogs) + **LLM Teacher Loop** for `NEEDS_REVIEW` — validates Mode 2 registry and Golden Query Suite |
| **Next** | Stage 1 Internal MVP | **Systemic Risk Radar Narrative Agent** + **CRM Case Copilot** — structured aggregations + signature similarity; no free-text narratives required |
| **Later** | Stages 2 & 3 | **B2B Visual AST Copilot** + **Consumer Guided Triage / SLA Estimator** — after Edge CU metering and k-anonymity guardrails are live |

**Dependency spine (data before AI surfaces):**

```text
Raw Iceberg (M40 done) → Refined → Taxonomy Registry → Curated SoR → Vector Catalogs
                                    │
                                    ├── Platform AI: Mode 2 + NL-to-AST + Drift
                                    ├── Internal AI: Radar / Copilot / Friction / Peers
                                    ├── B2B AI: Visual AST / Watchlists / Feature shares
                                    └── Consumer AI: Navigator / SLA estimator
```

---

## 8. Multi-cloud AI stacks (overview)

CCAA keeps a **single portable embedding space** (**BAAI/bge-base-en-v1.5**, 512-d MRL, L2-normalized, SQ8) and **single-hub batch inference** on the Semantic Signature Registry. The Neutral Query AST Gateway sits in front of Curated Iceberg and the three compact vector catalogs (~17k vectors).

The same AI capabilities (§2–§5) can be executed on three stacks without changing the data contract:

| Stack | Best fit |
|---|---|
| **Open-source / Hugging Face** | Cloud-agnostic batch hub; local DuckDB + Chroma parity; avoid proprietary lock-in |
| **AWS (Bedrock & native)** | Production on S3 Iceberg, OpenSearch Serverless, AWS Data Exchange |
| **Azure AI (Foundry & native)** | Entra ID enterprises; ADLS Gen2 / Fabric; Dynamics / Teams integrations |

Each stack below covers: **core AI solutions**, **fine-tuning**, and **agentic AI** for that cloud.

---

## 9. Open-source & Hugging Face stack

**Best for:** primary single-compute batch hub, local laptop parity (DuckDB + Chroma), and avoiding proprietary vendor lock-in.

### 9.1 Core AI solutions & models

| Capability | Implementation |
|---|---|
| **Portable embeddings** | `BAAI/bge-base-en-v1.5` → Matryoshka truncate to **512-d** + SQ8; serve via Hugging Face **Text Embeddings Inference (TEI)** on spot GPUs or **ONNX Runtime** on developer laptops |
| **Zero-shot Mode 2 classifier** | `MoritzLaurer/DeBERTa-v3-large-mnli-fever-anli-ling-wanli` or `MoritzLaurer/bge-m3-zeroshot-v2.0` — independent scores for all 12 Money Topics on unseen `signature_id`s (Fraud/Transfer overlays) |
| **Emergent micro-topic discovery** | `umap-learn` + `hdbscan` over signature embeddings; cluster titles via `Qwen/Qwen2.5-7B-Instruct` (vLLM) |

### 9.2 Fine-tuning pipelines (LLM teacher → distilled student)

| Pipeline | Method | Outcome |
|---|---|---|
| **SetFit multi-label distillation** | After Domain SME approves ~2,000–5,000 tricky `NEEDS_REVIEW` signatures (e.g. Private vs Federal Student Loans; Payday vs Personal Loans), fine-tune **SetFit** on `BAAI/bge-base-en-v1.5` with a 12-label sigmoid head | Replaces slow cross-encoder NLI with **sub-10 ms** local CPU/GPU inference |
| **QLoRA NL-to-AST adapter** | PEFT / QLoRA on `Qwen2.5-7B-Instruct` or `Llama-3.1-8B-Instruct` using the 100-case Golden Query Suite expanded synthetically to ~2,000 prompt→AST pairs | Strict Neutral Query AST JSON with zero syntax errors |

### 9.3 Agentic AI orchestration

**Framework:** LangGraph / PydanticAI + **MCP (Model Context Protocol)** for stateful multi-step agents (e.g. Autonomous UDAAP Risk Briefing Agent).

| MCP / tool | Behavior |
|---|---|
| `resolve_org_alias(query)` | Query Chroma `cfpb_organization_aliases` |
| `resolve_signature(query)` | Query Chroma `cfpb_semantic_signatures` |
| `execute_ast_query(ast_json)` | Deterministic SQL over Curated Iceberg via DuckDB |

---

## 10. AWS stack (Bedrock & native services)

**Best for:** AWS production — S3 Iceberg, OpenSearch Serverless, AWS Data Exchange.

### 10.1 Core AI solutions & managed services

| Capability | Implementation |
|---|---|
| **Managed vector search & hybrid filters** | Hydrate ~17k catalogs from S3 Gold/Curated Parquet into **Amazon OpenSearch Serverless** (FAISS HNSW + scalar quantization) or **Aurora PostgreSQL (pgvector)** — keep BGE 512-d vectors intact |
| **LLM adjudication & narrative synthesis** | **Amazon Bedrock Batch Inference** (Claude 3.5 Haiku / Sonnet or Amazon Nova Micro/Lite) for `NEEDS_REVIEW` adjudication and Systemic Risk Radar executive briefs |
| **Tabular escalation & SLA prediction** | Train/deploy LightGBM / XGBoost with **SageMaker Autopilot / Canvas** on S3 Curated Iceberg for dispute risk and servicer SLA breaches |

### 10.2 Fine-tuning on AWS

| Pipeline | Method | Outcome |
|---|---|---|
| **SageMaker JumpStart / Training Jobs** | Spot `ml.g5.xlarge` (or similar) for SetFit multi-label distillation or QLoRA on Qwen2.5-7B / Llama-3.1-8B; export quantized artifact to S3 | Local Chroma and AWS stay synchronized on the same student model |
| **Bedrock custom model import / fine-tune** | Fine-tune **Amazon Nova Lite** on Golden Query AST pairs | Ultra-low-latency NL-to-AST inside B2B Visual AST Copilot |

### 10.3 Agentic AI on AWS

| Pattern | Implementation |
|---|---|
| **CRM Case Resolution Copilot** | **Amazon Bedrock Agents** + Knowledge Bases (internal remediation SOPs) + Action Group calling FastAPI Query AST Gateway for precedent `signature_id` win rates |
| **Consumer / B2B safety** | **Bedrock Guardrails** — PII checks, topic denial, hallucination grounding so Consumer Issue Navigator never leaks cross-customer data |
| **Event-driven Tier 3 drift** | **Step Functions + EventBridge** trigger a Bedrock Agent when SageMaker Model Monitor or Glue Data Quality detects a &gt;2σ spike |

---

## 11. Azure AI stack (Foundry & native services)

**Best for:** enterprises on Microsoft Entra ID, ADLS Gen2, Dynamics / ServiceNow / Teams.

### 11.1 Core AI solutions & managed services

| Capability | Implementation |
|---|---|
| **Managed vector catalogs** | Sync Curated Parquet catalogs from ADLS Gen2 into **Azure AI Search** (HNSW + `scalarQuantization` int8; strongly typed `filterable: true` fields) or **Azure Database for PostgreSQL Flexible Server (pgvector)** |
| **Batch classification & copilot generation** | **Azure OpenAI** Batch API (GPT-4o-mini / GPT-4.1-mini) via **Azure AI Foundry** for borderline NLI adjudication and CRM Case Resolution Copilot |
| **Automated tabular risk modeling** | **Azure Machine Learning (Automated ML)** over ADLS Gen2 / Fabric OneLake Iceberg shortcuts for SLA and dispute scorers |

### 11.2 Fine-tuning on Azure

| Pipeline | Method | Outcome |
|---|---|---|
| **Azure AI Foundry fine-tuning** | Fine-tune **Phi-4** or **GPT-4o-mini** on Neutral Query AST training pairs (serverless Foundry pipeline) | Deterministic NL-to-AST for B2B SaaS portal |
| **Azure ML custom GPU pipelines** | SetFit distillation on low-priority GPU compute; register versioned model in Azure ML Model Registry | Promote only after Golden Query Suite recall gates pass |

### 11.3 Agentic AI on Azure

**Framework:** **Azure AI Agent Service** + Semantic Kernel / AutoGen.

| Multi-agent Risk Investigation (Systemic Risk Radar) | Role |
|---|---|
| **Triage Agent** | Detects Tier 3 HDBSCAN velocity spike via Azure Monitor / Event Hubs |
| **Analyst Agent** | Code Interpreter / SQL tool against Curated Iceberg (Fabric / DuckDB) — isolates `parent_org_id` and ZIP-3 cohorts |
| **Compliance Briefing Agent** | Drafts UDAAP alert card; posts to Microsoft Teams or Enterprise Portal |

**Safety:** Wrap Consumer Issue Navigator and B2B API with **Azure AI Content Safety** + Prompt Shields — block prompt injection, enforce k-anonymity output rules, validate groundedness against Curated Iceberg facts. Entra ID JWT RBAC at the gateway.

---

## 12. Cross-stack architecture comparison

| AI dimension | Open-source / Hugging Face | AWS (Bedrock & native) | Azure AI (Foundry & native) |
|---|---|---|---|
| **Embeddings (512-d SQ8)** | BGE via HF TEI / ONNX | Self-hosted BGE on SageMaker/ECS → OpenSearch Serverless | Self-hosted BGE on Azure Container Apps → Azure AI Search |
| **Mode 2 classification** | DeBERTa-v3 NLI + distilled SetFit | SetFit on SageMaker + Bedrock Batch (Claude/Nova) teacher | SetFit on Azure ML + Azure OpenAI Batch (GPT-4o-mini) teacher |
| **Fine-tuning focus** | SetFit multi-label + QLoRA Qwen2.5-7B (NL-to-AST) | SageMaker SetFit + Bedrock Nova Lite NL-to-AST | Azure ML SetFit + Foundry Phi-4 / GPT-4o-mini NL-to-AST |
| **Agentic framework** | LangGraph / PydanticAI + MCP | Bedrock Agents + Action Groups + Step Functions | Azure AI Agent Service + Semantic Kernel / AutoGen |
| **Tabular risk / SLA** | LightGBM / XGBoost in Airflow / Spark | SageMaker + S3 Iceberg | Azure ML + ADLS / Fabric OneLake |
| **Safety & guardrails** | Presidio + AST Gateway RBAC | Bedrock Guardrails + AST Gateway | Azure AI Content Safety + Entra ID JWT RBAC |

**Portability rule:** Regardless of stack, keep the same **512-d BGE SQ8** vectors, the same **Neutral Query AST**, and the same **registry / Curated Iceberg contracts** so local Chroma, AWS, and Azure stay interchangeable at the gateway.

---

## 13. Document control

| Field | Value |
|---|---|
| Title | AI Capabilities & Solutions — CCAA Enterprise |
| Tier model | Platform · Internal · External B2B · Consumer (aligned with Project Charter) |
| Cloud stacks | Hugging Face / open-source · AWS Bedrock & native · Azure AI Foundry & native |
| Empirical mode | Mode 2; U_sig 2,924 / 8,438; ~17k catalog vectors; portable BGE 512-d SQ8 |
| Charter | `docs/Project_Management/PROJECT_CHARTER.md` |
| Data architecture | `docs/DataArchitecture.md` (gated expansion under M41) |
| Delivered under | M43-0001 #318 |
| Last updated | 2026-11-18 — multi-cloud AI stacks (§8–§12) |
