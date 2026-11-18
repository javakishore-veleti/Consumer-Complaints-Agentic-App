# Complaints Data Classification & Indexing — Brainstorming

Architecture and modeling notes for classifying ~1.97M CFPB consumer complaint rows into the 12 official CFPB Consumer Education **Money Topics**, then indexing into vector stores (Chroma and multi-cloud). Content preserved from design brainstorming; formatted for readability.

## Table of contents

1. [Money Topics taxonomy](#1-money-topics-taxonomy)
2. [Why Product does not map 1-to-1 to Money Topics](#2-why-product-does-not-map-1-to-1-to-money-topics)
3. [Is classifying before vector indexing a good idea?](#3-is-classifying-before-vector-indexing-a-good-idea)
4. [Architectural mindset](#4-architectural-mindset)
5. [What NLI means](#5-what-nli-means)
6. [Model landscape for multi-label taxonomy mapping](#6-model-landscape-for-multi-label-taxonomy-mapping)
7. [Why specific models were selected](#7-why-specific-models-were-selected)
8. [Decision matrix for modeling strategy](#8-decision-matrix-for-modeling-strategy)
9. [Three-tier model cascade (when rules are viable)](#9-three-tier-model-cascade-when-rules-are-viable)
10. [Revised many-to-many classification architecture](#10-revised-many-to-many-classification-architecture)
11. [Semantic Signature Registry & Cache-First pattern](#11-semantic-signature-registry--cache-first-pattern)
12. [Historical vs real-time classification](#12-historical-vs-real-time-classification)
13. [Full solution architecture for ~1.97M rows](#13-full-solution-architecture-for-197m-rows)
14. [Same embeddings across all vector stores](#14-same-embeddings-across-all-vector-stores)
15. [Multi-cloud vector store mapping](#15-multi-cloud-vector-store-mapping)
16. [Real-time / micro-batch extension](#16-real-time--micro-batch-extension)
17. [Master end-to-end system architecture](#17-master-end-to-end-system-architecture)
18. [Gold metadata contract & dual-path consumption](#18-gold-metadata-contract--dual-path-consumption)
19. [Governance & Day-2 operations](#19-governance--day-2-operations)
20. [Illustrative mapping notes (deterministic cues vs overrides)](#20-illustrative-mapping-notes-deterministic-cues-vs-overrides)
21. [Deep dive: Data Modeling, Taxonomy, Compute Economics & Multi-Cloud Portability](#21-deep-dive-data-modeling-taxonomy-compute-economics--multi-cloud-portability)
22. [What “canonical” means in this solution](#22-what-canonical-means-in-this-solution)
23. [Business data modeling & taxonomy design](#23-business-data-modeling--taxonomy-design)
24. [Tech stack & physical representation by layer](#24-tech-stack--physical-representation-by-layer)
25. [Local development parity for the full 2M dataset](#25-local-development-parity-for-the-full-2m-dataset)
26. [Why not Postgres or MongoDB as the data lake](#26-why-not-postgres-or-mongodb-as-the-data-lake)
27. [Hybrid local serving: Chroma vs optional pgvector](#27-hybrid-local-serving-chroma-vs-optional-pgvector)
28. [CI/CD promotion & multi-cloud release pipeline](#28-cicd-promotion--multi-cloud-release-pipeline)
29. [Observability, drift detection & FinOps governance](#29-observability-drift-detection--finops-governance)
30. [Executive ADR-001 & phased 90-day implementation roadmap](#30-executive-adr-001--phased-90-day-implementation-roadmap)
31. [Day-1 deliverables: Neutral Query AST & Golden Query Suite](#31-day-1-deliverables-neutral-query-ast--golden-query-suite)
32. [PII/redaction compliance & multi-tenant access control (RBAC)](#32-piiredaction-compliance--multi-tenant-access-control-rbac)
33. [Data products & front ends for business and customers](#33-data-products--front-ends-for-business-and-customers)
34. [Serving all three business models: Multi-Persona Experience Layer](#34-serving-all-three-business-models-multi-persona-experience-layer)
35. [Unified monetization, metering, API gateway & multi-persona front-end stack](#35-unified-monetization-metering-api-gateway--multi-persona-front-end-stack)
36. [Master system architecture diagram & team topology / resource sizing](#36-master-system-architecture-diagram--team-topology--resource-sizing)

---

## 1. Money Topics taxonomy

Classifying complaints using the **12 official CFPB Money Topics** (Consumer Education → Money topics) gives a clean, standardized taxonomy across all ~1.97 million rows:

- Auto Loans
- Bank Accounts & Services
- Credit Cards
- Credit Reports & Scores
- Debt Collection
- Fraud & Scams
- Money Transfers
- Mortgages
- Payday Loans
- Prepaid Cards
- Private Student Loans
- Reverse Mortgages

CSV/Mongo rows have both explicit **Product / Sub-product** labels and **Issue / Sub-issue** descriptions (for example, “Fraud or scam” inside a Checking Account complaint). A hybrid approach is therefore natural: rules (or cues) for clear product matches, and semantic / NLI models for cross-cutting topics such as **Fraud & Scams** and **Money Transfers** that hide inside other product categories.

### Direct Product / Sub-product cues (deterministic candidates)

| Money topic | Typical CFPB Product / Sub-product cue |
|---|---|
| Auto Loans | Vehicle loan or lease |
| Mortgages | Mortgage (excluding Reverse mortgage) |
| Reverse Mortgages | Reverse mortgage |
| Credit Cards | Credit card; or Credit card or prepaid card where sub-product is credit card |
| Prepaid Cards | Prepaid card |
| Payday Loans | Payday loan, title loan, personal loan, or advance loan (or Payday loan) |
| Private Student Loans | Student loan (specifically Private student loan) |
| Debt Collection | Debt collection |
| Credit Reports & Scores | Credit reporting, credit repair services, or other personal consumer reports (or Credit reporting) |
| Money Transfers | Money transfer, virtual currency, or money service |
| Bank Accounts & Services | Checking or savings account |

### Cross-cutting semantic override (Fraud & Scams & Money Transfers)

Even when a complaint’s Product is Checking or savings account or Credit card, if the Issue or Sub-issue involves unauthorized transactions, phishing, scams, or wire delays, semantic similarity / NLI can flag **Fraud & Scams** or **Money Transfers** as a secondary or primary topic.

By storing both `money_topic` / `primary_money_topic` and `secondary_money_topic` (or multi-label flags) in vector metadata (and Parquet for AWS / Azure / GCP), a user filtering by either Bank Accounts & Services or Money Transfers can still retrieve overlapping cases.

---

## 2. Why Product does not map 1-to-1 to Money Topics

The CFPB complaint **Product / Sub-product** taxonomy does **not** map 1-to-1 to the 12 consumer education Money Topics. That mismatch shows up in real data as:

- **Many-to-one bundling:** Broad operational categories (such as “Payday loan, title loan, personal loan, or advance loan” or “Credit reporting or other personal consumer reports”) bundle products like installment/personal loans or tenant screening that do not have their own standalone Money Topic on the consumer portal.
- **Cross-cutting themes (Fraud & Scams):** In the complaint database, Fraud & Scams is not a Product at all—it is buried inside Issue and Sub-issue fields across checking accounts, credit cards, wire transfers, and crypto.
- **Sub-product splits (Student Loans & Mortgages):** The Product field groups all student loans together, whereas the Money Topic is specifically **Private Student Loans** (requiring separation of federal vs private via Sub-product and Issue). Similarly, **Reverse Mortgages** is a Sub-product under Mortgage, not a top-level Product.
- **2026 taxonomy updates:** The CFPB periodically consolidates or renames complaint product and issue labels, creating legacy and modern label variations inside multi-month exports.

Therefore a hard 1-to-1 rule table alone is insufficient as the sole production classifier; treat Money Topics as **many-to-many / multi-label** semantic targets evaluated over the full concatenated context (Product + Sub-product + Issue + Sub-issue + Tags).

---

## 3. Is classifying before vector indexing a good idea?

**Yes.** Classifying data before indexing into vector stores is a foundational best practice in enterprise RAG and search architecture.

In production systems, relying solely on raw vector similarity without pre-computed classification metadata leads to poor precision, higher cloud bills, and unreliable user experiences. Pre-classification transforms an unstructured semantic index into a hybrid, precision-filtered retrieval engine.

### Why pre-classification wins architecturally

- **Eliminates semantic drift & false positives (hard pre-filtering):** Vector embeddings measure conceptual closeness, not business boundaries. Without pre-classification, a semantic search for “wire transfer scam” might return a mortgage escrow dispute or a credit card chargeback simply because they share words like “funds” and “unauthorized.” When you classify first and store money topics as metadata, the query engine applies a deterministic pre-filter (`WHERE money_topic = 'Money Transfers'`), guaranteeing zero cross-domain pollution.
- **Dramatically cuts cloud vector latency & compute:** Scanning a 2-million-vector HNSW graph globally is far slower and more expensive than filtering down to a 150,000-vector slice first. Across AWS OpenSearch, Azure AI Search, and GCP Vertex AI, metadata pre-filtering reduces the search space before distance calculations occur, lowering p99 query latency and keeping cloud instance sizing smaller.
- **Enables hybrid routing (SQL + vector):** Once records are classified into the 12 CFPB Money Topics in the Gold Lakehouse, the application layer can answer both quantitative questions (“What percentage of Fraud & Scams complaints were closed with monetary relief in Q3?” via SQL) and qualitative discovery questions (“Show examples of how banks responded to servicer transfer delays” via vector search) using the exact same taxonomy.
- **Single-compute multi-cloud fan-out:** Because the roadmap spans Chroma, AWS, Azure, and GCP, classifying upstream in the ETL / Lakehouse layer ensures ML inference cost is paid once. Every downstream vector store receives identical, governed metadata without duplicating classification logic inside four different cloud ingestion pipelines.

### Trade-offs and mitigations

| Trade-off | Mitigation |
|---|---|
| Taxonomy evolution (re-classification cost) | Semantic Signature Registry + Gold Parquet: re-run classification on ~10,000 unique signatures; push metadata-only updates without regenerating embeddings when document text is unchanged. |
| Ingestion latency on real-time streams | Cache-First Signature Registry: 99%+ of live records resolve via ~1 ms key-value lookup; only unseen taxonomy combinations trigger ML inference. |

**Architectural verdict:** Keep classification strictly upstream of vector stores inside the Silver-to-Gold enrichment layer. Treat vector databases (Chroma, AWS, Azure, GCP) as high-speed retrieval indexes that consume pre-classified, pre-embedded records from the canonical Gold layer.

---

## 4. Architectural mindset

When you have ~2 million regulatory complaint records that are categorical in nature, and the goal is a multi-cloud vector ecosystem (starting with Chroma and expanding to AWS, Azure, and GCP), you are solving three architectural challenges: **Data Modeling & Taxonomy**, **Compute Economics**, and **Multi-Cloud Portability**.

### Vectors are derived views, not systems of record

The biggest mistake teams make when building vector platforms is treating the vector database as their primary data store. Vector stores (whether Chroma, OpenSearch, Azure AI Search, or Vertex AI) are specialized search indexes, not analytical warehouses.

- **The Canonical Gold Layer (Object Storage):** The true source of truth should be an immutable Parquet / Iceberg data lake sitting in object storage (S3, ADLS, or GCS). Every record in this Gold layer holds the cleansed attributes, CFPB Money Topic classifications, and the precomputed vector array.
- **Plug-and-play vector sinks:** Each vector database (Chroma, AWS, Azure, GCP) acts as a downstream materialized view subscribing to that Gold layer. If you ever need to rebuild an index, tune HNSW graph parameters, or onboard a new cloud vendor, you replay from object storage—never from raw CSVs or live ML models.

### Data architecture: solving the structured-to-semantic mismatch

Because post-August 2026 CFPB records often lack free-text narratives, the data is fundamentally **low-cardinality categorical data disguised as text**.

- **The Semantic Signature Pattern (deduplication by design):** Across 2 million rows, the combination of Product + Sub-product + Issue + Sub-issue + Tag + Resolution yields only a few thousand unique permutations. Architecturally, treat these permutations as a **Dimension Table of Semantic Signatures**. Classify and embed the dimension table once, then join it back to the 2-million-row fact table. This shifts ML compute from O(N) (scaling with row volume) to O(U) (scaling only with taxonomy complexity).
- **Hybrid classification strategy (rules + NLI), when cues exist:** Never use an expensive probabilistic model to guess what a deterministic rule already knows with certainty—but also do not pretend Product is 1-to-1 with Money Topics (see §2).
  - **Tier 1 (deterministic taxonomy cues):** Where Product/Sub-product maps cleanly, use versioned rules for precision and auditability.
  - **Tier 2 (cross-cutting / many-to-many overlay):** Reserve ML (Zero-Shot NLI or distilled multi-label classifiers) for latent themes and mismatches. Storing both a primary topic and secondary / multi-label topics gives analysts multi-dimensional slicing without duplicating records.

### Multi-cloud vector portability strategy

- **Decouple embedding generation from cloud vendors:** Never use proprietary cloud embedding endpoints (AWS Titan, Azure-exclusive models, Vertex Gecko) if cross-cloud parity is a requirement. Standardize on an open-weights embedding model (BGE or E5). Because the vector math is identical everywhere, a query embedded in one environment can search an index hosted in another.
- **Lowest-common-denominator metadata schema:** Chroma prefers flat key-value primitives; GCP Vertex AI separates categorical `restricts` from `numeric_restricts`; Azure AI Search and AWS OpenSearch use strongly typed JSON schemas. **Architectural rule:** Enforce a strict, flat metadata contract in the Gold layer—strings, booleans, and integers (e.g., YYYYMMDD integers for dates, explicit `"UNKNOWN"` strings instead of nulls). Avoid nested JSON objects or arrays in metadata when portability matters (use delimited strings or boolean flags for multi-label).
- **Abstract the retrieval layer:** Build a thin Query Broker / Retrieval API in front of vector stores. When an application or LLM agent asks a question, the broker translates a single canonical filter request into the native filter syntax of whichever backend is serving that tenant.

### Productizing the platform (what sits on top)

1. **Analytical aggregation (OLAP path — DuckDB / Snowflake / BigQuery):** Questions like “How many checking complaints occurred in Georgia last quarter?” or “Which bank has the highest timely response rate for Servicemembers?” **Never** route counting, grouping, or trend-line questions through a vector database. Vector search returns Top-K approximate neighbors; it cannot count. Route analytical queries to the Gold Parquet / Iceberg layer via SQL.
2. **Semantic discovery & RAG (vector path):** Questions like “Find complaints similar to unauthorized wire transfers involving military personnel.” Use **metadata pre-filtering first**, then dense vector search to rank semantic relevance within that slice.

---

## 5. What NLI means

**NLI** stands for **Natural Language Inference**. It is a core NLP task where a model determines the logical relationship between two pieces of text: a **Premise** (a known fact) and a **Hypothesis** (a proposed statement).

### The three logical outcomes of NLI

| Outcome | Meaning |
|---|---|
| **Entailment** | The hypothesis logically follows from the premise. |
| **Contradiction** | The hypothesis conflicts with the premise. |
| **Neutral** | The premise does not prove or disprove the hypothesis. |

### How NLI powers zero-shot classification

Architecturally, **Zero-Shot Classification** repurposes an NLI engine. Instead of training from scratch on thousands of labeled Money Topic rows, feed the complaint record as the **Premise** and turn each Money Topic into a **Hypothesis**.

Illustrative premise (structured fields only; fictional values):

> Product: Checking or savings account | Sub-product: Checking account | Issue: Managing an account | Sub-issue: Funds not handled or disbursed as instructed.

| Hypothesis | Typical outcome |
|---|---|
| This consumer complaint is about Bank Accounts & Services. | Entailment (high confidence) |
| This consumer complaint is about Money Transfers. | Entailment (possible secondary) |
| This consumer complaint is about Auto Loans. | Contradiction / low score |

### Why architects use NLI for taxonomy mapping

- **Independent multi-label scoring:** Each Money Topic is tested as its own hypothesis, so one record can entail multiple topics (many-to-many).
- **Logical exclusion:** Unlike keyword matching or pure bi-encoder similarity, NLI models can recognize that “Federal student loan servicing” **contradicts** “Private Student Loans” even when both share “student loan.”
- **Zero training data required (Day-1):** Pre-trained on general logical reasoning (MNLI, FEVER, etc.); topics can be added or renamed without retraining weights (prompt / hypothesis engineering still matters).

---

## 6. Model landscape for multi-label taxonomy mapping

Choosing a classification model for many-to-many regulatory taxonomy mapping comes down to **zero-shot generalization** (no training data) vs **fine-tuned specialization** (high domain precision and low latency).

| Model family | Representative models | How it works | Pros | Cons |
|---|---|---|---|---|
| **1. Zero-Shot NLI Cross-Encoders** | MoritzLaurer/DeBERTa-v3-large-mnli-fever-anli-ling-wanli; MoritzLaurer/bge-m3-zeroshot-v2.0; facebook/bart-large-mnli | Evaluates (complaint text, Money Topic) pairs with full cross-attention; entailment score per topic | Zero training data; native multi-label; catches Fraud inside Checking | Slowest local inference (topic-wise passes); sensitive to hypothesis phrasing |
| **2. Contrastive few-shot (SetFit)** | SetFit on BAAI/bge-base-en-v1.5 or paraphrase-mpnet-base-v2 | Contrastive fine-tune on 8–32 examples per topic + multi-label head | Much faster than NLI; small footprint; learns CFPB boundaries | Needs ~150–300 labeled tricky combinations |
| **3. Bi-Encoder cosine similarity (zero-shot)** | BAAI/bge-base-en-v1.5; intfloat/e5-base-v2; nomic-embed-text-v1.5 | Embed complaint + topic descriptions; dot-product | Reuses retrieval embedder; sub-ms scoring | Lower precision on exclusions (Reverse vs Mortgage; Private vs Federal) |
| **4. Domain-specific financial encoders** | ProsusAI/finbert; yiyanghkust/finbert-tone; AdaptLLM/finance-chat | Pretrained on SEC filings / financial news | Institutional finance vocabulary | Poor fit for consumer complaints / retail protection |
| **5. Frontier / small LLMs (structured JSON)** | Gemini 2.5 Flash / GPT-4o-mini (API); Qwen2.5-7B / Llama-3.1-8B (self-hosted) | Instruction + JSON schema multi-label | Highest reasoning on messy edge cases; can explain labels | Latency/cost if run on millions of raw rows; OK on ~10k unique signatures |
| **6. Classical tabular / sparse ML** | TF-IDF / HashingVectorizer + LightGBM / LogisticRegression (One-Vs-Rest) | Sparse n-grams over categorical tokens | Microsecond latency; explainable | Needs labels; weak on unseen 2026 taxonomy without retrain |

---

## 7. Why specific models were selected

### Why DeBERTa-v3 NLI (MoritzLaurer/…) over FinBERT or BART-large-mnli

- **Disentangled attention:** DeBERTa-v3 separates word content from relative position embeddings, making it better at reading structured key-value strings (`Product: … | Sub-product: … | Issue: …`) than older RoBERTa/BART architectures.
- **Multi-dataset NLI training:** Moritz Laurer’s checkpoints are trained across MNLI, FEVER, ANLI, LingNLI, and WANLI—improving logical exclusion (e.g., recognizing that “Federal student loan” does not entail “Private Student Loans”).
- **Why not FinBERT:** Despite “Finance” in the name, FinBERT was trained on Wall Street financial news for market sentiment, not consumer retail banking disputes.

### Why BGE / E5 over proprietary cloud embeddings (Titan / Gecko / Ada)

Because the roadmap spans Chroma, AWS, Azure, and GCP, locking into AWS Titan or GCP Vertex embeddings creates incompatible vector spaces across clouds. `BAAI/bge-base-en-v1.5` and `intfloat/e5-base-v2` give a single mathematical vector space across every environment.

### Why the “LLM Teacher → Fine-Tuned Encoder (SetFit / DeBERTa)” pattern is the gold standard

- **Day-1:** Zero-Shot NLI bootstraps with zero labeled Money Topic data.
- **Steady-state:** Label ~10,000 deduplicated signatures (or a reviewed subset) with a frontier LLM under a strict rubric, then distill into SetFit (bge-base) or DeBERTa-v3-small multi-label for millisecond local inference with LLM-grade accuracy and no ongoing API dependency for the hot path.

---

## 8. Decision matrix for modeling strategy

- **If you want zero manual labeling and fast time-to-production:** Use Zero-Shot NLI (`DeBERTa-v3-large` or `bge-m3-zeroshot-v2.0`) on deduplicated signatures, paired with `BAAI/bge-base-en-v1.5` for vector store embeddings.
- **If you want maximum precision on CFPB taxonomy edge cases** (Federal vs Private Student Loans; Personal Loans vs Payday Loans): Run batch LLM labeling on ~10k unique signatures once to generate a golden dataset, then train SetFit (`bge-base-en-v1.5`) multi-label for historical backfill and real-time cache misses.

### Practical Day-1 vs Day-N choices (speed vs nuance)

| Model / approach | Architecture | Speed on ~10k unique rows | Extra RAM (approx.) | Best when |
|---|---|---|---|---|
| BAAI/bge-small-en-v1.5 (bi-encoder similarity) | Embedding dot-product | Very fast; can reuse retrieval model | 0 MB extra if already loaded | Fastest pipeline; zero extra models |
| MoritzLaurer/DeBERTa-v3-small-mnli-fever-docnli-ling-2c | Zero-shot NLI | Minutes-scale on CPU | ~550 MB | Strong local zero-shot; Fraud inside Checking |
| MoritzLaurer/bge-m3-zeroshot-v2.0 (or roberta-large-mnli) | Zero-shot NLI | Slower | ~1.5–2.2 GB | Maximum local zero-shot reasoning |
| gpt-4o-mini / gemini-2.5-flash (structured output) | Cloud LLM API | Tens of seconds async on ~10k | 0 MB locally | Richest multi-label tagging / teacher labels |

---

## 9. Three-tier model cascade (when rules are viable)

For structured regulatory text, relying on a single giant model is slow and expensive. Where Product cues are reliable, design the Model Enrichment Engine as a cascade:

| Pipeline stage | Responsibility | Recommended engine | Execution frequency |
|---|---|---|---|
| 1. Primary taxonomy | Assign core Money Topic where Product/Sub-product cues are reliable | Deterministic rule engine (versioned) | Every unique signature (~10k total) |
| 2. Latent risk overlay | Multi-label Fraud & Scams / Money Transfers | DeBERTa-v3-large (NLI) or DeBERTa-v3-small | Unseen signatures / residual |
| 3. Edge-case adjudication | Resolve low-confidence NLI (e.g. 0.45–0.65) | Gemini 2.5 Flash / GPT-4o-mini | Rare |
| 4. Vector embedding | Portable 768-dim search vectors | BAAI/bge-base-en-v1.5 or e5-base-v2 | Unseen signatures |

**Important:** Given the confirmed non–1-to-1 mapping (§2), Stage 1 must not force every row into a wrong bucket; unmapped / ambiguous rows flow to Stage 2 multi-label NLI rather than a false “Bank Accounts & Services” default.

---

## 10. Revised many-to-many classification architecture

Because the mapping is many-to-many rather than 1-to-1, every unique complaint signature is evaluated holistically across all columns combined (Product + Sub-product + Issue + Sub-issue + Tags) against the 12 Money Topics simultaneously:

```text
[Unique Semantic Signature: Product + Sub-product + Issue + Sub-issue + Tags]
                                     │
                                     ▼
            ┌─────────────────────────────────────────────────┐
            │     MULTI-LABEL CLASSIFICATION ENGINE           │
            │  (Evaluates all 12 Money Topics independently)  │
            └────────────────────────┬────────────────────────┘
                                     │
                 ┌───────────────────┴───────────────────┐
                 ▼ (High Confidence)                     ▼ (Ambiguous / Unmapped)
      [Assign 1 to N Money Topics]           [LLM Teacher Adjudication]
      e.g., ["Bank Accounts & Services",      (e.g., Personal Loans / Edge Cases
             "Money Transfers",                routed to Gemini / GPT-4o-mini
             "Fraud & Scams"]                  for structured label assignment)
```

### Updated model strategy for many-to-many

1. **Primary classifier — Multi-Label Zero-Shot NLI Cross-Encoder**
   - Models: `MoritzLaurer/DeBERTa-v3-large-mnli-fever-anli-ling-wanli` or `MoritzLaurer/bge-m3-zeroshot-v2.0`.
   - Scores all 12 Money Topics independently (0.0 to 1.0). Topics above threshold (e.g., >= 0.70) attach as a list. If nothing matches strongly → `Other / Unclassified` rather than a forced wrong bucket.
2. **Edge-case teacher & fine-tuning loop (LLM → distilled classifier)**
   - Step 1: Batch LLM gold labeling on ~10,000 unique signatures with structured multi-label output and rich Money Topic definitions.
   - Step 2: Distill into SetFit (bge-base) or DeBERTa-v3-small with a 12-label sigmoid head for real-time and future batch runs.
3. **Vector metadata representation (multi-cloud safe)**
   - `primary_money_topic` (string — highest-scoring topic)
   - `money_topics_delimited` (e.g., `|Bank Accounts & Services|Money Transfers|`) **or** boolean flags (`is_fraud_scam`, `is_money_transfer`, …) so every cloud vector store can filter multi-label memberships without array-compatibility issues.

---

## 11. Semantic Signature Registry & Cache-First pattern

### Core pattern: Cache-First, Model-Second

Because CFPB complaints consist of finite combinations of Product + Sub-product + Issue + Sub-issue + Tag (+ Resolution), 99%+ of incoming real-time records share the exact same semantic signature as historical records already classified.

Maintain a central, low-latency **Semantic Signature Registry** (Redis, DynamoDB, or equivalent; synced with Silver Parquet catalog):

- **Signature key:** Deterministic hash (e.g., SHA-256) of normalized categorical fields.
- **Registry payload:** Precomputed primary Money Topic(s), secondary topics / flags, fraud risk score, and the 768-dim embedding vector.

### Single packaged inference artifact

Package deterministic mapping cues (if any), NLI threshold logic, and embedding model into a single versioned container or library. Both batch workers and real-time inference APIs must execute that exact package—never duplicate business rules across batch and streaming codebases.

Stamp every classified record with `classifier_version`. On upgrade: hydrate a new version, validate, cut over.

---

## 12. Historical vs real-time classification

### Path A: Historical batch (high throughput / backfills)

1. Batch deduplication: scan raw historical partitions; extract distinct Signature Keys not yet in the Registry.
2. Vectorized inference: Rules (where safe) + Zero-Shot NLI / distilled classifier + Embedding Model process only unseen signatures.
3. Registry hydration & fact join: commit signatures; join to historical facts; materialize Gold; bulk-load vector stores.

### Path B: Real-time streaming / micro-batch (low latency)

1. Event ingestion: Kafka / Kinesis / Event Hubs / Pub/Sub (or scheduled micro-batch).
2. Fast-path cache hit (~1–2 ms): hash fields; query Registry; attach labels + vector without GPU/ML.
3. Slow-path cache miss: Inference Microservice (same artifact); write-back to Registry; forward enriched record.
4. Dual sink: Gold Lakehouse (Iceberg / Delta) + vector upserts (Chroma / AWS / Azure / GCP).

### Consistency safeguards

- Single packaged artifact for batch and streaming.
- Monitor **cache miss rate** as taxonomy drift signal.
- Model version tagging on every enriched record.

---

## 13. Full solution architecture for ~1.97M rows

Optimal pattern: **Batch Lakehouse Fan-Out** separating heavy ML enrichment from vector database ingestion.

```text
[STAGE 1: BRONZE INGESTION & DEDUPLICATION]
  14 Raw CSV Partitions (1.97M rows)
         │
         ├──► Hash & Extract Distinct Semantic Signatures (~10,000 unique combinations)
         │
         ▼
[STAGE 2: SILVER ML ENRICHMENT ENGINE (Executed ONCE on ~10k signatures)]
  ├──► Multi-Label Classification (Zero-Shot NLI Cross-Encoder / LLM-Distilled SetFit)
  │      └─ Outputs: primary_money_topic, secondary_money_topics[], confidence_scores
  └──► Dense Vector Encoding (Cloud-Agnostic Open-Weights Bi-Encoder: BGE-base-768d)
         └─ Outputs: normalized_float32_vector[768]
         │
         ▼
[STAGE 3: GOLD CANONICAL LAKEHOUSE (Partitioned Parquet / Iceberg)]
  Parallel Broadcast Join: 1.97M Fact Rows ◄──► Enriched Signature Catalog (~10k rows)
  Materializes Clean Gold Partitions (ID, Serialized Text, 768d Vector, Flat Metadata)
         │
         ▼
[STAGE 4: MULTI-CLOUD VECTOR FAN-OUT (Asynchronous Sink Adapters)]
  ├──► [Adapter 1] ChromaDB (Open-Source / Self-Hosted)
  ├──► [Adapter 2] AWS OpenSearch Serverless / Bedrock Knowledge Base
  ├──► [Adapter 3] Azure AI Search (HNSW + Filterable Fields)
  └──► [Adapter 4] GCP Vertex AI Vector Search (JSONL Stream + Numeric/Token Restricts)
```

### Stage-by-stage breakdown

**Stage 1 — Bronze-to-Silver deduplication (compute compression)**  
Read partitions in parallel; construct canonical text; generate `signature_id`. Compress ~1.97M rows to ~10k-row dimension catalog. All expensive ML runs on this catalog only.

**Stage 2 — Silver ML enrichment**  
Multi-label classification across 12 Money Topics; store primary topic + multi-label flags; encode with BGE-base 768-d L2-normalized; persist to Semantic Signature Registry (Silver + hot KV).

**Stage 3 — Gold canonical lakehouse**  
Broadcast join facts to enriched catalog; enforce LCD flat schema; replace nulls with explicit strings; YYYYMMDD ints for dates.

**Stage 4 — Multi-cloud sinks**  
Independent idempotent adapters keyed on Complaint ID (see §15).

### Operational sizing note

At 1.97M vectors and 768 dimensions (float32), raw vector storage is ~5.6 GB; in-memory HNSW overhead often needs ~10–12 GB RAM per node. Size cloud nodes for at least ~16 GB index memory, or enable scalar/product quantization where supported to cut memory with controlled recall trade-offs.

---

## 14. Same embeddings across all vector stores

**Always standardize on a single, cloud-agnostic embedding model** (e.g., `BAAI/bge-base-en-v1.5` at 768 dimensions or `intfloat/e5-base-v2` at 768 dimensions) rather than AWS Titan for AWS, Azure OpenAI for Azure, and Vertex Gecko for GCP.

| Reason | Detail |
|---|---|
| Mathematical space consistency | Vector DBs store and search float arrays; they do not care which model created them beyond dimension and distance metric. One model ⇒ identical relevance behavior across clouds. |
| Zero redundant compute | Embed once into Gold Parquet; never pay four times to re-embed 1.97M rows. |
| Cross-cloud query portability | One query-encoding microservice embeds the prompt once and can broadcast that vector to Chroma, AWS, Azure, and GCP. |

---

## 15. Multi-cloud vector store mapping

Because the Gold Parquet layer stores normalized 768-dimensional float arrays and flat typed metadata, migrating across providers requires only thin ingestion adapters:

| Target vector store | Index schema mapping | Bulk / streaming strategy |
|---|---|---|
| **ChromaDB** | `ids` = Complaint ID; `embeddings` = embedding; `documents` = semantic_text; `metadatas` = flat dict | Batched HTTP upsert (e.g. 10k); live micro-batch to avoid write locks |
| **AWS OpenSearch Serverless / Bedrock KB** | `knn_vector` (768, cosinesimil) + keyword/integer fields | `parallel_bulk` from S3; streaming `_bulk` with short refresh |
| **Azure AI Search** | `Collection(Edm.Single)` 768-d HNSW + filterable fields | Buffered upload; MergeOrUpload for near-real-time |
| **GCP Vertex AI Vector Search** | JSONL: id, embedding, restricts, numeric_restricts | GCS JSONL batch update; Streaming UpsertDatapoints |

---

## 16. Real-time / micro-batch extension

Use an **Event-Driven Fast-Path / Slow-Path Router** in front of the Semantic Signature Registry. Principle: **Zero Dual-Pipeline Drift**—real-time uses the same Registry, model artifacts, Gold schema, and sink adapters as historical batch; only the trigger changes (schedule → event bus).

```text
[Real-Time Producers: CFPB API Poller / Webhook / Live Support Ticket]
                                  │
                                  ▼
                [Event Streaming Backbone: Kafka / Kinesis / PubSub]
                                  │
                                  ▼
              ┌───────────────────────────────────────┐
              │   STREAM ENRICHMENT PROCESSOR         │
              └───────────────────┬───────────────────┘
                                  │ (Hash → signature_id)
                                  ▼
              ┌───────────────────────────────────────┐
              │     SEMANTIC SIGNATURE REGISTRY       │
              └───────────────────┬───────────────────┘
                                  │
               ┌──────────────────┴──────────────────┐
               ▼ Cache Hit (~99%, ~1–2 ms)           ▼ Cache Miss (<1%, ~50–150 ms)
     [Attach cached labels & vector]       [ONLINE ML INFERENCE MICROSERVICE]
               │                            (same package as batch; write-back)
               └──────────────────┬──────────────────┘
                                  ▼
              [ENRICHED EVENT TOPIC (Gold Stream)]
                                  │
       ┌──────────────────────────┼──────────────────────────┐
       ▼                          ▼                          ▼
[Gold Lakehouse]          [Chroma / AWS OpenSearch]  [Azure AI / GCP Vertex]
```

### Reliability safeguards

- Idempotent upserts on Complaint ID (duplicates from retries / polling).
- Per-cloud Dead-Letter Queues so one cloud outage never blocks others.
- Unified model packaging (`classifier-embedder:v1.x`) for batch and online.

---

## 17. Master end-to-end system architecture

```text
====================================================================================================
1. INGESTION & EVENT BACKBONE (Unified Entry Point)
====================================================================================================
  [Historical Batch: 14 CSVs / 1.97M Rows]            [Real-Time Producers: CFPB API / Webhooks]
                     │                                                    │
                     ▼                                                    ▼
        (Airflow / Spark Partitioner)                       (Kafka / Kinesis / GCP PubSub)
                     │                                                    │
                     └─────────────────────────┬──────────────────────────┘
                                               ▼
====================================================================================================
2. SEMANTIC SIGNATURE REGISTRY & ENRICHMENT PLANE (Zero Dual-Pipeline Drift)
====================================================================================================
                     [Canonical Normalizer & Deterministic SHA-256 Hasher]
                        (Extracts: Product + Sub-product + Issue + Sub-issue + Tag)
                                               │
                                               ▼
                            ┌─────────────────────────────────────┐
                            │    SEMANTIC SIGNATURE REGISTRY      │
                            │  Hot Tier: Redis / DynamoDB (~1ms)  │
                            │  Cold Tier: Silver Iceberg Catalog  │
                            └──────────────────┬──────────────────┘
                                               │
                      ┌────────────────────────┴────────────────────────┐
                      ▼ Cache Hit                                       ▼ Cache Miss
        [Attach Cached Classifications & Vectors]         [UNIFIED ML INFERENCE SERVICE (Container v1.x)]
                      │                                    ├─ 1. Multi-Label Classifier (DeBERTa-v3 / SetFit)
                      │                                    ├─ 2. Edge-Case Adjudicator (Frontier LLM Fallback)
                      │                                    ├─ 3. Cloud-Portable Embedder (BGE-base-768d)
                      │                                    └─► Write-Back to Hot & Cold Registry
                      └────────────────────────┬────────────────────────┘
                                               ▼
====================================================================================================
3. CANONICAL GOLD LAKEHOUSE (Single Source of Truth)
====================================================================================================
                     ┌───────────────────────────────────────────────────┐
                     │           GOLD APACHE ICEBERG / PARQUET           │
                     │  • Immutable Fact Table (1.97M+ Enriched Rows)    │
                     │  • Lowest-Common-Denominator Flat Metadata Schema │
                     │  • Precomputed 768-dim Normalized Float32 Vectors │
                     └─────────────────────────┬─────────────────────────┘
                                               │
                 ┌─────────────────────────────┼─────────────────────────────┐
                 ▼ (OLAP Analytics Path)       │ (Async Multi-Cloud Fan-Out) │
     [SQL / BI / DuckDB / BigQuery]            │                             │
                                               ▼                             ▼
====================================================================================================
4. MULTI-CLOUD VECTOR INDEXING PLANE (Materialized Search Views)
====================================================================================================
     ┌───────────────────────┬─────────────────────────┬─────────────────────────┐
     ▼                       ▼                         ▼                         ▼
[ChromaDB Cluster]   [AWS OpenSearch /]       [Azure AI Search]        [GCP Vertex AI]
 (OSS Self-Hosted)    [Bedrock KB]             (HNSW + Filterable)      [Vector Search]
     │                       │                         │                         │
     └───────────────────────┴─────────────────────────┴─────────────────────────┘
                                               │
                                               ▼
====================================================================================================
5. CONSUMPTION & HYBRID RETRIEVAL PLANE
====================================================================================================
                     ┌───────────────────────────────────────────────────┐
                     │        UNIFIED RETRIEVAL & QUERY BROKER           │
                     │  • Embeds user query ONCE (BGE-base-768d)         │
                     │  • Translates canonical filters to native syntax  │
                     │  • Routes SQL aggregations vs. Vector RAG search  │
                     └───────────────────────────────────────────────────┘
```

### Layer deep-dives (summary)

**Layer 1 — Unified ingestion & canonical normalization**  
Batch: Airflow Dynamic Task Mapping across partitions; dedupe Complaint ID; standardize nulls and types. Streaming: durable message bus. Both paths build the same canonical string and `signature_id`.

**Layer 2 — Registry & ML enrichment**  
Hot + cold registry; three-stage container: multi-label classifier, optional LLM adjudication for borderline scores, BGE-base-768d encoder.

**Layer 3 — Gold lakehouse**  
System of record; flat LCD metadata; embeddings as first-class columns.

**Layer 4 — Multi-cloud indexing**  
See §15; per-cloud DLQs; HNSW / knn sizing and optional quantization.

**Layer 5 — Retrieval broker**  
Intent routing (SQL vs vector); single-encode query; metadata pre-filter then HNSW.

---

## 18. Gold metadata contract & dual-path consumption

### Lowest-common-denominator Gold fields (illustrative)

- Identifiers & text: `complaint_id` (PK), `semantic_text`, `classifier_version`
- Vector payload: `embedding` (float32[768])
- Filterable primitives: `company`, `state`, `product`, `primary_money_topic`, `is_fraud_scam`, `is_money_transfer`, `fraud_risk_score`, `tags`, `timely_response`, `date_received_int`

### Dual-path consumption

- Expose Gold to an analytical SQL engine for exact aggregations/counts.
- Route semantic similarity and RAG discovery through the Retrieval Broker in front of vector stores.

---

## 19. Governance & Day-2 operations

- **Model & index versioning:** Treat embedding model and HNSW settings as versioned artifacts (e.g., `cfpb_money_topics_bge_v1`). Stand up v2 in parallel, validate against a golden evaluation set, cut over the Retrieval Broker atomically.
- **Idempotency via deterministic IDs:** Always use CFPB Complaint ID as the primary document key across every vector store so backfills upsert rather than duplicate.
- **Background index compaction:** Frequent real-time upserts fragment HNSW graphs; schedule periodic optimization across backends.
- **Taxonomy drift observability:** Track real-time Registry cache-miss rate; spikes signal new CFPB product/issue categories needing audit.
- **Zero-downtime upgrades:** Tag Gold and vector metadata with `model_version`; dual-run then switch pointer.

---

## 20. Illustrative mapping notes (deterministic cues vs overrides)

These cues remain useful as **features / high-precision shortcuts** inside a many-to-many system—not as a claim of global 1-to-1 completeness:

- Reverse mortgage Sub-product → Reverse Mortgages
- Credit card or prepaid card → Prepaid Cards if Sub-product indicates prepaid, else Credit Cards
- Product exact matches listed in §1 for Auto Loans, Bank Accounts & Services, Credit Cards, Credit Reports & Scores, Debt Collection, Money Transfers, Mortgages, Payday Loans, Prepaid Cards, Private Student Loans (with Sub-product refinement for federal vs private)
- Cross-cutting overlays for Fraud & Scams and Money Transfers via NLI / multi-label scores even when Product is Checking or Credit card

**Canonical document serialization for embeddings (compact key–value, no conversational fluff):**

```text
Product: … | Sub-product: … | Issue: … | Sub-issue: … | Tag: … | Resolution: …
```


---

## 21. Deep dive: Data Modeling, Taxonomy, Compute Economics & Multi-Cloud Portability

For a ~2-million-record regulatory complaint ecosystem starting on Chroma and expanding across AWS, Azure, and GCP, the architecture must treat **vector embeddings as derived artifacts** while keeping canonical JSON/Parquet records and taxonomies as the **system of record**.

When you have ~2 million regulatory complaint records that are categorical in nature, and the goal is a multi-cloud vector ecosystem (starting with Chroma and expanding to AWS, Azure, and GCP), you are solving three architectural challenges: **Data Modeling & Taxonomy**, **Compute Economics**, and **Multi-Cloud Portability**.

### 21.1 Data Modeling (The Canonical Payload & Chunking Strategy)

Regulatory complaints (such as CFPB datasets) combine high-cardinality structured fields with noisy, PII-redacted consumer narratives. Do not index raw CSV rows directly.

- **Canonical Storage Separation:** Store the master record in cloud object storage using Apache Parquet (partitioned by `date_received` and product) or Iceberg/Delta Lake. Vector stores hold only the ID, vector, and filterable metadata.
- **Composite Document Representation:** Build a deterministic text template before embedding so semantic search captures categorical context alongside the narrative:
  - **Header Block:** `[Product] > [Sub-product] | [Issue] > [Sub-issue] | [Company] | [State]`
  - **Body Block:** Cleaned consumer narrative (stripping placeholder tokens like `XXXX` that dilute embedding quality).
- **Selective Chunking Rule:**
  - **Short/Medium Narratives (< 512 tokens, ~80% of complaints):** Keep as a single vector (1 record = 1 vector) to preserve global intent and avoid cross-chunk metadata duplication.
  - **Long Narratives (> 512 tokens):** Use recursive semantic chunking (512-token window, 64-token overlap). Attach `parent_complaint_id` and `chunk_index` to every chunk so retrieval can deduplicate back to unique complaint counts.
- **Strict Metadata Schema (Filter-First Design):**
  - **Low-Cardinality Enumerations (Pre-filterable):** `product_id`, `issue_id`, `company_tier`, `timely_response`, `consumer_disputed`, `year_month` (stored as integer `YYYYMM` for fast range scans).
  - **High-Cardinality Fields (Avoid indexing in HNSW):** Keep `company_name` or `zip_code` as stored payload attributes rather than indexed filter fields where possible, preventing metadata graph bloat.

### 21.2 Taxonomy Architecture (Hybrid Hierarchical & Semantic)

Regulatory data has a rigid statutory taxonomy (e.g., Product → Sub-product → Issue → Sub-issue) that often diverges from emerging consumer language. You need a two-tier taxonomy architecture.

- **Tier 1: Canonical Regulatory Spine (Deterministic):**
  - Normalize legacy or drifted category labels into a versioned Master Taxonomy Registry (e.g., `tax_version: v2.4`) using lookup tables.
  - Encode paths as hierarchical path strings (e.g., `credit_reporting/improper_use/credit_inquiry`) to enable prefix-based filtering across all vector engines.
- **Tier 2: Dynamic Micro-Taxonomy (LLM / Embedding-Driven):**
  - Regulatory categories are too broad for root-cause analysis (e.g., thousands of complaints sit under “Incorrect information on your report”).
  - Run periodic unsupervised clustering (HDBSCAN over UMAP-reduced embeddings) on recent complaint windows to discover emerging micro-themes (e.g., “BNPL late fee reporting glitch”).
  - Assign a `semantic_cluster_id` and LLM-generated short label back to the canonical record, turning unstructured drift into queryable taxonomy tags.
- **Hybrid Routing Pattern:** At query time, classify incoming user intent to extract explicit taxonomy filters first (**Pre-filtering**), then execute vector similarity search within that narrowed subspace.

### 21.3 Compute Economics (2M Records at Multi-Cloud Scale)

At 2 million records (roughly 2.4M–2.8M vectors after chunking), naive dense indexing wastes significant RAM and embedding spend.

- **Embedding Model Sizing:**
  - Standardize on a compact, high-throughput embedding model (384 or 768 dimensions, such as `bge-base-en-v1.5` or `text-embedding-3-small` truncated via Matryoshka Representation Learning to 512 dimensions).
  - **Math impact:** 2.5M vectors at 1536-dim (float32) requires ~15.3 GB raw vector memory (~30–40 GB RAM with HNSW graph overhead). At 512-dim with Scalar Quantization (int8 / SQ8), raw footprint drops to ~1.28 GB (~3–4 GB RAM with HNSW), cutting cloud memory costs by ~85% with < 1.5% recall loss.
- **Ingestion & Inference Economics:**
  - **Historical Backfill (2M rows):** Run asynchronously via serverless batch inference (AWS Bedrock Batch, Azure OpenAI Batch, or GCP Vertex Batch) for a 50% API cost discount, or self-host on spot GPU instances (e.g., single L4/T4 GPU processes 2M records in ~2–3 hours).
  - **Incremental Daily Delta:** Regulatory feeds update daily or weekly, not sub-second. Use micro-batch pipelines (every 6–24 hours) rather than always-on streaming clusters.
- **Storage & Index Tiering:**
  - **Hot Tier (Last 12–18 months, ~600K vectors):** Full HNSW in RAM for sub-50ms interactive triage.
  - **Warm/Cold Tier (Historical > 18 months, ~1.9M vectors):** Disk-backed ANN (DiskANN / memory-mapped HNSW) or IVF-PQ on object storage, accepting 150–300ms latency for historical trend queries.

### 21.4 Multi-Cloud Portability (Chroma → AWS, Azure, GCP)

Chroma uses SQLite/DuckDB + local HNSW files, while AWS (OpenSearch / Aurora pgvector), Azure (AI Search), and GCP (Vertex AI Vector Search / AlloyDB) have incompatible filter syntax and index APIs. Achieve portability via decoupled storage and a thin abstraction layer.

| Architectural Layer | Portability Strategy | Target Implementation Across Clouds |
|---|---|---|
| 1. Vector & Metadata Lake (Source of Truth) | Store pre-computed embeddings alongside canonical metadata in Parquet files on S3 / ADLS / GCS. Never re-embed when migrating clouds. | Single Parquet schema (`complaint_id`, `embedding_v1`, `taxonomy_tags`, `metadata_json`) replicated via rclone/object sync. |
| 2. Embedding Determinism | Lock model weights, tokenizer version, and normalization parameters in an Embedding Manifest. | Self-hosted container (ONNX/vLLM) or fixed API model snapshot so Chroma vectors match cloud vectors identically. |
| 3. Query & Filter Abstraction (DAL) | Build an internal Vector Repository Interface that translates a neutral JSON filter AST into native provider syntax. | Translates `{product: "Mortgage", year: {$gte: 2024}}` into Chroma `$where`, OpenSearch `bool`/`filter`, Azure OData, or Vertex restricts. |
| 4. Index Parameter Mapping | Standardize around HNSW + Cosine Similarity + SQ8 across all targets. | Chroma: `hnsw:space=cosine`; AWS: OpenSearch FAISS + SQ; Azure: AI Search HNSW + scalarQuantization; GCP: Vertex Tree-AH or AlloyDB HNSW |
| 5. Blue/Green Index Hydration | Treat cloud vector databases as ephemeral, rebuildable caches. | Spin up target cloud index, bulk-ingest vectors directly from Parquet lake in < 20 minutes, validate recall@10 on a golden query set, and flip traffic. |

### 21.5 Summary Execution Blueprint

1. **Phase 1 (Local/Dev on Chroma):** Build the Parquet canonical store, run batch embedding with a locked 512/768-dim model, and load Chroma with strict metadata schemas.
2. **Phase 2 (Abstraction & Governance):** Implement the neutral Query AST translator and Taxonomy Registry before writing any cloud-specific SDK calls.
3. **Phase 3 (Multi-Cloud Expansion):** Replicate the Parquet vector lake to S3, ADLS, and GCS, using cloud-native bulk loaders to hydrate AWS, Azure, and GCP vector stores without incurring second-pass embedding costs.

---

## 22. What “canonical” means in this solution

In this architecture, **canonical** means the single, authoritative, standardized **source of truth** for your data—as opposed to derived, temporary, or vendor-specific copies.

Because you are working across Chroma, AWS, Azure, and GCP, each vector database will store data in its own proprietary format. Your canonical layer is the master version that stays neutral, clean, and permanent regardless of which cloud or database you use.

### 22.1 Canonical Storage (The Master Record vs. Disposable Indexes)

- **What it is:** The complete, immutable record of each complaint stored in open-source Apache Parquet files in object storage (like S3, GCS, or ADLS), containing the cleaned text, standardized fields, and pre-computed vectors.
- **Why it matters:** Cloud vector databases are expensive to maintain and hard to migrate directly. By keeping a canonical Parquet lake, your vector databases become **disposable caches**. If you switch from Chroma to AWS OpenSearch or Azure AI Search, you simply re-load from your canonical files without re-cleaning or re-embedding 2 million records.

### 22.2 Canonical Taxonomy (Standardized Labels vs. Raw Input)

- **What it is:** A clean, unified set of category names and hierarchy paths (e.g., `credit_reporting/improper_use/credit_inquiry`) governed by a central lookup registry.
- **Why it matters:** Over years of regulatory reporting, category names drift (e.g., “Credit reporting” in 2018 vs. “Credit reporting, credit repair services, or other personal consumer reports” in 2024). Mapping all historical variations into one canonical taxonomy ensures a single filter works accurately across the entire 2-million-record timeline.

### 22.3 Canonical Payload / Representation (Deterministic Input)

- **What it is:** The exact, standardized text template (combining structured headers + cleaned narrative) fed into your embedding model.
- **Why it matters:** Embedding models are sensitive to formatting changes. Defining a canonical text structure guarantees that a record embedded today on Chroma produces the exact same vector space geometry as a record embedded six months from now on GCP.

### 22.4 The Core Architectural Rule

- **Canonical** = Permanent, Cloud-Agnostic, Source of Truth.
- **Non-Canonical (Vector DBs)** = Derived, Cloud-Specific, Rebuildable.

---

## 23. Business data modeling & taxonomy design

To design a robust multi-cloud vector ecosystem for 2 million regulatory complaints, separate your **business data model** from your **vector storage model** and build a multi-layered taxonomy that handles both statutory rules and evolving consumer language.

### 23.1 Business Data Modeling (Three-Layer Architecture)

Define three distinct logical data models so that business analytics, compliance auditing, and semantic search do not interfere with one another.

#### Layer A: The Canonical Domain Model (System of Record)

This is your cloud-agnostic, relational/columnar business model stored in Parquet or Iceberg. It captures the complete lifecycle of a regulatory complaint.

- **Core Fact Entity (`Complaint_Master`):** Holds immutable business facts—`complaint_id` (natural key), `date_received`, `date_sent_to_company`, `submission_channel`, `narrative_raw`, `narrative_cleaned`, and `narrative_hash` (for deduplication and idempotent updates).
- **Entity Resolution Dimension (`Organization_Entity`):** Regulatory data contains noisy company variations (e.g., “JPMORGAN CHASE & CO.” vs. “Chase Bank”). Model a canonical `parent_org_id` mapped to raw aliases so executives can roll up complaints accurately across subsidiaries.
- **Outcome & SLA Dimension (`Resolution_State`):** Tracks `company_response_type`, `timely_response_flag`, and `consumer_disputed_flag` to support compliance risk scoring.
- **Geographic Dimension (`Geo_Hierarchy`):** Maps `zip_code` to state, region, and census_division for regional regulatory reporting.

#### Layer B: The Semantic Projection Model (Embedding Input)

Vector models fail when fed raw relational rows or unformatted text. Define an explicit **Projection Model** that dictates how business entities are serialized into a single semantic unit before embedding.

- **Context Header Injection:** Prepend normalized business attributes (Product, Issue, Organization Tier, Year) to the cleaned narrative so every vector encodes both *what happened* and *which regulatory domain* it belongs to.
- **Parent-Child Chunking Model:** Define a strict two-table relationship for long narratives:
  - **Parent Record:** Holds the full business metadata and summary metrics.
  - **Child Chunk Record:** Holds `chunk_id`, `parent_complaint_id`, `chunk_sequence`, `text_segment`, and the `embedding_vector`. This ensures high-precision search without inflating business counts.

#### Layer C: The Vector Index Payload Model (Portability Contract)

Define a minimal, strict contract for what actually enters Chroma, AWS, Azure, or GCP.

- **Rule of Minimum Viable Metadata:** Only project fields required for pre-filtering (e.g., `canonical_product_code`, `canonical_issue_code`, `parent_org_id`, `year_month_int`, `has_narrative`). Keep heavy text and audit fields in Layer A and hydrate them post-search using `complaint_id`.

### 23.2 Taxonomy Architecture (Three-Tier Hybrid Design)

Regulatory complaints suffer from two problems: **upstream category drift** (regulators rename or split categories every few years) and **downstream granularity gaps** (categories are too broad to pinpoint specific operational bugs). Define a three-tier taxonomy to solve both.

#### Tier 1: Statutory / Regulatory Taxonomy (Deterministic & Hierarchical)

- **Purpose:** Guarantees compliance reporting and exact roll-ups across historical and current data.
- **Design Pattern:** Model this as a strictly versioned Directed Acyclic Graph (DAG) or Materialized Path Hierarchy (e.g., `L1_Product / L2_SubProduct / L3_Issue / L4_SubIssue`).
- **Cross-Walk Governance:** Maintain an explicit Taxonomy Cross-Walk Table that maps retired or renamed historical categories to current canonical IDs. Never overwrite raw regulatory labels; store both `raw_regulatory_label` and `canonical_taxonomy_id`.

#### Tier 2: Operational & Root-Cause Taxonomy (Business-Defined Facets)

- **Purpose:** Translates legal/regulatory terms into internal business ownership (which product team, billing system, or vendor caused the complaint).
- **Design Pattern:** Model this as **orthogonal (multi-facet) tags** rather than a single tree, because one complaint often spans multiple operational causes:
  - **Lifecycle Stage:** Onboarding, Billing/Servicing, Collections, Account Closure.
  - **Failure Mode:** System Outage, Fee Dispute, Miscommunication, Fraud/Unauthorized Access, Delay.
  - **Severity / Regulatory Risk:** Routine, Escalated, Fair Lending / UDAAP Risk.
- **Population Method:** Populated via deterministic business rules combined with zero-shot/few-shot LLM classification pipelines during ingestion.

#### Tier 3: Emergent Semantic Micro-Taxonomy (Bottom-Up Discovery)

- **Purpose:** Catches brand-new product defects or emerging consumer issues that do not yet exist in Tier 1 or Tier 2.
- **Design Pattern:** A dynamic, unsupervised clustering layer (`micro_topic_id`) generated periodically over recent embedding windows (e.g., rolling 30-day cohorts).
- **Lifecycle Promotion:** When a dynamic cluster exceeds a volume or velocity threshold, a governance workflow promotes that cluster into a formal Tier 2 Operational Tag, keeping your taxonomy continuously synchronized with real-world complaint trends.

### 23.3 Summary Architectural Governance Rules

| Architectural Concern | Modeling Decision | Taxonomy Decision |
|---|---|---|
| Historical Drift | Immutable raw fields paired with normalized canonical IDs | Versioned Master Registry with backward-compatible cross-walks |
| Search Precision | Parent-child chunking with injected context headers | Pre-filter on Tier 1/2 codes before running vector similarity |
| Multi-Cloud Sync | Minimal flat metadata payload (enums + integers only) | Materialized path strings (supported natively across all vector DBs) |
| Business Agility | Decouple heavy relational attributes from vector stores | Combine top-down statutory trees with bottom-up semantic clusters |

---

## 24. Tech stack & physical representation by layer

To translate logical data models and three-tier taxonomy into a concrete, multi-cloud solution, each architectural layer must map to a portable, cloud-agnostic technology stack and a clear physical storage representation.

### 24.1 Layer A: The Canonical Domain Model (System of Record)

- **Tech Stack:**
  - **Storage Engine:** Cloud Object Storage (AWS S3, Azure Data Lake Storage Gen2, Google Cloud Storage) backed by Apache Iceberg (or Delta Lake) as the open table format.
  - **Processing & Transformation:** Apache Spark (Databricks / EMR / Dataproc) or DuckDB (for local/single-node batch processing up to ~2M–5M rows).
- **Physical Representation:**
  - Stored as columnar Apache Parquet files compressed with Zstandard (ZSTD).
  - **Partitioning Strategy:** Physically partitioned into directories by `year_month` and `l1_product_code` (e.g., `/canonical/complaints/year_month=202611/product=MORTGAGE/part-0001.parquet`) so incremental updates and backfills only scan relevant partitions.
  - **Dimension Tables** (`Organization_Entity`, `Geo_Hierarchy`): Stored as small, broadcastable Parquet reference tables alongside the fact table.

### 24.2 Layer B: The Taxonomy Registry & Cross-Walk Store

- **Tech Stack:**
  - **Authoritative Store:** PostgreSQL (hosted on AWS RDS, Azure Database for PostgreSQL, or GCP Cloud SQL) for transactional governance, paired with Git (YAML/JSON definitions) for version control.
  - **Runtime Cache:** Exported as versioned Parquet / JSON lookup artifacts to object storage for fast distributed joins during ingestion.
- **Physical Representation:**
  - **Tier 1 (Statutory Hierarchy):** Relational adjacency/materialized-path table (`taxonomy_id`, `version`, `materialized_path`, `is_active`) plus a `taxonomy_crosswalk` table mapping `raw_source_label` → `canonical_taxonomy_id`.
  - **Tier 2 (Operational Facets):** A bridge/junction table (`complaint_facet_map`) storing many-to-many tags (`complaint_id`, `facet_category`, `facet_value`, `confidence_score`).
  - **Tier 3 (Emergent Micro-Topics):** A time-windowed cluster registry (`micro_topic_id`, `window_start`, `window_end`, `centroid_vector`, `llm_summary_label`).

### 24.3 Layer C: The Semantic Projection & Embedding Pipeline

- **Tech Stack:**
  - **Orchestration:** Apache Airflow or Prefect / Dagster (cloud-portable workflow orchestrators).
  - **Embedding Inference:** Self-hosted vLLM or Hugging Face Text Embeddings Inference (TEI) running on containerized GPUs (NVIDIA L4/T4), or cloud batch endpoints (AWS Bedrock Batch, Azure OpenAI Batch, GCP Vertex Batch).
  - **Tier 2/3 Classification:** BERTopic / HDBSCAN + UMAP (running on CPU/GPU batch workers) for clustering, paired with a small distilled LLM (e.g., Llama-3-8B or Mistral-7B) for labeling.
- **Physical Representation:**
  - **The Vector Lake (Intermediate Artifact):** Before touching any vector database, embeddings are written to a dedicated Vector Parquet Lake (`/vector_lake/model=bge_base_v1.5_512d/year_month=202611/`).
  - **Physical Row Layout:** Each row contains `chunk_id` (String), `parent_complaint_id` (String), `embedding` (Fixed-Size List of float32 or pre-quantized int8), and a flattened struct of pre-filterable metadata integers/strings.

### 24.4 Layer D: The Multi-Cloud Vector Serving Layer

- **Tech Stack:**
  - **Local / Edge / Dev:** Chroma (Persistent Client mode).
  - **AWS:** Amazon OpenSearch Service (or Aurora PostgreSQL with pgvector).
  - **Azure:** Azure AI Search.
  - **GCP:** Vertex AI Vector Search (or AlloyDB with pgvector).
  - **Abstraction Gateway:** A containerized FastAPI / gRPC Query Service containing your neutral Query AST Translator.
- **Physical Representation Across Engines:**

| Engine | Physical Storage & Index Representation | Metadata Physical Layout |
|---|---|---|
| Chroma (Local/Initial) | Local directory containing a SQLite3 database (`chroma.sqlite3`) for metadata/collections and memory-mapped binary HNSW segment files (`data_level0.bin`, `header.bin`). | Key-value rows inside SQLite tables (`embedding_metadata`) indexed via B-Trees for `$where` pre-filtering. |
| AWS OpenSearch | Distributed Lucene shards backed by native C++ FAISS HNSW graph files (`.faiss` / `.knnvec`) stored on EBS/NVMe volumes. | Inverted indexes and DocValues column stores inside the same Lucene segment for single-pass hybrid filtering. |
| Azure AI Search | Partitioned search units storing HNSW graph structures alongside Inverted Indexes with optional Scalar Quantization (int8) compressed vector blocks. | Strongly-typed JSON document fields marked `filterable: true` stored in columnar storage per partition. |
| GCP Vertex Vector Search | Distributed ScaNN (Tree-AH) index shards deployed on managed matching-engine nodes, built from JSONL/Avro batch snapshots in GCS. | Namespace `restricts` and numeric `numeric_restricts` embedded directly into the ScaNN shard postings lists. |

### 24.5 End-to-End Physical Data Flow Summary

1. **Raw Landing:** Source CSV/JSON files arrive in Object Storage (`/raw/`).
2. **Canonical Hydration:** Spark/DuckDB cleans narratives, resolves company aliases, joins the PostgreSQL/Git Taxonomy Registry, and writes partitioned Canonical Parquet files (`/canonical/`).
3. **Vector Materialization:** Batch inference workers read `/canonical/`, apply the context header template, generate 512-dim vectors, and write to the Vector Parquet Lake (`/vector_lake/`).
4. **Target Hydration (Push Model):** Cloud-specific bulk loaders read `/vector_lake/` and hydrate Chroma (SQLite + HNSW files) locally, or push bulk batches into OpenSearch, Azure AI Search, or Vertex Vector Search.

---

## 25. Local development parity for the full 2M dataset

To make the multi-cloud architecture seamless for local development at a 2-million-record scale, design a **1-to-1 architectural parity model**. Local developers should run the exact same logical pipelines, storage formats, and query abstractions on a modern laptop (e.g., 16GB–32GB RAM) without spinning up expensive cloud clusters or hitting cloud API limits.

Because 2 million rows of structured text and 512-dim quantized vectors take only ~2.5 GB to 4 GB on disk, a single developer workstation can easily hold and query the entire production dataset locally.

### 25.1 Local vs. Multi-Cloud Parity Stack

| Architectural Layer | Local Development Stack (Laptop / Workstation) | Multi-Cloud Production Stack (AWS / Azure / GCP) | Parity & Portability Mechanism |
|---|---|---|---|
| Object Storage (Data Lake) | Local Filesystem (`./data_lake/`) or MinIO (S3-compatible container) | AWS S3 / Azure ADLS Gen2 / GCP GCS | `fsspec` / S3A URI Abstraction: Code points to `s3://lake/...` or `file:///lake/...` via environment config. |
| Table Format & Compute | DuckDB (Embedded in-process SQL engine over Parquet/Iceberg) | Apache Spark / Trino / Snowflake over Apache Iceberg | SQL & Parquet Standard: DuckDB reads and writes identical Parquet/Iceberg files on a single machine with zero JVM overhead. |
| Taxonomy Registry | SQLite (or containerized PostgreSQL via Docker Compose) + Local Git Repo | Managed PostgreSQL (RDS / Cloud SQL) + Git | Schema Migration Parity: Identical DDL schemas and versioned YAML/JSON taxonomy artifacts exported to Parquet. |
| Workflow Orchestration | Dagster / Prefect (Local dev server) or Taskfile / Make | Dagster Cloud / Managed Airflow / Cloud Composer | Declarative Assets: Pipeline steps are defined as storage-agnostic assets reading/writing Parquet partitions. |
| Embedding & Classification | ONNX Runtime / Ollama / llama.cpp (Apple Silicon Metal / local CPU/GPU) | vLLM / Hugging Face TEI (GPU nodes) or Cloud Batch APIs | Pre-Computed Vector Sync: Devs pull pre-embedded Parquet slices from cloud object storage for the 2M backfill, using local ONNX only for small test deltas. |
| Vector Serving Engine | Chroma (Persistent local mode with HNSW) | AWS OpenSearch / Azure AI Search / GCP Vertex Vector Search | Query AST Translator (DAL): Application code talks only to your internal repository interface, never directly to Chroma or cloud SDKs. |

### 25.2 Physical Representation on a Local Workstation

For a developer working with all 2 million records locally, physical disk layout and memory management are critical so the laptop does not swap or freeze.

**Local Directory & File Layout:**

```text
./local_ecosystem/
├── lake/
│   ├── raw/                  # Raw regulatory CSV/JSON drops (~1.2 GB)
│   ├── canonical/            # Partitioned ZSTD Parquet files (~850 MB total)
│   │   └── year_month=202611/product=MORTGAGE/part-0.parquet
│   ├── taxonomy_registry/    # Versioned Parquet & JSON lookup tables (~5 MB)
│   └── vector_lake/          # Pre-computed 512d SQ8 int8 embeddings (~1.4 GB)
│       └── model=bge_base_512d_sq8/part-0.parquet
├── state/
│   └── taxonomy.db           # Local SQLite/Postgres state for taxonomy governance
└── chroma_db/                # Local Chroma persistence directory (~3.2 GB)
    ├── chroma.sqlite3        # Metadata B-Trees & collection catalog
    └── <collection-uuid>/    # Memory-mapped HNSW binary segments
```

### 25.3 Local Compute & Memory Mechanics (2M Records on 16GB–32GB RAM)

- **Zero-Copy Analytics with DuckDB:** Instead of loading 2 million rows into pandas/RAM, DuckDB streams directly from the local `canonical/*.parquet` files using vectorized execution, running full aggregations and taxonomy joins in < 500 milliseconds using < 500 MB RAM.
- **Pre-Computed Vector Hydration (Avoid Local Re-Embedding):** Embedding 2 million records on a laptop CPU takes hours. In this architecture, the CI/CD or data engineering pipeline publishes the Vector Parquet Lake to shared cloud storage. A local developer runs a single sync command to download the ~1.4 GB `vector_lake` Parquet files and bulk-loads them into local Chroma in ~3 to 5 minutes.
- **Two Local Developer Profiles (Data Tiers):**
  - **Full-Scale Mode (2M records, ~3.5 GB RAM):** Loads the entire `vector_lake` into Chroma with memory-mapped (mmap) HNSW segments for realistic latency, memory profiling, and recall benchmarking.
  - **Fast-Iteration Mode (50K stratified sample, ~150 MB RAM):** A deterministic 2.5% sample partitioned by `l1_product_code` that spins up in < 5 seconds for rapid UI, API, and Query AST testing.

### 25.4 Local Development Environment Topology

To keep local setup simple and cloud-faithful, package the local runtime into two lightweight components:

1. **Docker Compose Infrastructure Profile (`infra-local`):**
   - **MinIO:** Emulates S3 buckets locally so developers can test S3 multipart uploads, IAM-style bucket policies, and Iceberg catalog commits offline.
   - **PostgreSQL:** Runs the exact production DDL for the Tier 1/2/3 Taxonomy Registry and Cross-Walk tables.
2. **Host-Native Execution Profile (`compute-local`):**
   - **DuckDB + Chroma + FastAPI DAL:** Run natively on the host OS (macOS/Linux/Windows) rather than inside Docker containers. Running Chroma and DuckDB natively avoids Docker Desktop filesystem mount bottlenecks (virtiofs / osxfs) when memory-mapping multi-gigabyte HNSW index files and scanning Parquet partitions.

---

## 26. Why not Postgres or MongoDB as the data lake

You can use PostgreSQL (with pgvector) or MongoDB (with Atlas Vector Search) as an **operational store** or hybrid database. However, in a multi-cloud ecosystem (Chroma, AWS, Azure, GCP) processing 2 million regulatory complaints, making either one your primary **Data Lake (System of Record)** introduces major architectural, economic, and portability bottlenecks compared to an Object Storage + Parquet/Iceberg lake.

### 26.1 Local development nuance

When you narrow the question down to **local development**, comparing Postgres (pgvector) and MongoDB against the Parquet + DuckDB + Chroma stack becomes more nuanced. On a single laptop with 2 million records, Postgres and MongoDB are actually quite viable—but they introduce specific architectural trade-offs that affect multi-cloud portability.

### 26.2 Why not Postgres (pgvector) for Local Development?

Postgres is the strongest alternative to the current local setup, because a single container can act as your Taxonomy Registry, Analytical Store, and Vector Database (pgvector). However, it introduces four friction points for local developers:

- **Heavy Bulk-Loading & Index Build Overhead:** Loading 2 million vectors into pgvector and building an HNSW index locally takes 15 to 40 minutes of heavy CPU and disk I/O (Write-Ahead Logging / WAL). By contrast, bulk-loading pre-computed Parquet vectors into Chroma takes 3 to 5 minutes.
- **Storage Bloat on a Laptop:** Postgres stores data in row-oriented 8KB pages with MVCC transaction overhead, TOAST tables for long complaint narratives, and heavy B-Tree/HNSW indexes. A 2M-record dataset that takes ~4.5 GB total in Parquet + Chroma will easily expand to 12 GB–18 GB inside a local Postgres volume.
- **Container Disk I/O Bottlenecks:** Running Postgres with 2M vectors inside Docker Desktop (especially on macOS or Windows) suffers from virtualized filesystem overhead during index builds and vacuuming. DuckDB and Chroma run natively in-process with zero daemon overhead.
- **False Architectural Assumptions (The Biggest Risk):** If developers build against Postgres locally, they inevitably rely on SQL JOINs between vector similarity (`<=>`) and relational taxonomy tables. When you deploy to AWS OpenSearch, Azure AI Search, or GCP Vertex Vector Search, those engines cannot perform relational joins at query time. Parquet + Chroma forces developers to respect the strict flat-metadata pre-filtering contract from day one.

**Where Postgres Does Belong Locally:** Keep local Postgres small (~5 MB) strictly for the Taxonomy Registry & Cross-Walk state, **not** for the 2M complaint vectors.

### 26.3 Why not MongoDB for Local Development?

Even though MongoDB Community Edition supports local Atlas Vector Search via `mongot` containers, using it as a local data lake for 2 million records creates major bottlenecks:

- **Uncompressed BSON Footprint:** MongoDB stores every complaint document as verbose BSON, repeating field names (`"product"`, `"issue"`, `"narrative"`, `"embedding"`) 2 million times. Locally, 2M records with 512-dim float arrays will consume 18 GB–25 GB of disk space, compared to ~2.2 GB in columnar Parquet.
- **Slow Analytical Aggregations:** Regulatory workflows require frequent local slicing (e.g., “Group 2M complaints by Organization, Year, and Tier-1 Issue”). MongoDB’s aggregation pipeline scans documents sequentially and struggles with memory limits (100MB stage caps unless spilling to disk), whereas DuckDB scans columnar Parquet in < 500ms.
- **Multi-Container Memory Tax:** Running local MongoDB + the `mongot` Java search sidecar process requires 6 GB–8 GB of dedicated RAM just to stay idle, leaving little headroom on a 16GB developer laptop.
- **No Multi-Cloud Object Lake Parity:** MongoDB locks your local data inside proprietary WiredTiger storage files. You cannot directly push WiredTiger files to S3, ADLS, or GCS to hydrate cloud vector stores—you would have to export them back out to Parquet/JSONL anyway.

### 26.4 Local Development Comparison Matrix (2M Records)

| Architectural Metric | Parquet + DuckDB + Chroma (Recommended) | Local Postgres (pgvector) | Local MongoDB (mongot) |
|---|---|---|---|
| Total Local Disk Footprint | ~4.5 GB (Compressed Parquet + mmap HNSW) | ~14 GB (Heap + WAL + HNSW + TOAST) | ~22 GB (BSON + WiredTiger + Lucene) |
| Initial 2M Data Hydration | 3–5 mins (Direct Parquet stream) | 15–40 mins (INSERT + HNSW build) | 20–45 mins (BSON import + Lucene index) |
| Idle RAM Overhead | ~0 MB (In-process / on-demand) | ~1.5–3 GB (Shared buffers + daemon) | ~6–8 GB (mongod + JVM mongot) |
| 2M Group-By Analytics | < 0.5 sec (Vectorized columnar scan) | 3–8 sec (Row scan / parallel workers) | 10–30+ sec (Document scan) |
| Multi-Cloud Parity | 100% (Files match S3/ADLS/GCS; filter AST matches Cloud Vector DBs) | Low (Tempts devs to use SQL joins unsupported by cloud vector DBs) | Low (Proprietary BSON/MQL doesn’t map to OpenSearch/Vertex/Azure) |

### 26.5 Summary Architectural Rule for Local Dev

Use **Parquet + DuckDB + Chroma** locally not just because it is lighter on a laptop, but because it enforces the exact same physical and query constraints as your cloud production environment:

1. **Parquet** gives you zero-copy file portability to S3, ADLS, and GCS.
2. **DuckDB** replaces cloud Spark/Snowflake for instant local analytics.
3. **Chroma** enforces flat metadata filtering just like OpenSearch, Azure AI Search, and Vertex Vector Search.

---

## 27. Hybrid local serving: Chroma vs optional pgvector

To give developers seamless local agility without sacrificing cloud portability, design a **Swappable Vector Serving Profile** on top of a single Parquet + DuckDB canonical lake.

In this architecture, the data lake and taxonomy registry never change. Developers simply toggle an environment variable (`VECTOR_BACKEND=chroma` or `VECTOR_BACKEND=pgvector`) to swap the serving adapter behind your Query AST Translator (DAL).

### 27.1 Hybrid Local Architecture Topology

The local environment is split into two distinct zones: **Permanent Lake Storage** (shared by both profiles) and **Pluggable Serving Runtimes** (started on demand).

```text
[Canonical Parquet Lake (./lake/)] + [DuckDB Analytical Engine]
                        │
                        ▼ (Shared Hydration Stream)
         ┌──────────────────────────────┐
         │  Query AST Translator (DAL)  │  <── Application / API
         └──────────────┬───────────────┘
                        │
        ┌───────────────┴───────────────┐
        ▼ (Profile A: Default)          ▼ (Profile B: Optional)
[Chroma Persistent Engine]      [Postgres 17 + pgvector Container]
  • Host-native execution         • Docker Compose profile
  • Sub-5 min hydration           • Tests SQL/Hybrid parity
  • Maps to OpenSearch/Vertex     • Maps to AWS Aurora / GCP AlloyDB
```

### 27.2 Profile A vs. Profile B: Architectural Roles

#### Profile A: The Fast Iteration Profile (`VECTOR_BACKEND=chroma`)

- **When to use:** Daily feature development, UI work, taxonomy rule tuning, and fast local smoke tests.
- **Physical Runtime:** Runs natively on the host OS (no Docker overhead) reading memory-mapped HNSW segments from `./chroma_db/`.
- **Data Scale:**
  - Supports the 50K stratified sample (hydrates in < 5 seconds) for rapid branch switching.
  - Supports the full 2M dataset (~3.2 GB on disk) when testing recall or memory behavior.
- **Cloud Parity Target:** Mirrors dedicated vector engines (AWS OpenSearch, Azure AI Search, GCP Vertex Vector Search) where relational joins are prohibited and all filtering uses flat metadata predicates.

#### Profile B: The Relational-Vector Parity Profile (`VECTOR_BACKEND=pgvector`)

- **When to use:** Integration testing before deploying to AWS Aurora PostgreSQL, Azure Database for PostgreSQL, or GCP AlloyDB, or when testing complex transactional metadata updates.
- **Physical Runtime:** Packaged as an opt-in Docker Compose profile (`--profile pgvector`) so it consumes zero RAM or CPU unless explicitly started.
- **Resource Guardrails (Laptop Protection):**
  - **Volume Persistence:** Store Postgres data in a named Docker volume (`pgdata_2m`) so developers only pay the 15–20 minute HNSW index build cost once, rather than every time containers restart.
  - **Memory Cap:** Explicitly constrain the container to 4 GB RAM (`shared_buffers=1GB`, `maintenance_work_mem=1GB`) so HNSW graph construction never triggers macOS/Windows swap thrashing.
  - **Strict Schema Isolation:** Mirror the exact same flat metadata table structure used in Chroma—forbidding developers from writing ad-hoc JOINs against the Taxonomy Registry inside vector queries, preserving portability to non-SQL cloud targets.

### 27.3 Shared Hydration & Governance Mechanics

To prevent drift between local Chroma, local pgvector, and cloud targets, enforce three architectural rules:

1. **Single Hydration Pipeline (Parquet-to-Target):** Both Chroma and pgvector read directly from the exact same pre-computed `vector_lake/*.parquet` files. Neither engine ever invokes the embedding model directly.
2. **Idempotent Manifest Tracking:** Maintain a lightweight local state file (`hydration_manifest.json`) recording the `taxonomy_version`, `embedding_model_id`, and `parquet_snapshot_hash` currently loaded into each local engine. When a developer pulls updated Parquet files, the startup script automatically detects version skew and refreshes only the stale local index.
3. **Golden Query Verification Suite:** Maintain a curated set of 50–100 benchmark queries (covering edge-case taxonomy filters, organization aliases, and semantic similarity) with expected `complaint_id` top-10 results. Developers run this suite locally against both Chroma and pgvector to verify that the Query AST Translator produces consistent recall across engines before pushing to CI/CD.

### 27.4 Summary Developer Workflow

- **90% of daily work:** Developer runs DuckDB + Host Chroma (zero containers, < 1 GB RAM footprint, instant startup).
- **10% pre-release validation:** Developer spins up the pgvector Docker profile, hydrates from the local Parquet lake, runs the Golden Query Suite to verify relational-vector parity, and tears down the container.

---

## 28. CI/CD promotion & multi-cloud release pipeline

To take the multi-cloud vector ecosystem from a local workstation into automated production across AWS, Azure, and GCP, the CI/CD architecture must treat **code**, **taxonomy definitions**, and **vector artifacts** as **decoupled release pipelines**.

Because re-embedding 2 million records is expensive and slow, separate **fast software/taxonomy releases** from **heavy vector-model releases**.

### 28.1 The Three Decoupled Promotion Tracks

Do not bundle everything into a single monolithic deployment pipeline. Structure CI/CD into three independent tracks that converge at the serving layer:

- **Track 1: Application & Query AST Track (Fast — Minutes)**
  - **What moves:** API services, Query AST Translators (Chroma, OpenSearch, AI Search, Vertex, pgvector), and UI components.
  - **Trigger:** Every pull request / merge to main.
  - **Validation:** Runs the Golden Query Suite locally/in CI against the 50K sample on both Chroma and pgvector containers to verify zero filter-translation regressions.
- **Track 2: Taxonomy & Cross-Walk Track (Medium — 10–15 Minutes)**
  - **What moves:** Versioned Tier 1/2/3 taxonomy definitions (YAML/JSON in Git) and Organization Entity alias tables.
  - **Trigger:** Merge to the taxonomy-registry repository.
  - **Execution:** Updates the authoritative PostgreSQL Registry, runs a lightweight metadata-only transformation on the Canonical Parquet Lake (updating tags without re-computing embeddings), and pushes metadata patches to active vector stores.
- **Track 3: Embedding Model & Full Re-Index Track (Heavy — Hours, Scheduled/Manual)**
  - **What moves:** Embedding model upgrades (e.g., migrating from 512d to 768d) or major chunking template changes.
  - **Trigger:** Explicit release tag (`model-v2.0`).
  - **Execution:** Runs once on a single primary compute cloud (wherever GPU spot/batch rates are lowest) to generate a new Vector Parquet Lake partition, then replicates the resulting Parquet files to the other clouds.

### 28.2 Multi-Cloud Artifact Replication & Hydration Topology

Instead of running three separate embedding pipelines on AWS, Azure, and GCP, adopt a **Hub-and-Spoke Artifact Distribution Model**:

```text
[Git + CI Runner] ──► [Primary Compute Hub (e.g., AWS / GCP Batch)]
                             │  (Generates Canonical & Vector Parquet once)
                             ▼
                  [Primary Object Lake (S3 / GCS)]
                             │
             ┌───────────────┼───────────────┐ (Async Object Replication)
             ▼               ▼               ▼
       [AWS S3 Lake]   [Azure ADLS]    [GCP GCS Lake]
             │               │               │
             ▼               ▼               ▼
      [AWS OpenSearch] [Azure AI Search] [GCP Vertex AI]
      (Blue/Green Hydrate) (Blue/Green)   (Blue/Green)
```

- **Zero Duplicate Compute:** You pay for embedding inference and LLM taxonomy classification once. Cross-cloud object replication (via rclone or cloud-native storage transfer services) moves the ~2.2 GB compressed Parquet lake across AWS, Azure, and GCP in under two minutes for pennies.
- **Immutable Snapshot Tagging:** Every release publishes a `release_manifest.json` alongside the Parquet files containing `schema_version`, `taxonomy_version`, `embedding_model_hash`, and `row_count_checksum`. Cloud bulk loaders refuse to ingest unless the manifest checksum passes validation.

### 28.3 Zero-Downtime Blue/Green Vector Rollouts

Cloud vector databases cannot safely mutate 2 million vectors in place during major taxonomy or model updates without causing query latency spikes or mixed-version search results. Enforce a **Blue/Green Index Alias Pattern** across all targets:

1. **Provision Green Target:** When a new `release_manifest.json` lands in S3, ADLS, or GCS, a cloud-native orchestration job spins up an isolated Green index (a new OpenSearch index, Azure AI Search index, Vertex index endpoint, or Postgres table).
2. **Bulk Hydrate from Parquet:** The cloud bulk loader streams the 2M vectors and flat metadata directly from local cloud object storage into the Green index (~10–20 minutes).
3. **Automated Quality Gates (Smoke & Recall Gate):** Before routing live user traffic, the pipeline executes the Golden Query Suite against the Green index and checks three SLAs:
   - **Completeness Gate:** Document count matches `release_manifest.json` within 0.01%.
   - **Recall Gate:** Recall@10 against the benchmark set meets or exceeds the Blue baseline.
   - **Latency Gate:** P95 query latency under synthetic load stays under target threshold (e.g., < 80ms).
4. **Atomic Traffic Cutover:** Once gates pass, the pipeline flips the routing pointer (OpenSearch Index Alias, Azure AI Search Alias, Vertex Endpoint traffic split, or Postgres View swap) from Blue to Green with zero downtime.
5. **Rollback & Retention Window:** Keep the Blue index warm (or snapshotted) for 24–48 hours for instant rollback, then decommission it to reclaim compute and RAM costs.

### 28.4 End-to-End Environment Promotion Matrix

| Environment | Compute & Storage Stack | Dataset Scale | Promotion Gate |
|---|---|---|---|
| Local Dev | DuckDB + Host Chroma / Optional pgvector | 50K Sample (Fast) / 2M Full (Parity) | Unit tests + Golden Query AST parity check |
| CI / PR Ephemeral | GitHub Actions / GitLab CI + DuckDB + Chroma | 50K Stratified Sample | Automated schema lint, taxonomy DAG cycle check, AST tests |
| Staging (Multi-Cloud) | Single-node OpenSearch / Basic AI Search / Small Vertex | Full 2M Production Mirror | Full Blue/Green hydration dry run + Recall@10 & P95 latency SLA |
| Production (AWS/Azure/GCP) | Multi-AZ HA Clusters with SQ8 Quantization | Full 2M + Daily Micro-Batches | Canary alias switch + automated drift & query latency alerts |


---

## 29. Observability, drift detection & FinOps governance

To complete the multi-cloud vector architecture, the **Observability, Drift Detection, and FinOps Governance** layer must monitor not only traditional infrastructure health (CPU/RAM/latency) but also **semantic search quality**, **taxonomy accuracy**, and **cross-cloud vector economics**.

### 29.1 Semantic & Data Drift Detection (Protecting Search Quality)

Unlike traditional SQL databases, a vector search engine can appear healthy (returning HTTP 200 in 25ms) while silently returning irrelevant results due to data drift or taxonomy erosion. Implement three automated drift monitors:

- **Embedding Distribution Drift (Covariate Shift):**
  - **What to monitor:** Track the cosine distance distribution between incoming daily complaint vectors and your static Tier 1 / Tier 2 category centroids stored in the Taxonomy Registry.
  - **Trigger threshold:** If the rolling 7-day average distance to known centroids increases beyond a statistical threshold (e.g., > 2 standard deviations), flag an **Emergent Topic Alert**—indicating consumers are reporting a novel issue, product bug, or scam pattern not captured by current taxonomy rules.
- **Taxonomy & Entity Coverage Drift:**
  - **What to monitor:** Track the percentage of daily ingested complaints falling into “Other / Uncategorized” buckets or matching “Unresolved Organization Alias” records.
  - **Trigger threshold:** When unmapped company names or low-confidence Tier 2 classifications exceed 5% of daily volume, route those samples to a human-in-the-loop review queue to update the Taxonomy Cross-Walk Table.
- **Retrieval Quality & Zero-Hit Monitoring:**
  - **What to monitor:** Log user query telemetry inside your Query AST Translator (DAL)—tracking empty result rates (when over-restrictive pre-filters return zero vectors) and downstream click/citation engagement.
  - **Auto-relaxation signal:** High zero-hit rates on valid taxonomy filters signal that pre-filter predicates are too narrow, informing automated fallback rules (e.g., broadening from `L4_SubIssue` to `L3_Issue`).

### 29.2 Multi-Cloud Observability Architecture (Unified Telemetry)

Because the serving layer spans Chroma (local), AWS OpenSearch, Azure AI Search, and GCP Vertex Vector Search, avoid fragmented cloud-native dashboards. Centralize telemetry at the Abstraction Gateway (DAL) using open standards.

- **Standardized Telemetry Backbone:** Instrument your FastAPI/gRPC Query Service with OpenTelemetry (OTel), exporting traces, metrics, and structured query logs to a single observability backend (e.g., Grafana Stack / Prometheus / Tempo or Datadog).
- **Four Core Golden Signals for Vector Serving:**
  1. **End-to-End vs. Engine Latency Breakdown:** Separate AST Translation Time, Pre-Filter Execution Time, HNSW Graph Traversal Time, and Canonical Hydration Time so you know whether a bottleneck sits in metadata filtering or vector search.
  2. **Recall@K Shadow Benchmarking:** Run an asynchronous background replay job (1% traffic sample) comparing fast quantized indexes (SQ8 / Tree-AH) against an exact brute-force (Flat) scan on a small audit slice to verify recall stays above 95%.
  3. **Index Freshness Lag (Data SLA):** Track the timestamp delta between `date_received` in the Canonical Parquet Lake and the newest `indexed_at` watermark across AWS, Azure, and GCP, alerting if any cloud falls behind its 24-hour ingestion SLA.
  4. **Segment & Shard Skew:** Monitor memory pressure and document distribution across OpenSearch shards, Azure search units, and Vertex replicas to catch hot partitions (e.g., when a single major bank accounts for 20% of all complaints).

### 29.3 FinOps Governance (Controlling Multi-Cloud Vector Spend)

Vector databases are notoriously expensive because HNSW indexes keep high-dimensional vectors pinned in RAM 24/7. Enforce four FinOps controls across AWS, Azure, and GCP:

- **Compute & Storage Tiering (Hot vs. Cold Partitioning):**
  - **Hot Serving Tier (Rolling 18 Months, ~650K vectors):** Kept in memory-optimized HNSW nodes across active clouds for sub-50ms interactive analyst triage.
  - **Cold Archive Tier (Historical > 18 Months, ~1.35M vectors):** Demoted out of expensive RAM-bound vector clusters into disk-backed ANN (pgvectorscale DiskANN / memory-mapped storage) or queried on-demand via DuckDB/Spark batch scans over the Canonical Parquet Lake, cutting active cloud RAM spend by 60%–70%.
- **Single-Compute Inference Rule (Zero Redundant GPU Spend):**
  - Enforce via CI/CD policy that no cloud target ever runs its own embedding inference. All embedding and LLM classification compute executes once on whichever cloud offers the lowest spot/batch GPU pricing, distributing static Parquet artifacts to the remaining clouds.
- **Blue/Green Orphan Reaper:**
  - Automated scheduled policies verify that old Blue indexes are decommissioned automatically 48 hours after a successful Green cutover, preventing forgotten multi-gigabyte indexes from silently accruing monthly charges.
- **Cross-Cloud Cost Attribution Tagging:**
  - Inject `tenant_id`, `business_unit`, and `query_type` tags at the Query AST Translator layer so cloud compute and query unit costs can be charged back accurately to compliance, legal, or product teams.

### 29.4 End-to-End Architecture Summary

| Architectural Pillar | Core Pattern | Primary Technology / Artifact |
|---|---|---|
| System of Record | Decoupled Columnar Lake | Object Storage (S3/ADLS/GCS/Local) + Parquet / Iceberg |
| Taxonomy Governance | Three-Tier Hybrid Registry | PostgreSQL + Git (Statutory DAG, Operational Facets, Emergent Clusters) |
| Compute Economics | 512d SQ8 Quantization + Hot/Cold Tiering | Batch GPU inference once → Vector Parquet Lake |
| Multi-Cloud & Local Parity | Neutral Query AST Translator + Swappable Profiles | DuckDB + Host Chroma (Default) / pgvector (Relational Parity) |
| Release Engineering | Decoupled Tracks + Blue/Green Alias Swaps | Hub-and-spoke Parquet sync + Golden Query Recall Gates |
| Observability & FinOps | OpenTelemetry Gateway + Centroid Drift Alerts | OTel + Prometheus/Grafana + 48-hour Blue Index Reaper |

---

## 30. Executive ADR-001 & phased 90-day implementation roadmap

Here is both the **Executive Architecture Decision Record (ADR)** and the **Phased 90-Day Implementation Roadmap** to serve as the actionable blueprint for kicking off the multi-cloud regulatory complaint ecosystem.

### 30.1 Part 1: Executive Architecture Decision Record (ADR-001)

- **Title:** Multi-Cloud Vector & Taxonomy Ecosystem for 2M+ Regulatory Complaints
- **Status:** Accepted / Baseline Architecture
- **Context:** We need to ingest, categorize, and semantically search ~2 million categorical regulatory complaints. The system must support lightweight local development on standard laptops, start with Chroma, and scale seamlessly across AWS, Azure, and GCP without vendor lock-in or duplicate compute spend.

#### Key Architectural Decisions

1. **Decoupled Canonical Data Lake (System of Record):** Store raw, cleaned, and enriched records in ZSTD-compressed Apache Parquet / Iceberg on cloud object storage (S3, ADLS, GCS) and local filesystems. Vector databases are treated strictly as ephemeral, rebuildable serving caches, never as primary storage.
2. **Three-Tier Hybrid Taxonomy:** Govern data using a PostgreSQL + Git registry combining: (1) a deterministic statutory hierarchy with backward-compatible cross-walks, (2) orthogonal operational root-cause facets, and (3) unsupervised semantic micro-clusters for emergent issue discovery.
3. **Single-Compute Inference & SQ8 Compression:** Standardize on 512-dimensional embeddings with int8 Scalar Quantization (SQ8). Run embedding and LLM classification once on a single primary compute hub, distributing static Vector Parquet artifacts across all clouds to eliminate duplicate GPU spend and cut RAM footprint by ~85%.
4. **Neutral Query AST Translator (DAL):** Abstract all search and pre-filtering behind an internal Query AST Gateway. Applications never call Chroma, OpenSearch, Azure AI Search, Vertex, or pgvector SDKs directly.
5. **Local-to-Cloud Parity Profiles:** Equip local developers with DuckDB + Host-Native Chroma (default fast iteration) alongside an opt-in pgvector Docker profile (relational parity), hydrated directly from pre-computed Parquet snapshots.
6. **Blue/Green Zero-Downtime Rollouts & Hot/Cold Tiering:** Deploy index updates via automated Blue/Green alias swaps gated by a Golden Query recall benchmark, while keeping only the rolling 18-month active window in RAM-backed HNSW nodes.

#### Trade-Offs Accepted

- **Eventual Consistency over Real-Time Streaming:** Regulatory complaints arrive in daily/weekly batches. Adopting micro-batch Parquet pipelines trades sub-second ingestion for massive cost savings and cross-cloud simplicity.
- **Flat Metadata Contract:** Prohibiting relational joins at vector query time requires denormalizing taxonomy codes into flat metadata payloads during ingestion, ensuring 100% compatibility across non-SQL cloud vector engines.

### 30.2 Part 2: Phased 90-Day Implementation Roadmap

#### Phase 1: Foundation, Canonical Lake & Local Parity (Days 1–30)

**Goal:** Establish the single source of truth, taxonomy governance, and a working local 2M-record developer experience.

- **Weeks 1–2: Canonical Modeling & Taxonomy Registry**
  - Finalize the logical schemas for `Complaint_Master`, `Organization_Entity` aliases, and the flat Vector Payload contract.
  - Stand up the Git + PostgreSQL Taxonomy Registry and build the Tier 1 statutory cross-walk tables to normalize historical category drift.
  - Build the DuckDB ingestion pipeline to transform raw regulatory files into partitioned Canonical Parquet files.
- **Weeks 3–4: Vector Lake Hydration & Local Stack**
  - Run the initial batch embedding pass (512-dim + SQ8) to generate the Vector Parquet Lake (~1.4 GB) and publish both the 2M Full Snapshot and 50K Stratified Sample.
  - Configure the local developer environment (DuckDB + Host Chroma default profile + optional pgvector Docker profile) with idempotent manifest hydration.
  - Curate the initial 50-to-100 Golden Query Benchmark Suite for recall and filter testing.

#### Phase 2: Abstraction Gateway & Operational Taxonomy (Days 31–60)

**Goal:** Decouple application queries from vendor SDKs and activate Tier 2/3 automated classification.

- **Weeks 5–6: Query AST Translator (DAL)**
  - Design and build the containerized FastAPI / gRPC Query Gateway with a neutral JSON filter AST.
  - Implement the first two backend adapters (Chroma and pgvector) and verify identical recall@10 and pre-filtering behavior across both using the Golden Query Suite in CI.
- **Weeks 7–8: Tier 2 & Tier 3 Automated Enrichment**
  - Integrate deterministic rules and distilled LLM classification into the batch pipeline to populate Tier 2 Operational Facets (Lifecycle Stage, Failure Mode, Severity).
  - Deploy rolling 30-day UMAP + HDBSCAN clustering jobs to detect Tier 3 Emergent Micro-Topics and surface novel consumer issues to governance reviewers.

#### Phase 3: Multi-Cloud Expansion, Blue/Green CI/CD & FinOps (Days 61–90)

**Goal:** Replicate the ecosystem across AWS, Azure, and GCP with automated release gates and cost controls.

- **Weeks 9–10: Cloud Adapters & Hub-and-Spoke Sync**
  - Implement the remaining Query AST adapters for AWS OpenSearch, Azure AI Search, and GCP Vertex AI Vector Search.
  - Configure automated cross-cloud object replication (rclone / storage transfer) to sync Canonical and Vector Parquet snapshots from the primary compute hub to S3, ADLS, and GCS.
- **Weeks 11–12: Blue/Green Automation, Observability & FinOps**
  - Build automated Blue/Green bulk hydration pipelines with mandatory document-count, P95 latency, and Golden Query recall gates before atomic alias cutovers.
  - Instrument the Query Gateway with OpenTelemetry (latency breakdown, shadow recall checks, and centroid drift alerts).
  - Enforce Hot/Cold tiering (18-month HNSW retention) and activate the 48-hour Blue Index Orphan Reaper across all three cloud environments.

### 30.3 Day-1 Kickoff Checklist for the Architecture Team

1. Lock the Canonical Parquet Schema (`complaint_id`, `tax_version`, `parent_org_id`, `year_month`, `embedding_sq8`).
2. Freeze the Embedding Model & Template (confirm 512-dim model snapshot and deterministic context header format).
3. Define the Neutral Filter AST Specification before any engineer writes a single line of Chroma or cloud SDK integration code.

---

## 31. Day-1 deliverables: Neutral Query AST & Golden Query Suite

Architectural specification for both Day-1 deliverables: the **Neutral Query AST Specification** (which guarantees multi-cloud portability) and the **Golden Query Benchmark Suite** (which guarantees search quality across engines).

### 31.1 Part 1: Neutral Query AST Specification (Portability Contract)

To ensure an application query produces identical filtering behavior on Chroma, pgvector, AWS OpenSearch, Azure AI Search, and GCP Vertex AI Vector Search, the Abstraction Gateway (DAL) must restrict queries to the **Lowest Common Denominator (LCD) Predicate Set** supported natively as pre-filters across all five engines.

#### Logical Request Envelope

Every search request entering the Query Gateway conforms to four strict sections:

- **Vector Intent Block:** Either a raw `query_text` (embedded on the fly by the gateway using the locked model) or a pre-computed `query_vector` array, paired with `top_k` (capped at 100) and `similarity_metric` (locked to cosine).
- **Deterministic Pre-Filter AST (`filter_tree`):** A recursive boolean expression tree (`AND`, `OR`, `NOT`) evaluating leaf predicates before HNSW graph traversal.
- **Grouping & Deduplication Directive (`collapse_policy`):** Instructs the gateway how to roll up chunk-level hits back to unique parent records (`group_by: parent_complaint_id`, `aggregation: max_score`), preventing a single long narrative with four chunks from dominating top-10 business counts.
- **Hydration Projection (`include_canonical_fields`):** Specifies which heavy fields (e.g., `narrative_raw`, `company_response_text`) the gateway should fetch from the Canonical Parquet/DuckDB/Object store post-search, keeping vector indexes lightweight.

#### Supported Leaf Operators & Cross-Cloud Mapping

Limit AST leaf operators strictly to these six primitives so every target engine executes them as true single-pass pre-filters rather than slow post-filters:

| AST Operator | Supported Data Types | Cross-Cloud Native Translation Target |
|---|---|---|
| EQ / NEQ | String Enum, Integer, Boolean | Chroma `$eq`/`$ne`, OpenSearch `term`, Azure OData `eq`/`ne`, Vertex `allow_list`/`deny_list` |
| IN / NOT_IN | List of String Enums or Integers | Chroma `$in`/`$nin`, OpenSearch `terms`, Azure `search.in()`, Vertex multi-token restricts |
| RANGE (GT, GTE, LT, LTE) | Integer (`year_month` as YYYYMM), Float | Chroma `$gte`/`$lte`, OpenSearch `range`, Azure OData `ge`/`le`, Vertex `numeric_restricts` |
| PREFIX | Materialized Taxonomy Path String | Translated at Gateway into an explicit IN list of descendant codes using the cached Taxonomy Registry (ensures 100% parity on engines lacking native prefix filters like Vertex). |
| AND / OR | Nested Predicate Nodes (Max depth: 3) | Mapped to native boolean combinators (`$and`/`$or`, Lucene `bool`, OData `and`/`or`, Vertex conjunctions). |

**Architectural Guardrail:** Strictly forbid wildcard text matching (`LIKE %...%`), regex filters, or cross-entity joins inside the Query AST. If full-text keyword matching is needed alongside semantic search, model it as an explicit Hybrid BM25 + Vector Rank Fusion (RRF) flag handled by the gateway.

#### Automated Zero-Hit Fallback Policy

When regulatory analysts apply overly narrow filters (e.g., filtering simultaneously by a specific `zip_code`, `parent_org_id`, and `L4_SubIssue`), vector search can return zero results. Define a deterministic **Three-Step Relaxation Cascade** inside the gateway:

1. **Step 1 (Exact Execution):** Execute the AST as submitted. If `result_count >= min_results_threshold` (e.g., 5), return immediately.
2. **Step 2 (Taxonomy Broadening):** Automatically widen the Tier 1 taxonomy filter one level up the hierarchy (`L4_SubIssue` → `L3_Issue`) while preserving organization and date constraints, tagging the response metadata with `relaxation_applied: taxonomy_broadened`.
3. **Step 3 (Geographic Broadening):** If still below threshold, widen `zip_code` to `state` (`relaxation_applied: geo_broadened`). Never silently drop `parent_org_id` or `year_month` without explicit user consent, as doing so violates compliance audit expectations.

### 31.2 Part 2: Golden Query Benchmark Suite Structure

The Golden Query Suite is the automated quality gate that runs locally on developer laptops, in CI pull requests, and during Blue/Green cloud cutovers. Structure it as a version-controlled JSON/YAML artifact containing **100 curated test cases** stratified across five distinct test categories.

#### Benchmark Suite Stratification (100 Test Cases)

- **Category 1: Pure Semantic & Paraphrase Queries (25 Cases)**
  - **What it tests:** Consumer phrasing that uses colloquial language instead of regulatory jargon (e.g., “bank froze my account without warning and bounced my rent check”).
  - **Assertion:** Verifies embedding alignment and ensures expected `L2_SubProduct` and `L3_Issue` complaints appear in Top-10.
- **Category 2: High-Selectivity Metadata Pre-Filtering (25 Cases)**
  - **What it tests:** Complex boolean AST trees combining `year_month` ranges, `parent_org_id` aliases, and Tier 1/Tier 2 taxonomy codes (e.g., “Mortgage servicing complaints against Chase between 202401 and 202506”).
  - **Assertion:** Zero False-Positive Filter Leakage—100% of returned results must strictly satisfy every AST predicate across Chroma, pgvector, OpenSearch, Azure AI Search, and Vertex.
- **Category 3: Long-Narrative Chunk Deduplication (20 Cases)**
  - **What it tests:** Complaints exceeding 512 tokens that were split into multiple child chunks during ingestion.
  - **Assertion:** Verifies that `collapse_policy` correctly deduplicates multiple matching chunks from the same complaint so no `parent_complaint_id` appears twice in Top-10 results.
- **Category 4: Historical Taxonomy Drift & Alias Resolution (15 Cases)**
  - **What it tests:** Queries targeting categories that changed names between 2018 and 2026, or companies that underwent mergers/rebrands.
  - **Assertion:** Confirms that the Taxonomy Cross-Walk and Entity Resolution layers retrieve records seamlessly across both pre-drift and post-drift partitions.
- **Category 5: Edge Cases & Zero-Hit Relaxation (15 Cases)**
  - **What it tests:** Contradictory filters, empty narratives, special characters, and ultra-narrow queries designed to trigger the Three-Step Relaxation Cascade.
  - **Assertion:** Verifies graceful fallback execution, deterministic response flags, and sub-100ms SLA compliance even on worst-case filter combinations.

#### Multi-Engine Pass/Fail Gate Criteria

Every candidate index (local Chroma, local pgvector, or cloud Blue/Green staging) is scored against the exact same **Canonical Ground Truth** (computed via exact brute-force Flat cosine search over the Canonical Parquet Lake):

| Quality Metric | Minimum Promotion Threshold | Architectural Purpose |
|---|---|---|
| Filter Compliance Rate | 100.0% (Zero tolerance) | Guarantees the Query AST Translator has zero syntax or boolean precedence bugs on the target cloud engine. |
| Recall@10 vs. Exact Flat | ≥ 95.0% | Proves that HNSW graph parameters (`ef_search`, `M`) and SQ8 quantization have not degraded semantic accuracy. |
| NDCG@10 (Ranking Stability) | ≥ 0.92 | Ensures the ordering of top-ranked regulatory evidence remains stable across AWS, Azure, and GCP. |
| P95 End-to-End Latency | ≤ 80 ms (Hot Tier) | Validates that index sharding and pre-filter execution meet interactive user SLAs before flipping traffic. |

---

## 32. PII/redaction compliance & multi-tenant access control (RBAC)

To complete the security and compliance posture of the multi-cloud vector ecosystem, protect sensitive consumer narratives and enforce strict data isolation across Chroma, AWS, Azure, and GCP.

Vector embeddings are vulnerable to **embedding inversion attacks** (reconstructing original sensitive text from vectors) and **cross-tenant metadata leakage**. Address **PII/Redaction Compliance** and **Multi-Tenant Access Control (RBAC)** directly inside the canonical pipeline and Query AST Gateway.

### 32.1 PII & Redaction Compliance Architecture

Regulatory complaint datasets already contain partial redactions (such as `XXXX` masks), but unredacted names, account fragments, or sensitive attributes frequently slip into free-text narratives.

- **Two-Stage Redaction Gate (Before Embedding):**
  - **Stage 1 (Deterministic Regex & Checksum Scrubbing):** Strip structured identifiers (SSNs, credit card patterns, routing numbers, email addresses, phone numbers) and normalize inconsistent regulator masks (`XX/XX/XXXX` or `XXXX`) into clean semantic tokens (e.g., `[DATE]`, `[ACCOUNT]`) so embedding quality is not degraded by noise.
  - **Stage 2 (NLP / NER Entity Masking):** Run a lightweight local Named Entity Recognition pipeline (such as Microsoft Presidio or a fine-tuned DeBERTa NER model) during canonical hydration to mask residual person names, street addresses, and medical/financial identifiers before any text reaches an embedding model.
- **Air-Gapped Sensitive Vault (Tokenization Pattern):**
  - Store the unredacted raw intake file in a restricted **Compliance Vault Bucket** (S3/ADLS/GCS with strict IAM and Customer-Managed Encryption Keys / KMS) accessible only to authorized legal auditors.
  - The Canonical Parquet Lake and all Vector Indexes ingest only the scrubbed `narrative_cleaned` text, ensuring PII never enters vector space or local developer laptops.
- **Right-to-Erasure (GDPR / CCPA) Propagation:**
  - Maintain a **Deletion Tombstone Log** in the PostgreSQL Control Plane keyed by `complaint_id`.
  - When a consumer deletion request arrives, immediately add the `complaint_id` to an active Gateway Exclusion Filter (blocking it from search results in milliseconds) while asynchronous batch jobs purge the record from the Canonical Parquet partitions and active Blue/Green vector indexes.

### 32.2 Multi-Tenant Access Control (RBAC & ABAC)

In a regulatory enterprise, different business units (e.g., Mortgage Servicing vs. Credit Cards), external auditors, or regional compliance teams must only query complaints within their authorized scope. Because Chroma, OpenSearch, Azure AI Search, and Vertex have incompatible security models, enforce **Gateway-Driven Mandatory Filter Injection**.

- **Policy Enforcement Point (PEP) at the Query AST Gateway:**
  - Never rely on cloud-specific database roles to enforce row-level security. Authenticate callers at the Query AST Gateway via OIDC / OAuth2 JWT tokens containing claims (`tenant_id`, `allowed_products`, `allowed_orgs`, `clearance_level`).
  - **Mandatory AST Injection:** Before translating a user’s query into Chroma or cloud syntax, the gateway wraps the incoming `filter_tree` inside a non-overridable top-level AND security envelope injecting the caller’s authorized `parent_org_id` and `l1_product_code` list. Even if a user crafts a malicious query, the vector database only searches within their permitted subspace.
- **Tenant Isolation Tiers (Physical vs. Logical):**
  - **Logical Isolation (Default for Internal Business Units):** All 2 million complaints live in a shared index partitioned logically via `tenant_id` and `l1_product_code` pre-filters. This maximizes HNSW memory efficiency and simplifies Blue/Green rollouts.
  - **Physical Isolation (High-Sensitivity / External Audit Tenants):** If strict contractual or regulatory segregation is required for a specific subsidiary or legal investigation, spin up a dedicated Index Namespace / Collection routed dynamically by the gateway based on the caller’s `tenant_id` claim.
- **Local Developer Security Parity:**
  - Local developer datasets (both the 2M Full Snapshot and 50K Sample) are generated exclusively from the post-redaction Canonical Parquet Lake with synthetic or stripped tenant identifiers, ensuring developers never pull unredacted consumer PII onto local workstations.

### 32.3 End-to-End Security & Governance Summary

| Security Domain | Architectural Control | Physical Enforcement Layer |
|---|---|---|
| PII Prevention | Two-stage regex + NER scrubbing before vectorization | Canonical Hydration Pipeline (Pre-Parquet) |
| Raw Audit Access | KMS-encrypted Compliance Vault separated from analytics | Restricted Cloud Object Storage Bucket |
| Row-Level RBAC | Mandatory JWT-claim AND filter injection | Query AST Translator Gateway (PEP) |
| Right-to-Erasure | Instant Tombstone filter + async Blue/Green purge | PostgreSQL Control Plane + Gateway Cache |
| Local Dev Safety | Post-redaction snapshots only; zero raw PII synced | Local `vector_lake` Parquet Artifacts |


---

## 33. Data products & front ends for business and customers

Shifting from infrastructure to **product strategy**, a 2-million-record regulatory complaint ecosystem—enriched with a three-tier taxonomy, entity resolution, and semantic search—becomes a **strategic intelligence engine**. Instead of serving a single search bar, you can package this foundation into distinct **internal business products** and **external customer-facing experiences**.

### 33.1 Internal Business & Compliance Data Products

These products serve executives, compliance officers, legal teams, and product managers by turning raw complaint volume into proactive risk and revenue protection.

#### Early-Warning Systemic Risk Radar (Compliance & Legal)

- **Core Value:** Detects emerging UDAAP (Unfair, Deceptive, or Abusive Acts or Practices) violations, fair-lending anomalies, or systemic billing bugs weeks before regulators launch formal inquiries.
- **How It Uses Your Stack:** Monitors Tier 3 Emergent Micro-Topics and embedding centroid velocity to trigger automated alerts when a specific failure mode spikes across a geographic region or demographic segment.
- **Front-End Experience:** An executive command-center dashboard featuring live spike heatmaps, cluster velocity timelines, and one-click drill-downs into representative consumer narratives.

#### AI Case Resolution Copilot (Customer Operations & Escalations)

- **Core Value:** Cuts resolution time and repeat escalations by arming frontline agents with proven resolutions from historical twin cases.
- **How It Uses Your Stack:** Takes an incoming customer complaint, runs semantic similarity search via the Query AST Gateway filtered by `L2_SubProduct` and `Failure_Mode`, and surfaces past cases that achieved “Closed with non-monetary relief” without consumer dispute.
- **Front-End Experience:** An embedded side-panel widget inside Salesforce or ServiceNow displaying the top 3 precedent cases, root-cause tags, and suggested compliant response templates.

#### Product Friction & Churn Intelligence Hub (Product Management)

- **Core Value:** Quantifies the exact financial and reputational cost of specific product flaws (e.g., mobile app login loops, confusing fee disclosures, or third-party vendor delays).
- **How It Uses Your Stack:** Combines DuckDB columnar aggregations over the Canonical Parquet Lake with Tier 2 Operational Facets to rank product defects by dispute rate and remediation cost.
- **Front-End Experience:** A self-service product analytics portal with side-by-side cohort comparisons (e.g., comparing complaint drivers before and after a major app release or fee policy change).

#### Competitive & Third-Party Vendor Benchmarking Engine (Strategy & Procurement)

- **Core Value:** Benchmarks your organization’s complaint ratios and SLA timeliness against peer institutions, or holds third-party loan servicers and debt collectors accountable.
- **How It Uses Your Stack:** Leverages your Organization Entity Resolution dimension (`parent_org_id`) across public regulatory datasets to normalize subsidiary aliases and compare peer performance fairly.
- **Front-End Experience:** Interactive peer scorecards showing market-share-adjusted complaint rates, response-time percentiles, and topic-level win/loss comparisons.

### 33.2 Customer-Facing & Public Ecosystem Products

Depending on whether you operate as a financial institution, a consumer advocacy platform, or a B2B SaaS provider, you can expose curated slices of this ecosystem directly to end users.

#### Plain-Language Consumer Issue Navigator (Self-Service Support)

- **Core Value:** Helps frustrated customers articulate their issue accurately and route directly to the right resolution workflow without navigating confusing regulatory jargon.
- **How It Uses Your Stack:** Translates everyday user descriptions into your Tier 1 Statutory and Tier 2 Operational taxonomies using semantic matching, automatically pre-filling support tickets or self-service dispute forms.
- **Front-End Experience:** A conversational guided triage assistant on your web and mobile portals that turns messy customer descriptions into structured, instant resolution paths.

#### Transparent Resolution & SLA Estimator (Customer Trust Portal)

- **Core Value:** Reduces anxious repeat calls and regulatory escalations by giving customers realistic expectations on how long their specific issue takes to resolve.
- **How It Uses Your Stack:** Queries historical resolution distributions in the Canonical Parquet Lake for matching `L3_Issue` and `Failure_Mode` cohorts to calculate median turnaround times and common documentation requirements.
- **Front-End Experience:** A status tracker inside the customer portal showing estimated resolution windows, required proof checklists, and proactive status updates.

#### B2B Embedded Regulatory Intelligence API / Data Marketplace (Monetizable Product)

- **Core Value:** Packages your clean, canonical, pre-embedded regulatory dataset and taxonomy cross-walks as a commercial data product for law firms, fintech compliance teams, and risk consultants.
- **How It Uses Your Stack:** Exposes your Query AST Gateway and Versioned Parquet Snapshots via metered APIs and cloud data shares (AWS Data Exchange, Snowflake Marketplace, GCP Analytics Hub) protected by your RBAC tenant layer.
- **Front-End Experience:** A developer portal with interactive query builders, downloadable taxonomy cross-walk schemas, and embedded executive benchmark widgets.

### 33.3 Product-to-Architecture Mapping Summary

| Data Product | Target Persona | Primary Front-End UX | Underlying Engine Capability |
|---|---|---|---|
| Systemic Risk Radar | Chief Compliance Officer / Legal | Alert feed + cluster velocity map | Tier 3 HDBSCAN micro-topics + drift detection |
| Case Resolution Copilot | Escalation & Support Agents | CRM embedded side-panel | Real-time semantic search + `collapse_policy` |
| Product Friction Hub | Product Managers | Release-impact analytics portal | DuckDB Parquet aggregations + Tier 2 facets |
| Peer & Vendor Benchmarks | Strategy / Vendor Risk | Comparative scorecard UI | `Organization_Entity` alias roll-ups |
| Consumer Issue Navigator | Retail Customers | Conversational triage & form filler | Semantic-to-Taxonomy classification |
| B2B Intelligence API | External Fintechs / Legal | Developer portal + Data Share | Multi-tenant Query AST Gateway + Parquet Lake |


---

## 34. Serving all three business models: Multi-Persona Experience Layer

To serve all three business models—**Internal Enterprise Operations**, **Direct Consumer Self-Service**, and **External B2B Monetization**—from a single 2-million-record ecosystem, you need a **Multi-Persona Experience Layer (BFF / Experience APIs)** sitting cleanly above your unified Query AST Gateway and Canonical Parquet Lake.

Instead of building separate data pipelines for each audience, you expose one core intelligence engine through three tailored front-end applications and strict tenant/data boundaries.

### 34.1 The Unified Multi-Product Architecture

```text
[Consumer Web/Mobile App]   [Internal Enterprise Portal]   [External B2B Portal & API]
  • Issue Navigator           • Systemic Risk Radar          • Developer API Playground
  • SLA & Trust Tracker       • Agent Case Copilot           • Cloud Data Shares (Parquet)
           │                           │                              │
           └───────────────────────────┼──────────────────────────────┘
                                       ▼
                ┌─────────────────────────────────────────────┐
                │   Persona-Aware Experience Layer (BFFs)     │
                │  (Rate limits, PII masks, Metering, UI DSL) │
                └──────────────────────┬──────────────────────┘
                                       ▼
                ┌─────────────────────────────────────────────┐
                │   Unified Query AST Gateway & DuckDB Engine │
                └──────────────────────┬──────────────────────┘
                                       ▼
          [Canonical Parquet Lake]  +  [Multi-Cloud Vector Indexes]
```

### 34.2 Tailoring the Front-End Experience Across All Three Models

Each business model consumes the exact same 2M records and three-tier taxonomy, but renders different UI paradigms, latency profiles, and data exposure rules.

#### Model A: Internal Enterprise Front Ends (High Density & Actionable)

- **Unified Command Center (Modular Web App):** Combine the Systemic Risk Radar, Product Friction Hub, and Peer Benchmarking into a single role-based web application using micro-frontends or modular workspaces.
  - **Compliance View:** Live velocity charts of Tier 3 Emergent Micro-Topics, UDAAP risk flags, and geographic heatmaps.
  - **Product View:** Cohort release comparisons powered by sub-second DuckDB queries over the Canonical Parquet Lake.
  - **Strategy View:** Competitor and vendor scorecards built on `parent_org_id` entity roll-ups.
- **Embedded CRM Copilot (Zero-Switch Workflow):** Deliver the Case Resolution Copilot as an embedded iframe/component inside Salesforce, Zendesk, or ServiceNow. Agents never leave their ticketing screen—the widget automatically reads the active ticket text, queries the AST Gateway, and renders top precedent resolutions and dispute-prevention checklists.

#### Model B: Direct Consumer Front Ends (Conversational & Reassuring)

- **Guided Triage & Dispute Assistant (Web / Mobile SDK):** Embed a conversational UI component inside your customer support portal.
  - **Experience:** Instead of forcing customers to pick from 80 regulatory categories, they describe their problem in plain English. The front end calls the semantic classifier to map their text to Tier 1/2 taxonomy codes, auto-populates the right dispute form, and displays a Transparent SLA Card (“Similar billing disputes are typically resolved in 6 business days”).
- **Strict Data Isolation Rule:** Consumer-facing front ends never render raw complaint narratives from other customers. They only surface aggregated statistics (median resolution times, required document checklists) and guided workflow steps.

#### Model C: External B2B & Monetization Front Ends (Self-Service & Metered)

- **B2B Regulatory Intelligence Portal (SaaS Web App):** Built for external law firms, fintech compliance officers, and risk consultants.
  - **Experience:** Features an interactive Visual Query Builder (generating valid Neutral AST queries without writing JSON), downloadable peer benchmark reports, and subscription tier management.
- **Developer Hub & Cloud Data Marketplace:**
  - **API Product:** Interactive OpenAPI/Swagger sandbox with API key provisioning, usage metering, and webhook subscriptions for Tier 3 Emergent Topic Alerts.
  - **Direct Data Product:** Automated publishing of versioned Canonical Parquet and Taxonomy Cross-Walk slices to AWS Data Exchange, Azure Marketplace, and GCP Analytics Hub, allowing enterprise buyers to join your clean regulatory data directly into their own warehouses.

### 34.3 Shared Product Governance Across All Three Models

Running all three business models simultaneously requires four cross-cutting controls in your Experience Layer (BFF):

| Governance Dimension | Consumer Front Ends | Internal Enterprise Front Ends | External B2B Front Ends |
|---|---|---|---|
| Data Exposure Scope | Aggregated SLAs & taxonomy routing only (Zero raw narratives) | Full post-redaction narratives, internal Tier 2 tags, and peer data | Public regulatory corpus only (Proprietary internal tickets excluded) |
| Authentication & Metering | Consumer session token + strict per-user rate limiting | Enterprise SSO (OIDC) + JWT role claims (RBAC) | OAuth2 Client Credentials / API Keys + usage-based billing metering |
| Latency & Caching SLA | < 150ms (Edge-cached taxonomy routes & SLA stats) | < 80ms interactive search; < 500ms DuckDB analytics | < 200ms API SLA with tiered throughput quotas |
| Explainability & Trust | Plain-language next steps & document checklists | Full citation links to precedent `complaint_ids` & confidence scores | Versioned `taxonomy_version` & `release_manifest` lineage metadata |

### 34.4 Recommended Sequencing Strategy (Crawl → Walk → Run)

Even when building for all three models, sequence your front-end rollouts to compound value:

1. **Stage 1 (Internal Operations First):** Launch the Agent Case Copilot and Systemic Risk Radar first. Internal compliance and support teams validate your three-tier taxonomy and surface edge-case retrieval bugs safely behind your firewall.
2. **Stage 2 (External B2B API & Data Share):** Expose the validated Query AST Gateway and Canonical Parquet Lake as a metered B2B API and Cloud Marketplace product—monetizing the exact infrastructure you already built for internal teams.
3. **Stage 3 (Direct Consumer Self-Service):** Deploy the Consumer Issue Navigator once your taxonomy classification accuracy and SLA estimation models are proven in production, reducing incoming support volume at the front door.

---

## 35. Unified monetization, metering, API gateway & multi-persona front-end stack

Complete architectural blueprint covering both the **Unified Monetization, Metering & API Gateway Layer** and the **Multi-Persona Front-End Technology Stack**, completing the full business-to-infrastructure loop.

### 35.1 Part 1: Unified Monetization, Metering & API Gateway Architecture

To safely expose your Query AST Gateway and Canonical Parquet Lake to internal teams, consumers, and paying B2B customers simultaneously, place an **Edge Control Plane** in front of your core services.

#### Edge Gateway & Traffic Segmentation

- **API Gateway Stack:** Kong Gateway, Envoy, or cloud-native edge gateways (AWS API Gateway / Azure APIM / GCP Apigee) sitting in front of your FastAPI/gRPC Query AST Translator.
- **Three Isolated Traffic Lanes:**
  - **Lane 1: Internal Enterprise (`*.internal.domain`):** Authenticated via corporate OIDC / Entra ID / Okta. Zero billing metering; bypasses public rate caps; unlocks proprietary internal complaint tags alongside public regulatory data.
  - **Lane 2: Consumer Self-Service (`api.domain/v1/assist`):** Authenticated via short-lived consumer session JWTs. Protected by strict IP/session burst limits and restricted exclusively to aggregated SLA endpoints and taxonomy routing (blocked at the gateway route table from calling raw vector search endpoints).
  - **Lane 3: External B2B Monetized (`api.domain/v1/intelligence`):** Authenticated via API Keys or OAuth2 Client Credentials issued by the B2B Developer Portal. Enforces tier-based quotas (Free Tier, Pro, Enterprise) and emits asynchronous metering events.

#### Usage Metering & Monetization Engine

Vector and analytical queries have vastly different compute costs. Meter B2B customers using **Value-Based Compute Units (CUs)** rather than naive HTTP request counts:

- **Compute Unit (CU) Weighting Model:**
  - **Taxonomy & Entity Lookup:** 1 CU (served from cached PostgreSQL/Parquet metadata).
  - **Standard Semantic + AST Vector Search (`top_k` <= 20):** 5 CUs (HNSW graph traversal).
  - **Bulk Analytical Aggregation (DuckDB Parquet Scan):** 15 CUs (columnar compute scan).
  - **Webhook / Streaming Alert Subscription (Tier 3 Emergent Micro-Topics):** Flat monthly add-on per monitored product/organization cohort.
- **Asynchronous Metering Pipeline:**
  - The API Gateway publishes lightweight usage events (`tenant_id`, `endpoint`, `cu_cost`, `timestamp`, `status_code`) to an event bus (Kafka / AWS EventBridge / GCP PubSub) with zero impact on query latency.
  - An aggregation engine (Lago, Orb, or Stripe Billing Metering) rolls up hourly CUs, enforces soft/hard quota thresholds, and generates automated monthly invoices.
- **Direct Data Lake Monetization (Zero-API Compute):**
  - For enterprise buyers wanting bulk access to the 2M records, publish automated read-only views of your Canonical Parquet Lake and Taxonomy Cross-Walks directly to AWS Data Exchange, Azure Marketplace, and GCP Analytics Hub. Customers pay cloud-native subscription fees and query the files using their own compute.

### 35.2 Part 2: Multi-Persona Front-End Technology Stack

To avoid maintaining three disconnected UI codebases while delivering distinct experiences for Executives/Analysts, Consumers, and B2B Developers, adopt a **Composable Monorepo Front-End Architecture**.

#### Shared Front-End Foundation

- **Framework & Build System:** Next.js (React) + TypeScript organized inside a Turborepo monorepo.
- **Design System & UI Primitives:** Tailwind CSS + Shadcn/UI with multi-brand theme tokens—allowing internal compliance tools, external B2B portals, and consumer widgets to share accessible components while maintaining distinct visual identities.
- **Type-Safe Query AST Client:** A shared TypeScript SDK generated from your OpenAPI spec that constructs, validates, and serializes Neutral Filter AST trees cleanly across all three front ends.

#### Front-End Stack Mapping by Business Persona

| Persona & Product | Front-End Delivery Form | Specialized UI Libraries & Capabilities | Key UX & Architectural Pattern |
|---|---|---|---|
| Internal Enterprise Portal (Risk Radar, Friction Hub, Peer Benchmarks) | Full-Page Modular Web App (Micro-frontends / Role-based workspaces) | Apache ECharts / Tremor (heatmaps, velocity spikes), TanStack Table (virtualized 100K+ row drill-downs) | Optimistic Filter State: Syncs complex AST filters directly to URL query params so compliance officers can share exact investigation views via link. |
| Internal Agent Copilot (Case Resolution Assistant) | Embeddable Micro-Widget / Web Component | Lightweight React Bundle wrapped as a custom Web Component (`<complaint-copilot>`) for Salesforce LWC / ServiceNow / Zendesk | Context-Aware Auto-Query: Listens to CRM ticket field changes (product, description) and pre-fetches top precedent resolutions before the agent clicks. |
| Direct Consumer Navigator (Guided Triage & SLA Tracker) | Embeddable Conversational SDK (Web & Mobile WebView) | Vercel AI SDK / Streaming UI for guided multi-turn triage cards and dynamic form pre-filling | Zero-Jargon Abstraction: Translates plain-language user inputs into Tier 1/2 taxonomy payloads behind the scenes; renders visual SLA timelines and checklists. |
| External B2B Portal (Intelligence SaaS & Developer Hub) | Self-Service SaaS App + Docs Portal | Mintlify / Docusaurus (interactive API playground), React Flow / Visual Query Builder, Stripe Customer Portal | No-Code-to-AST Builder: Lets non-technical legal analysts build nested AND/OR taxonomy queries visually and export results as CSV, Parquet, or API cURL snippets. |

#### Local-to-Cloud Front-End Parity

Just like the backend data lake, the front-end monorepo connects seamlessly to the local workstation setup:

- Running a single local workspace command starts the Next.js Front-End Apps pointed at your local FastAPI Query AST Gateway (`http://localhost:8000`), backed by DuckDB + Host Chroma (with the 50K fast sample or 2M full dataset).
- Product managers, designers, and engineers can test real-time semantic search, visual AST query builders, and SLA aggregations across 2 million records completely offline before deploying to AWS, Azure, or GCP.

### 35.3 Complete End-to-End Ecosystem Summary

Cohesive, multi-cloud architecture spanning every layer of the stack:

1. **System of Record:** Immutable, PII-scrubbed Canonical Parquet Lake + Three-Tier Hybrid Taxonomy (PostgreSQL + Git).
2. **Compute & Portability:** Single-hub 512d SQ8 embedding generation + Neutral Query AST Gateway abstracting Chroma, pgvector, AWS OpenSearch, Azure AI Search, and GCP Vertex AI.
3. **Developer & Release Agility:** Host-native DuckDB + Chroma local parity + decoupled Blue/Green CI/CD gated by the 100-case Golden Query Suite.
4. **Business & Monetization:** A unified Edge Metering Gateway powering Internal Enterprise Command Centers, Embedded CRM Copilots, Consumer Self-Service Triage, and Metered B2B APIs / Cloud Data Shares.


---

## 36. Master system architecture diagram & team topology / resource sizing

Master System Architecture Blueprint alongside the Team Topology & Resource Sizing Plan to execute the 90-day roadmap.

### 36.1 Part 1: Master System Architecture Diagram Specification

This end-to-end topology unifies the Data Lake, Three-Tier Taxonomy, Multi-Cloud Vector Serving, Security Boundaries, and Three Business Product Front Ends into a single visual architecture.

```text
====================================================================================================
ZONE 1: INGESTION, GOVERNANCE & CANONICAL LAKE (SINGLE COMPUTE HUB - RUN ONCE)
====================================================================================================
[Raw Regulatory Feeds] ──► (1. Two-Stage PII Scrub & NER Gate) ──► [Air-Gapped KMS Compliance Vault]
                                      │
                                      ▼
[Git + Postgres Taxonomy] ──► (2. Canonical Hydration: Spark/DuckDB)
 (Tier 1 DAG, Tier 2 Facets,          │
  Org Aliases, Cross-Walks)           ▼
                      [Canonical Parquet Lake (ZSTD)]  ◄── (3. Tier 3 UMAP+HDBSCAN Drift Loop)
                                      │
                                      ▼
                      (4. Single-Hub Batch Inference: 512d + SQ8 int8)
                                      │
                                      ▼
                      [Vector Parquet Lake + Release Manifest]
                                      │
        ┌─────────────────────────────┼─────────────────────────────┐ (Hub-and-Spoke Sync)
        ▼                             ▼                             ▼
[Local Dev Storage]           [AWS S3 / GCP GCS]            [Azure ADLS Gen2]

====================================================================================================
ZONE 2: MULTI-CLOUD & LOCAL VECTOR SERVING (EPHEMERAL BLUE/GREEN CACHES)
====================================================================================================
[Local Dev Laptop]            [AWS Production]              [Azure / GCP Production]
 • DuckDB (Analytics)          • OpenSearch (HNSW SQ8)       • Azure AI Search / Vertex
 • Host Chroma (Default)       • Aurora pgvector (Opt.)      • Blue/Green Alias Swaps
 • Docker pgvector (Parity)    • Hot (18m) / Cold Tiering    • Golden Query Recall Gates

====================================================================================================
ZONE 3: ABSTRACTION, SECURITY & EDGE METERING CONTROL PLANE
====================================================================================================
                      [Unified Query AST Gateway (FastAPI / gRPC)]
                       • Translates Neutral Filter AST to Native Target Syntax
                       • Injects Mandatory JWT RBAC Filters (PEP) & Tombstone Exclusions
                       • Executes Zero-Hit 3-Step Relaxation Cascade & Chunk Deduplication
                       • Emits OpenTelemetry Traces & Shadow Recall Metrics
                                      │
                                      ▼
                      [Edge API Gateway (Kong / Envoy / Cloud APIM)]
                       • Traffic Lane Isolation & Rate Limiting
                       • Async Compute Unit (CU) Metering -> Kafka -> Lago/Stripe

====================================================================================================
ZONE 4: MULTI-PERSONA PRODUCT FRONT ENDS (NEXT.JS MONOREPO + CLOUD DATA SHARES)
====================================================================================================
┌───────────────────────────┐ ┌───────────────────────────┐ ┌───────────────────────────┐
│  INTERNAL ENTERPRISE      │ │  DIRECT CONSUMER          │ │  EXTERNAL B2B & DATA      │
│  • Systemic Risk Radar    │ │  • Guided Issue Navigator │ │  • Visual AST Query SaaS  │
│  • Product Friction Hub   │ │  • Plain-Language Triage  │ │  • Metered Developer API  │
│  • Embedded CRM Copilot   │ │  • Transparent SLA Card   │ │  • AWS/Azure/GCP Shares   │
│  (Full Post-PII Access)   │ │  (Aggregated SLAs Only)   │ │  (Public Corpus Only)     │
└───────────────────────────┘ └───────────────────────────┘ └───────────────────────────┘
```

#### Architectural Boundary Rules

- **Trust Boundary 1 (Vault vs. Lake):** Raw unredacted data never leaves the KMS Compliance Vault; only scrubbed Parquet records enter Zone 1 downstream.
- **Trust Boundary 2 (Lake vs. Vector DBs):** Vector stores never write back to the Parquet Lake; data flows strictly unidirectional via Blue/Green bulk hydration.
- **Trust Boundary 3 (Gateway vs. Front Ends):** Front-end applications never hold database credentials or execute raw queries; all access passes through the Edge API Gateway and Query AST Policy Enforcement Point.

### 36.2 Part 2: Team Topology & Resource Sizing (90-Day Execution)

To deliver this ecosystem in 90 days without cross-team bottlenecks, organize around four streamlined, domain-aligned pods totaling **6 to 8 FTEs**.

#### Recommended Pod Structure

| Pod Name | Staffing & Roles | Core Architectural Ownership | Key 90-Day Deliverables |
|---|---|---|---|
| Pod 1: Data Platform & Taxonomy | 2 Senior Data Engineers + 0.5 Taxonomist / Domain SME | Canonical Parquet Lake, PII/NER scrubbing gate, Postgres/Git Taxonomy Registry, and Tier 2/3 batch pipelines. | Partitioned Parquet lake, Cross-Walk tables, single-hub 512d SQ8 embedding pipeline, and 2M/50K local snapshots. |
| Pod 2: Search & Multi-Cloud Infra | 2 Backend / Distributed Systems Engineers | Query AST Translator Gateway, native adapters (Chroma, pgvector, OpenSearch, AI Search, Vertex), and Blue/Green CI/CD. | Neutral AST Gateway, Golden Query Benchmark Suite (100 cases), local parity profiles, and multi-cloud alias swaps. |
| Pod 3: Product Experience (Front End) | 2 Full-Stack / Front-End Engineers | Next.js Turborepo monorepo, shared TypeScript AST SDK, Internal Command Center, CRM Copilot, and Consumer Navigator. | Role-based Enterprise Radar UI, embeddable CRM Web Component, and Consumer conversational triage widget. |
| Pod 4: Security, Edge & FinOps | 1 Platform / DevSecOps Engineer (Shared across pods) | Edge API Gateway, OIDC/JWT RBAC injection, CU usage metering pipeline, OpenTelemetry, and Hot/Cold FinOps reapers. | Three-lane API Gateway, Lago/Stripe CU billing integration, OTel drift dashboards, and 48-hour Blue index reaper. |

#### Cloud & Local Infrastructure Sizing Baseline (2M Records)

Because you standardized on 512-dimensional embeddings with int8 Scalar Quantization (SQ8) and 18-month Hot/Cold tiering, your hardware footprint stays remarkably lean across all environments:

- **Local Developer Workstation (Per Engineer):**
  - **Hardware:** Standard 16GB–32GB RAM laptop (Apple Silicon or x86 Linux/Windows).
  - **Footprint:** ~4.5 GB disk for full 2M Parquet + Chroma HNSW; < 1 GB active RAM in default mode.
- **Primary Compute Hub (Batch Inference & Clustering — Run Once):**
  - **Sizing:** Single spot GPU worker (1x NVIDIA L4 or T4, 16–24 GB VRAM) triggered on demand.
  - **Runtime:** Processes 2M historical backfill in ~2.5 hours; daily incremental deltas finish in < 3 minutes.
- **Multi-Cloud Serving Targets (Per Active Cloud — AWS / Azure / GCP):**
  - **Hot Tier (~650K active vectors, rolling 18 months):** ~1.5 GB RAM footprint with SQ8 HNSW. Run a compact 2-node HA cluster (e.g., 2x `r6g.large` OpenSearch nodes, Azure AI Search S1 2 partitions, or small Vertex `e2-standard-4` replicas) to guarantee sub-50ms P95 latency and zero single-point-of-failure.
  - **Cold Tier (~1.35M historical vectors, > 18 months):** Stored in ZSTD Parquet on Object Storage (~1.5 GB total, costing pennies/month) and queried on demand via serverless DuckDB/Athena/BigQuery or disk-backed pgvectorscale.

### 36.3 Final Architectural Sign-Off Summary

Complete, production-grade blueprint covering:

- **Data & Taxonomy:** Canonical Parquet Lake + Three-Tier Hybrid Taxonomy + PII Scrubbing Vault.
- **Portability & DevEx:** Neutral Query AST Gateway + Local DuckDB/Chroma/pgvector parity.
- **Operations & FinOps:** Hub-and-spoke Blue/Green rollouts + OpenTelemetry drift alerts + 18-month Hot/Cold tiering.
- **Business Monetization:** Unified Edge Metering Gateway serving Internal Risk/Copilot tools, Consumer Self-Service, and B2B SaaS/Data Shares.

---

## Document control

| Field | Value |
|---|---|
| Title | Complaints Data Classification & Indexing — Brainstorming |
| Purpose | Preserve architecture / modeling brainstorming for Money Topic classification + multi-cloud vector indexing, plus business/customer data-product strategy |
| Related product docs | Root `README.md` (embeddings exploration, Chroma recipe); M90 for cloud deployment |
| Status | Brainstorming notes (not an approved Superpowers implementation plan) — complete end-to-end blueprint including master architecture diagram and 90-day team/resource sizing |
| Last extended | M35-0001 #300 — §§34–36: Multi-Persona Experience Layer, monetization/FE stack, master architecture diagram + team topology & resource sizing |
