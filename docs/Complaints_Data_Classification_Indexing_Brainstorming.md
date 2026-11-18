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

## Document control

| Field | Value |
|---|---|
| Title | Complaints Data Classification & Indexing — Brainstorming |
| Purpose | Preserve architecture / modeling brainstorming for Money Topic classification + multi-cloud vector indexing |
| Related product docs | Root `README.md` (embeddings exploration, Chroma recipe); M90 for cloud deployment |
| Status | Brainstorming notes (not an approved Superpowers implementation plan) |
