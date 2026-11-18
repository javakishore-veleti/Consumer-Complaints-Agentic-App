# Consumer-Complaints-Agentic-App

## Introduction

**Consumer Complaints Agentic App (CCAA)** is a hands-on platform to bring the public [CFPB Consumer Complaint Database](https://www.consumerfinance.gov/data-research/consumer-complaints/) into your own environment through an **Admin portal**, and to grow toward an **Intellect** layer (search, RAG, agentic analysis) on that data.

Operators do not push millions of rows through a browser. They work in **Managed Information Objects (MIOs)**—for example “all complaints” or “last 3 months”—start the right **registered workflow**, and watch status return through the API. Heavy lifting (download the All zip, derive a date window, later batch ingest into MongoDB) runs **asynchronously** in Apache Airflow. The complaint dataset is **never committed** to this repository.

**Vision:** a reliable local-to-cloud path for complaint data ops first; then intelligence products that reason over the same MongoDB corpus. Milestones already prove Admin → API → Airflow → callback → UI refresh with a pluggable operational store (SQLite by default; Postgres or Mongo via `.env`).

Product intent: [`docs/PRODUCT_FEATURES.md`](docs/PRODUCT_FEATURES.md). Detailed rules: [`Middleware/ConsumerComplaintsHandsOn/DESIGN.md`](Middleware/ConsumerComplaintsHandsOn/DESIGN.md).

### Consumer finance

Consumer finance covers how individuals and households manage, borrow, save, invest, and protect their money.

- **Cash flow & budgeting** — income vs expenses; a budget that funds needs, wants, and savings; an emergency reserve for unexpected costs
- **Credit & debt** — credit scores, APR, principal vs interest, and debt-to-income when borrowing
- **Saving & investing** — compounding, inflation and purchasing power, diversification, tax-advantaged accounts
- **Risk protection & consumer rights** — insurance and deductibles; rules enforced by agencies such as the [CFPB](https://www.consumerfinance.gov/) (for example disputing credit-report errors and clear loan disclosures)

This app operates on **CFPB consumer complaint** records inside that domain.

### Understanding of Consumer Financial Data

Localhost work often uses a **three-month** window from the public [CFPB Consumer Complaint Database](https://www.consumerfinance.gov/data-research/consumer-complaints/) (for example a recent `date_received` range derived from the All export). Records are anonymized complaints the CFPB **sent to companies** for a response.

**Column groups** (CFPB field reference):

| Group | Fields |
|---|---|
| Tracking & dates | `Complaint ID`, `Date received`, `Date sent to company`, `Submitted via` |
| Product & issue | `Product`, `Sub-product`, `Issue`, `Sub-issue` |
| Company & resolution | `Company`, `Company response to consumer`, `Company public response`, `Timely response?` |
| Demographics & location | `State`, `ZIP code`, `Tags` (e.g. Older American, Servicemember) |

**Context for recent windows (from ~August 2026 onward):**

- **No free-text narratives** in the live database for this period — `Consumer complaint narrative` is typically blank; retrieval leans on structured categories plus synthesized text for vectors
- Only complaints sent for a company response are published; complaints referred to other regulators (for example many smaller depository institutions) are excluded
- **Not a statistical sample** of all consumers’ experiences; company complaint volume should be read with company size / market share in mind
- One complaint is not representative of all consumers; the public database generally **updates daily**

**Illustrative record shape** (fictional values — not a real complaint):

```text
Complaint ID: 00000000
Date received / Date sent to company: 2026-09-01
Product / Sub-product: Checking or savings account / Checking account
Issue / Sub-issue: Managing an account / Funds not handled or disbursed as instructed
Company: Example Bank, N.A.
State / ZIP / Tags: XX / 00000 / Servicemember
Submitted via: Web
Company response to consumer: Closed with explanation
Timely response?: Yes
```

After Mongo ingest, `_id` and `Complaint ID` may both hold the same public tracking number; treat **`Complaint ID`** as the stable key for indexing and joins.

### Data Products Ideas

Even without narratives, **semantic search + metadata filters** support products such as:

1. **Compliance / risk copilot (RAG)** — plain-language questions grounded in complaint IDs and facets (product, state, tags, dates)
2. **Issue clustering & trend detection** — similar patterns across companies or regions before they escalate
3. **Peer resolution advisor** — how comparable sub-issues were closed (e.g. explanation vs monetary relief)
4. **Triage / routing assist** — map incoming tickets to historical Product / Issue / Sub-issue; surface priority tags

**Portability:** start with local Chroma (and other local backends already in this repo). The same document-summary + metadata schema can later target open-source stores (e.g. pgvector, Qdrant, Milvus, Weaviate) or cloud vector products on AWS, Azure, and GCP — see milestone **M90** for cloud deployment; this README lists product *ideas*, not those builds.

### Consumer Financial Data Embeddings Exploration

Recent CFPB windows often have **structured categories only** (little or no free-text narrative). Indexing that corpus in a vector store (Chroma first; other open-source and cloud stores later) works best when each row is split into a **document string for embeddings** and **strict metadata for exact filters**. The notes below capture the exploration of that design as a short Q&A.

#### What does “descriptive text summary paired with strict metadata filters” mean?

Split each complaint row into two inputs before upsert:

1. **Document (text summary)** — a string the embedding model turns into one vector for **semantic** similarity (“funds not sent” ≈ “funds not handled or disbursed”).
2. **Metadata** — flat key/value fields stored beside the vector for **exact** constraints (company, state, product, date ranges), like a `WHERE` clause.

Embeddings alone are weak at hard filters (“only this company”, “on or after this date”). Metadata alone cannot match paraphrases. Together they support hybrid queries: filter first (or jointly), then rank by vector similarity inside the reduced set.

#### How would an illustrative row split?

Using the **fictional** shape above (`Complaint ID: 00000000`, Example Bank), not a live export row:

**Document (compact key–value — preferred starting point):**

```text
Product: Checking or savings account - Checking account | Issue: Managing an account - Funds not handled or disbursed as instructed | Tag: Servicemember | Resolution: Closed with explanation
```

**Metadata (exact filters; dates as integers help range queries):**

```json
{
  "complaint_id": "00000000",
  "company": "Example Bank, N.A.",
  "state": "XX",
  "zip_code": "00000",
  "product": "Checking or savings account",
  "sub_product": "Checking account",
  "issue": "Managing an account",
  "sub_issue": "Funds not handled or disbursed as instructed",
  "tags": "Servicemember",
  "company_response": "Closed with explanation",
  "timely_response": true,
  "date_received_int": 20260901
}
```

**At query time (hybrid):** for a question like “checking money-transfer problems in state XX after 2026-08-20 for Example Bank”, apply metadata (`company`, `state`, `date_received_int >= 20260820`) and embed the free-text question against document strings so rows about “funds not handled…” can rank highly even when the user did not type the official Sub-issue wording.

#### Do fixed sentence prefixes like “Complaint regarding a…” help?

Often **no** for this corpus. CFPB Product / Issue / Sub-issue phrases are already rich. Repeating the same English boilerplate on every row:

- Pulls vectors toward a shared “generic complaint” region and **dilutes** differences between issues
- Does **not** grow the stored vector’s byte size (dimension is fixed), but it can raise token/latency cost when embedding

**Three document formats:**

| Approach | Example shape | When |
|---|---|---|
| Pure value concatenation | `Checking or savings account \| Checking account \| Managing an account \| …` | Max signal, min noise; keyword-ish queries |
| Compact key–value | `Product: … \| Issue: … \| Resolution: …` | Best default balance; labels keep roles (outcome vs issue) |
| Full natural sentences | “On … a Servicemember submitted …” | Only if queries are long conversational sentences and the model is tuned for asymmetric sentence retrieval |

**Practical pick for CFPB structured rows:** skip conversational fluff; use **pure concatenation** or **compact key–value**.

#### What do you mean by “asymmetric sentence retrieval”?

**Asymmetric retrieval** (or asymmetric semantic search) happens when the user’s search query and the stored database document are fundamentally different in length, structure, or phrasing—yet need to match based on meaning.

In a standard **symmetric** search, you compare two similar things (for example, matching a tweet to a similar tweet, or a news headline to another news headline). In **asymmetric** search, you are matching a short, natural question against a longer, differently structured record.

**How this applies to CFPB-shaped data**

This project is a textbook example of asymmetric retrieval because the two inputs look completely different:

- **The query** (short, conversational, symptom-based):  
  `Why are banks holding up military members' wire transfers?`
- **The stored document** (structured, categorical, label-based):  
  `Product: Checking or savings account - Checking account | Issue: Managing an account - Funds not handled or disbursed as instructed | Tag: Servicemember | Resolution: Closed with explanation`

Notice that the query and the document share almost zero exact words (“wire transfer” vs “Funds not handled or disbursed as instructed”, “military members” vs “Servicemember”), and one is a question while the other is a structured tag summary.

**Why some embedding models fail at asymmetric search**

- **Symmetric models** (e.g. older `all-MiniLM` setups): Trained on pairs of similar sentences (paraphrases). Because they expect both texts to look alike, they often penalize matches when one text is a conversational question and the other is a structured database record.
- **Asymmetric models** (e.g. E5, BGE, Cohere embed-v3): Trained on question-and-answer datasets (like MS MARCO) where short queries are paired with structured passages. They learn to map a question about a problem to the region in vector space where the description/answer to that problem lives.

**How asymmetric models handle this in practice**

Many asymmetric embedding models ask you to add special instruction prefixes so the model knows which role each text plays:

```python
# When indexing a CFPB-shaped row, mark it as a stored document:
doc_text = "passage: Product: Checking account | Issue: Funds not handled or disbursed as instructed"

# When a user searches, mark their input as a search query:
query_text = "query: bank failed to send my wire transfer"
```

By using `query:` and `passage:` prefixes (used by models like `intfloat/e5`), the model adjusts its math to bridge the gap between how humans ask questions and how the database stores structured facts.

#### How do you choose an embedding model here?

Criteria that matter for Chroma-now / multi-cloud-later:

1. **Portability** — vectors from model A cannot be queried by model B. Prefer open-weights or a cloud-agnostic API so you can embed once (e.g. store vectors with raw JSON in Parquet) and load the **same** vectors into Chroma, AWS, Azure, or GCP without re-embedding.
2. **Asymmetric retrieval** — short structured documents vs conversational user questions; models trained for query↔passage help.
3. **Dimension vs scale** — for a finite CFPB category vocabulary, **~384–1024** dims is usually enough; larger dims cost more storage/latency.
4. **Matryoshka / truncatable dims (MRL)** — some models let you shorten vectors with limited quality loss when cloud bills matter.

| Model family | Type | Dim (typical) | Fit |
|---|---|---|---|
| `BAAI/bge-base-en-v1.5` (or large) | Open weights | 768 / 1024 | Local Chroma, portable, no API cost |
| `intfloat/e5-base-v2` (or multilingual-e5) | Open weights | 768 / 1024 | Strong asymmetric `query:` / `passage:` style |
| `nomic-embed-text-v1.5` | Open / API | 768 (MRL) | Flexible dim sizing |
| OpenAI `text-embedding-3-small` | Commercial API | 1536 (MRL) | Managed quality; still portable if you own the vectors |
| Cohere `embed-english-v3.0` | Commercial API | 1024 | Explicit document vs query input types |

Chroma’s common local default (`all-MiniLM-L6-v2`, 384-d) is fine for **prototyping**; for sharper finance nuance, compare against BGE/E5 or a small commercial model on a golden set before a full re-index.

#### How to Validate Your Choice in 15 Minutes

Before indexing your full multi-month dataset, run a quick benchmark on 50–100 representative rows from your download:

1. **Create a "Golden Test Set" of 10–15 Queries:** Write realistic questions a user might ask, ranging from exact terms ("checking account funds not disbursed") to indirect symptoms ("bank lost my transfer" or "military member charged unfair overdraft fee").
2. **Test 2 Candidate Models Side-by-Side:** Index those 100 rows into two temporary Chroma collections—one using a local open-source model (`BAAI/bge-base-en-v1.5`) and one using an API model (`text-embedding-3-small`).
3. **Check Top-3 Recall (Precision@3):** Verify whether the right Sub-issue and Product rows land in the top 3 results without relying on metadata filters yet.
4. **Inspect Score Separation:** Check that relevant complaints score noticeably higher (e.g., cosine similarity > 0.75) than unrelated complaints (e.g., mortgage or student loan rows scoring < 0.45). If all scores cluster tightly together (e.g., between 0.68 and 0.74), your text template has too much repeated boilerplate or the model is too generic.

Localhost CCAA today still has an MVP **hash** embedder for CI; professional indexing should swap to a real model under a later story while keeping this document/metadata contract stable.

#### How should we index in Chroma?

##### What to put in Chroma (per complaint)

| Chroma field | Source | Rule |
|---|---|---|
| `ids` | `Complaint ID` | Stable public key (ignore Mongo `_id` as the vector id) |
| `documents` | Compact key–value summary | No “Complaint regarding a…” fluff |
| `embeddings` | Real model (not hash) for prod | Same model at query time |
| `metadatas` | Exact facets | For `where` filters / date ranges |

**Document (index):**

```text
Product: {Product} - {Sub-product} | Issue: {Issue} - {Sub-issue} | Tag: {Tags} | Resolution: {Company response to consumer}
```

Omit blank parts. Do **not** put long `Company public response` boilerplate in the document.

**Metadata (filter):**  
`complaint_id`, `company`, `state`, `zip_code`, `product`, `sub_product`, `issue`, `sub_issue`, `tags`, `submitted_via`, `company_response`, `timely_response` (bool), `date_received_int` / `date_sent_int` (`YYYYMMDD` int).

##### How to index (engine settings)

1. **Collection:** new name (e.g. `complaints_v2`) — don’t reuse the hash/dim-32 `complaints` collection.
2. **Index:** Chroma **HNSW**, space **`cosine`** (~2M rows, daily upserts).
3. **Embedder:** open local model with asymmetric support — prefer `intfloat/e5-base-v2` or `BAAI/bge-base-en-v1.5`.
   - If E5: index as `passage: {document}`; query as `query: {user text}`.
4. **Upsert by UUID path** (Chroma 0.5): resolve collection id from create/get, then upsert (already fixed in M23).
5. **Batch:** ~100–500; full re-index OK for 3m cutover; later = upsert new/changed `Complaint ID`s.
6. **CI:** keep **hash** embeddings only in unit tests; Airflow uses the real model.

##### How to query (hybrid)

```text
where: company / state / product / tags / date_received_int >= …
+ query_texts: conversational question (with query: prefix if E5)
```

Semantic match finds paraphrase (“wire held up” ↔ “funds not handled…”); metadata enforces bank/state/date.

##### What not to do

| Anti-pattern | Why not |
|---|---|
| Hash embeddings for real search | Hash vectors are not semantic; paraphrases and related issues will not cluster, so Intellect/RAG quality is meaningless. |
| Full English sentence templates on every row | Shared boilerplate (“Complaint regarding a…”) pulls all vectors toward the same region and dilutes issue-level similarity. |
| Embed-only with no metadata | Embeddings are weak at exact company/state/date constraints; without `where` filters you cannot do reliable hybrid triage queries. |
| IVF / Flat as primary at ~2M | Flat is O(n) and too slow; static IVF clusters drift as CFPB topics arrive daily — HNSW fits upsert-heavy complaint corpora better as the default. |
| Different embed models for index vs query | Vectors from different models live in incompatible spaces; queries will not match indexed documents. |
| Claiming trends are statistically representative (CFPB caveats) | The public database is not a statistical sample of all consumers; volumes need company size/market-share context and must not be sold as market proof. |

##### 1,970,702 rows in 3 months of data

With **1,970,702** rows (nearly 2 million records), the dataset crosses the threshold where brute-force embedding and naive vector indexing become slow, expensive, and redundant.

Because the records contain structured categorical fields (`Product`, `Sub-product`, `Issue`, `Sub-issue`, `Company response`, `Tags`) rather than unique free-text narratives, almost all 1.97 million rows are combinations of a few thousand unique text strings.

**1. The game-changing optimization: deduplicate before embedding**

Instead of running the embedding model 1,970,702 times, extract the unique `text_summary` combinations first.

- **Massive compute savings:** Across 1.97 million CFPB rows, there are typically only **2,000 to 15,000** unique combinations of Product + Sub-product + Issue + Sub-issue + Tags + Company response.
- **99%+ reduction in embedding work:** Run the embedding model once on those ~10,000 unique strings (under ~30 seconds on a laptop CPU, or under about $0.02 via API), store them in a lookup dictionary (`text_summary` → vector), and map the precomputed vectors back to all 1,970,702 rows.
- **Cloud migration ready:** Save the resulting `complaint_id`, metadata, and embedding columns to Apache Parquet. When loading into AWS OpenSearch, Azure AI Search, or GCP Vertex AI later, upload the precomputed vectors directly without paying to re-embed 2 million rows.

**2. Storage & hardware sizing for 1.97M vectors**

At nearly 2 million rows, vector dimensionality directly dictates RAM requirements and cloud bills:

| Embedding dimension | Raw vector size (Float32) | Estimated RAM with HNSW index | Practical fit |
|---|---|---|---|
| 384 dims (e.g. `bge-small-en-v1.5`) | ~2.8 GB | ~4.5 – 6 GB | Fits comfortably on a standard 16 GB laptop; keeps cloud vector hosting cheaper. |
| 768 dims (e.g. `bge-base-en-v1.5` / `e5-base-v2`) | ~5.6 GB | ~9 – 12 GB | Strong accuracy/memory balance; runs well on a 16–32 GB machine or mid-tier cloud node. |
| 1,536 dims (e.g. `text-embedding-3-small`) | ~11.3 GB | ~18 – 24 GB | High memory footprint; needs a 32 GB+ machine locally and noticeably higher cloud costs. |

**Recommendation:** Prefer a **384- or 768-dimension** model such as `BAAI/bge-base-en-v1.5` or `intfloat/e5-base-v2`. Because the text strings are short categorical combinations, 768 dimensions captures full semantic nuance without bloating RAM.

**3. Batch ingestion best practices for Chroma at 2M scale**

Chroma handles 2 million records cleanly on a single machine if three rules are followed during ingestion:

- **Insert in batches of 5,000 to 10,000:** Never call `collection.upsert()` one row at a time or pass all 1.97 million rows in a single call (which can hit SQLite/gRPC payload limits). Loop through the frame in chunks of 5,000.
- **Pass precomputed `embeddings=` directly:** When calling `collection.add(ids=..., embeddings=..., documents=..., metadatas=...)`, pass the mapped vectors explicitly so Chroma bypasses its internal embedding function during the bulk load.
- **Index only high-cardinality metadata you filter on:** Keep metadata lean (`company`, `state`, `product`, `tags`, `timely_response`, `date_received_int`). Avoid stuffing long, unused strings (like the full boilerplate `Company public response` sentence) into every metadata dictionary across 2 million rows, as it bloats SQLite disk and memory usage.

**Example deduplication & mapping pattern (Python):**

```python
import pandas as pd

df = pd.read_csv("complaints.csv", dtype=str).fillna("")

# 1. Build clean, compact text summary
df["text_summary"] = (
    "passage: Product: "
    + df["Product"]
    + " - "
    + df["Sub-product"]
    + " | Issue: "
    + df["Issue"]
    + " - "
    + df["Sub-issue"]
    + " | Resolution: "
    + df["Company response to consumer"]
)

# 2. Embed ONLY unique text summaries (~10k rows instead of 1.97M)
unique_texts = df["text_summary"].unique().tolist()
# unique_vectors = model.encode(unique_texts, normalize_embeddings=True)
# vector_map = dict(zip(unique_texts, unique_vectors.tolist()))

# 3. Map precomputed vectors back to all 1,970,702 rows
# df["embedding"] = df["text_summary"].map(vector_map)
```

##### Optimal setup for an M2 MacBook Air (16 GB RAM)

With **16 GB of RAM** and **1,970,702** rows, memory management is critical—if you use a 768- or 1,536-dimension model, Chroma’s HNSW index plus macOS overhead will push the system into heavy swap.

- **Embedding model (`BAAI/bge-small-en-v1.5` — 384 dimensions):** A 384-dimension index for 1.97 million rows takes roughly **4.5 to 5.5 GB** of RAM, leaving headroom for macOS and Python. Because the M2 chip supports Apple Metal (`mps`), embedding the unique text combinations finishes in just a few seconds.
- **Streaming / chunked ingestion:** Never load all 1.97 million mapped vectors into a single Python list at once. Instead, embed the ~10,000 unique strings first, then stream the CSV/JSON file in chunks of **10,000** rows straight into Chroma and Parquet.

**Memory-safe pipeline script (M2 + 16 GB RAM)**

First, install the required libraries:

```bash
pip install chromadb sentence-transformers pandas pyarrow tqdm
```

Next, run this script to embed unique strings on the M2 GPU (`mps`), save a portable Parquet backup for AWS/Azure/GCP, and load Chroma without exceeding the 16 GB memory limit:

```python
import gc
import chromadb
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

FILE_PATH = "complaints.csv"  # Update with your downloaded filename
CHROMA_PATH = "./cfpb_chroma_384"
PARQUET_PATH = "./cfpb_portable_vectors.parquet"
BATCH_SIZE = 10000

# 1. Load 384-dim model onto Apple M2 GPU (MPS)
model = SentenceTransformer("BAAI/bge-small-en-v1.5", device="mps")


def build_text(df: pd.DataFrame) -> pd.Series:
  return (
      "Product: "
      + df["Product"]
      + " - "
      + df["Sub-product"]
      + " | Issue: "
      + df["Issue"]
      + " - "
      + df["Sub-issue"]
      + " | Tag: "
      + df["Tags"].replace("", "None")
      + " | Resolution: "
      + df["Company response to consumer"]
  )


# 2. Pass 1: Extract ONLY unique text summaries (~10k strings instead of 1.97M)
print("Scanning unique text patterns...")
unique_texts = set()
cols_needed = [
    "Complaint ID",
    "Date received",
    "Product",
    "Sub-product",
    "Issue",
    "Sub-issue",
    "Company",
    "State",
    "ZIP code",
    "Tags",
    "Company response to consumer",
    "Timely response?",
]

for chunk in pd.read_csv(
    FILE_PATH, usecols=cols_needed, dtype=str, chunksize=100000
):
  chunk = chunk.fillna("")
  unique_texts.update(build_text(chunk).unique())

unique_list = list(unique_texts)
print(f"Found {len(unique_list):,} unique combinations across 1.97M rows.")

# 3. Embed unique strings on M2 GPU
vectors = model.encode(
    unique_list, batch_size=256, show_progress_bar=True, normalize_embeddings=True
)
vector_map = {text: vec.tolist() for text, vec in zip(unique_list, vectors)}

# 4. Pass 2: Stream chunks into Chroma & portable Parquet
client = chromadb.PersistentClient(path=CHROMA_PATH)
collection = client.get_or_create_collection(
    name="cfpb_complaints", metadata={"hnsw:space": "cosine"}
)

parquet_writer = None

print("Indexing into Chroma and exporting Parquet...")
for chunk in tqdm(
    pd.read_csv(FILE_PATH, usecols=cols_needed, dtype=str, chunksize=BATCH_SIZE),
    total=198,
):
  chunk = chunk.fillna("")
  texts = build_text(chunk).tolist()
  embeddings = [vector_map[t] for t in texts]
  ids = chunk["Complaint ID"].tolist()

  # Build lean metadata for fast filtering
  metadatas = [
      {
          "company": row["Company"],
          "state": row["State"] or "UNKNOWN",
          "product": row["Product"],
          "tags": row["Tags"] or "None",
          "company_response": row["Company response to consumer"],
          "timely_response": row["Timely response?"] == "Yes",
          "date_received_int": int(row["Date received"].replace("-", "")),
      }
      for row in chunk.to_dict(orient="records")
  ]

  # Insert batch into Chroma
  collection.add(
      ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas
  )

  # Append batch to portable Parquet file (for AWS, Azure, GCP later)
  out_df = pd.DataFrame({
      "id": ids,
      "text": texts,
      "embedding": embeddings,
      "company": chunk["Company"].values,
      "state": chunk["State"].values,
      "product": chunk["Product"].values,
      "tags": chunk["Tags"].values,
      "date_received": chunk["Date received"].values,
  })
  table = pa.Table.from_pandas(out_df)
  if parquet_writer is None:
    parquet_writer = pq.ParquetWriter(
        PARQUET_PATH, table.schema, compression="snappy"
    )
  parquet_writer.write_table(table)

  del chunk, texts, embeddings, metadatas, out_df, table
  gc.collect()

if parquet_writer:
  parquet_writer.close()

print("Done! Total indexed:", collection.count())
```

**Quick tips before running**

- **Disk space check:** Make sure you have at least **12–15 GB** of free SSD space on Macintosh HD (`cfpb_chroma_384` will use ~6–7 GB and `cfpb_portable_vectors.parquet` will use ~3–4 GB).
- **Close memory-heavy apps:** Close extra browser tabs or Docker containers while running the indexing pass so Chroma has uninterrupted access to the 16 GB unified memory.


##### Airflow parallel indexing across 14 CSV files

Using Apache Airflow with **14 CSV files** on an M2 MacBook Air (16 GB RAM) is a clean fit for Airflow’s Dynamic Task Mapping (`.expand()`), provided you avoid two critical traps: **SQLite write-locking in Chroma** and **RAM exhaustion** from loading multiple embedding models simultaneously.

**Two architectural rules for parallel ingestion on 16 GB RAM**

**1. Decouple embedding from Chroma writes (avoid SQLite locks):** Local `PersistentClient` Chroma uses SQLite under the hood for metadata. If 4 or 8 Airflow workers write to the same local Chroma folder simultaneously, SQLite will throw `database is locked` errors. Instead, run a **Map-Reduce-Load** DAG:

- **Task 1 (Extract Unique Strings):** Scan all 14 CSVs quickly and write unique text combinations to a staging file.
- **Task 2 (Single-Worker GPU Embedding):** Run one task on the M2 GPU (`mps`) to embed all ~10,000 unique strings and save a single `vector_map.parquet` lookup dictionary. (Running 1 task on MPS is faster and uses ~10× less RAM than loading 14 PyTorch models in parallel).
- **Task 3 (Parallel Map via `.expand()`):** Run 14 parallel Airflow tasks (`max_active_tis_per_dagrun=4` to stay safe within 16 GB RAM). Each task reads one CSV, joins against `vector_map.parquet`, and writes a clean `part_XX.parquet` file containing `id`, `text`, `embedding`, and metadata.
- **Task 4 (Sequential Bulk Load into Chroma):** A single lightweight task reads the 14 Parquet files and bulk-inserts them into Chroma cleanly with zero lock contention.

**2. Cloud-ready artifact:** Because Task 3 produces 14 partitioned Parquet files with precomputed vectors, you can upload that exact Parquet folder straight to S3, Azure Blob, or GCS later to ingest into AWS OpenSearch, Azure AI Search, or GCP Vertex AI in parallel.

**Complete Airflow DAG (`cfpb_parallel_vector_pipeline.py`)**

Drop this file into your Airflow `dags/` folder and update `CSV_DIR` to point to your 14 CSV files:

```python
from datetime import datetime
import glob
import os
from airflow.decorators import dag, task
import pandas as pd

CSV_DIR = "/path/to/your/14_csv_files"  # <-- Update this path
STAGING_DIR = "/path/to/staging_parquet"  # <-- Update this path
CHROMA_PATH = "/path/to/cfpb_chroma_384"  # <-- Update this path

COLS_NEEDED = [
    "Complaint ID",
    "Date received",
    "Product",
    "Sub-product",
    "Issue",
    "Sub-issue",
    "Company",
    "State",
    "Tags",
    "Company response to consumer",
    "Timely response?",
]


def build_text_series(df: pd.DataFrame) -> pd.Series:
  return (
      "Product: "
      + df["Product"]
      + " - "
      + df["Sub-product"]
      + " | Issue: "
      + df["Issue"]
      + " - "
      + df["Sub-issue"]
      + " | Tag: "
      + df["Tags"].replace("", "None")
      + " | Resolution: "
      + df["Company response to consumer"]
  )


@dag(
    dag_id="cfpb_parallel_vector_pipeline",
    start_date=datetime(2026, 11, 1),
    schedule=None,
    catchup=False,
    tags=["cfpb", "chromadb", "vectors"],
)
def cfpb_vector_pipeline():

  @task
  def list_csv_files() -> list[str]:
    os.makedirs(STAGING_DIR, exist_ok=True)
    files = sorted(glob.glob(os.path.join(CSV_DIR, "*.csv")))
    if not files:
      raise FileNotFoundError(f"No CSV files found in {CSV_DIR}")
    return files

  @task
  def build_shared_embedding_lookup(csv_files: list[str]) -> str:
    """Scans all 14 CSVs for unique text summaries and embeds them ONCE on M2 GPU."""
    from sentence_transformers import SentenceTransformer

    unique_texts = set()
    for f in csv_files:
      for chunk in pd.read_csv(
          f, usecols=COLS_NEEDED, dtype=str, chunksize=100000
      ):
        chunk = chunk.fillna("")
        unique_texts.update(build_text_series(chunk).unique())

    unique_list = list(unique_texts)
    model = SentenceTransformer("BAAI/bge-small-en-v1.5", device="mps")
    vectors = model.encode(
        unique_list,
        batch_size=256,
        show_progress_bar=False,
        normalize_embeddings=True,
    )

    lookup_path = os.path.join(STAGING_DIR, "vector_lookup.parquet")
    pd.DataFrame({
        "text": unique_list,
        "embedding": [v.tolist() for v in vectors],
    }).to_parquet(lookup_path, index=False)

    return lookup_path

  @task(max_active_tis_per_dagrun=4)  # Cap at 4 workers for 16 GB RAM safety
  def transform_csv_to_parquet(csv_path: str, lookup_path: str) -> str:
    """Parallel worker: maps precomputed embeddings & cleans metadata for 1 CSV."""
    lookup_df = pd.read_parquet(lookup_path)
    vector_map = dict(zip(lookup_df["text"], lookup_df["embedding"]))

    df = pd.read_csv(csv_path, usecols=COLS_NEEDED, dtype=str).fillna("")
    df = df.drop_duplicates(subset=["Complaint ID"])

    df["text"] = build_text_series(df)
    df["embedding"] = df["text"].map(vector_map)
    df["state_clean"] = df["State"].replace("", "UNKNOWN")
    df["tags_clean"] = df["Tags"].replace("", "None")
    df["timely_bool"] = df["Timely response?"] == "Yes"
    df["date_received_int"] = (
        pd.to_datetime(df["Date received"], errors="coerce")
        .dt.strftime("%Y%m%d")
        .fillna("0")
        .astype(int)
    )

    out_df = df[[
        "Complaint ID",
        "text",
        "embedding",
        "Company",
        "state_clean",
        "Product",
        "tags_clean",
        "Company response to consumer",
        "timely_bool",
        "date_received_int",
    ]]

    base_name = os.path.splitext(os.path.basename(csv_path))[0]
    out_parquet = os.path.join(STAGING_DIR, f"{base_name}_ready.parquet")
    out_df.to_parquet(out_parquet, index=False, compression="snappy")
    return out_parquet

  @task
  def load_parquets_to_chroma(parquet_files: list[str]) -> int:
    """Single-writer bulk loader into Chroma to avoid SQLite lock errors."""
    import gc
    import chromadb

    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.get_or_create_collection(
        name="cfpb_complaints", metadata={"hnsw:space": "cosine"}
    )

    seen_ids = set()
    batch_size = 10000

    for pq_file in parquet_files:
      df = pd.read_parquet(pq_file)
      df = df[~df["Complaint ID"].isin(seen_ids)]
      seen_ids.update(df["Complaint ID"].tolist())

      for start in range(0, len(df), batch_size):
        sub = df.iloc[start : start + batch_size]
        metadatas = [
            {
                "company": r["Company"],
                "state": r["state_clean"],
                "product": r["Product"],
                "tags": r["tags_clean"],
                "company_response": r["Company response to consumer"],
                "timely_response": bool(r["timely_bool"]),
                "date_received_int": int(r["date_received_int"]),
            }
            for r in sub.to_dict(orient="records")
        ]

        collection.add(
            ids=sub["Complaint ID"].tolist(),
            embeddings=sub["embedding"].tolist(),
            documents=sub["text"].tolist(),
            metadatas=metadatas,
        )
      del df
      gc.collect()

    return collection.count()

  # Wire the DAG with Dynamic Task Mapping (.expand)
  files = list_csv_files()
  lookup = build_shared_embedding_lookup(files)
  mapped_parquets = transform_csv_to_parquet.partial(lookup_path=lookup).expand(
      csv_path=files
  )
  load_parquets_to_chroma(mapped_parquets)


cfpb_vector_pipeline()
```

**Why this DAG works well on an M2 Air**

- **Zero duplicate model loads:** Only `build_shared_embedding_lookup` touches PyTorch and the M2 GPU (`mps`), keeping peak memory low while embedding all 14 files in seconds.
- **Controlled concurrency (`max_active_tis_per_dagrun=4`):** Runs 4 CSV transformations concurrently without triggering macOS memory swap across 16 GB unified memory.
- **Reusable cloud stage:** Once `transform_csv_to_parquet` finishes, the 14 `*_ready.parquet` files act as a clean data lake layer ready for parallel upload to AWS S3, Azure Blob Storage, or GCS.

## Overall architecture

Capability view (not a folder map):

1. **Experience** — Angular Admin portal: Imports, per-MIO status, start only *allowed* workflows for that MIO.
2. **Integration** — FastAPI Middleware: workflow registry, start execution, MIO status, Airflow status callbacks (shared secret). Sole writer of the **operational/admin** catalog and logs.
3. **Orchestration** — Apache Airflow: download CFPB All, filter a 3-month slice, future DB ingest DAG. Reports `started` / `completed` / `failed` back to the API.
4. **Data** — Operational store (SQLite / Postgres / Mongo) for workflows, MIOs, bindings, ingest/exec logs; separate **complaint documents** MongoDB written only by the ingest job.
5. **Source** — CFPB public HTTP export (All zip). Filtered site downloads cannot cover multi-million-row windows, so 3 months is derived from All.
6. **Future** — `consumer-complaints-Intellect` reads complaint MongoDB for RAG / agentic workflows.

Write rules that never bend: **API owns operational data**; **Airflow owns bulk complaint MongoDB** (and may *read* operational config, never write it).

![CCAA enterprise architecture](docs/Design/ccaa-enterprise-architecture.jpg)

Layered Middleware internals (closed API → facades → open services → DAO) and deeper diagrams: [`ARCHITECTURE.md`](Middleware/ConsumerComplaintsHandsOn/ARCHITECTURE.md).

> [!CAUTION]
> # Install Superpowers on your laptop
> **To truly use this repo’s Superpowers integration (structured agent workflows: brainstorm → plan → TDD → review), each developer must install the [Superpowers](https://github.com/obra/superpowers) plugin in Cursor on their machine.**
>
> In Cursor, run:
> ```text
> /add-plugin superpowers
> ```
> Workspace setting `.cursor/settings.json` only *enables* the plugin for this project — it does **not** ship the skills in git.
>
> **The application still runs without Superpowers.** Middleware, Admin portal, Airflow, migrations, and tests work with the npm/local scripts below. Superpowers is for AI-assisted *development process*, not runtime.

## Development tooling

### Local containers (lite profiles)

Default local path uses **SQLite** for the operational/admin store — **no operational Postgres container**. Start Airflow only:

```bash
npm run local:containers:sqlite:start    # Airflow (SQLite-lite default)
npm run local:containers:sqlite:status   # shows expected: airflow
```

Opt-in profiles:

```bash
npm run local:containers:postgres:start  # Airflow + CCA operational Postgres
npm run local:containers:mongodb:start   # Airflow + MongoDB
```

`npm run local:containers:all:*` still starts/stops/status **every** `CICD/Local/*/docker-compose.yaml`. **Stop always removes Docker volumes** (`docker compose down -v`) so Airflow/Mongo/Postgres data does not linger (M01-0073 / #133). Pass `--keep-volumes` to `CICD/Local/docker-all-down.sh` only when you intentionally want to keep them. For Postgres/Mongo app config, set `.env` per `Middleware/ConsumerComplaintsHandsOn/.env.example` (D75–D78).

### Recommended local stack (three steps)

```bash
npm run local:containers:all:start          # or :sqlite:start / :postgres:start / :mongodb:start
npm run local:handson:middlware:all:start   # Middleware API (:8000)
npm run local:portals:all:start             # all Portals apps (today: admin on :4200)
```

`local:portals:all:*` is the umbrella for every app under `Portals/`; add future portals there. `local:portals:all:start` always runs `npm install` in the admin portal first (so pulls never leave deps stale), then `ng serve`. Single-app shortcuts remain: `local:portal:admin:start|build|test`. Shortcut `local:portal:admin:with-api` still starts Middleware then `local:portals:all:start`.

Admin Angular needs **Node.js 22+** (see root `.nvmrc`). If `nvm` defaults to 20:

```bash
nvm use    # or: nvm use 22
npm run local:portals:all:start
```

Then open http://localhost:4200/datasets/imports.

**Localhost Consumer Complaint Datasets (3 months) → search indexes:** [`docs/Runbooks/Localhost/3m-pgvector-chroma.md`](docs/Runbooks/Localhost/3m-pgvector-chroma.md) (#210).

E2E happy path (UI → API → Airflow → callback → UI, SQLite first): see `docs/local-admin-e2e-happy-path.md`. CI smoke: `npm run local:e2e:happy-path:smoke`. Live API probe: `npm run local:e2e:happy-path:probe`. DoD matrix (SQLite / Postgres / MongoDB): `docs/local-admin-e2e-dod-matrix.md` · `npm run local:e2e:dod-matrix:smoke`.

### Local URLs, usernames, and passwords

Defaults from `CICD/Local/*/docker-compose.yaml` and portal/API scripts. **Local-only** — never reuse these in cloud. Copy `Middleware/ConsumerComplaintsHandsOn/.env.example` → `.env` (git-ignored) and fill from this table.

> [!NOTE]
> GitHub’s README sanitizer strips `target="_blank"`, so these links always open in the **same** tab on github.com. Use **Cmd/Ctrl+click** or middle-click for a new tab.

#### Host apps (not Docker)

| Service | URL | Username | Password | Notes |
|---|---|---|---|---|
| Middleware API | http://127.0.0.1:8000 | — | — | `npm run local:handson:middlware:all:start`; OpenAPI at http://127.0.0.1:8000/docs |
| Admin portal | http://127.0.0.1:4200 | — | — | Proxies `/api` → API `:8000` |
| Intellect portal | http://127.0.0.1:4201 | — | — | Proxies `/api` → API `:8000` |
| SQLite operational DB | `Middleware/ConsumerComplaintsHandsOn/.data/operational.sqlite` | — | — | Default when `CCA_OPERATIONAL_STORE` / `CCA_DB_URL` unset |

#### Containers

| Service | URL / connection | Username | Password | `.env` / notes |
|---|---|---|---|---|
| Airflow UI + API | http://127.0.0.1:8080 | `airflow` | `airflow` | `CCA_AIRFLOW_API_BASE_URL`, `CCA_AIRFLOW_API_USERNAME`, `CCA_AIRFLOW_API_PASSWORD` |
| Airflow metadata Postgres | (internal Docker only) | `airflow` | `airflow` | DB `airflow`; not the CCA operational store |
| CCA ops Postgres (+ pgvector) | `postgresql://postgres:postgres@127.0.0.1:5432/cca` | `postgres` | `postgres` | DB `cca`. Set `CCA_OPERATIONAL_STORE=postgres`, `CCA_DB_URL=postgresql+psycopg://postgres:postgres@127.0.0.1:5432/cca`, `CCA_PGVECTOR_URL=postgresql://postgres:postgres@127.0.0.1:5432/cca` |
| MongoDB (complaints) | `mongodb://root:changeme-local@127.0.0.1:27017/?authSource=admin` | `root` | `changeme-local` | **Auth required** or Compass shows an empty Databases list. Paste that URI in Compass (or Username `root` / Password `changeme-local` / Auth DB `admin`). After first boot: `consumer_comp_db.complaints` (empty until DB Ingest). App: `CCA_MONGO_COMPLAINTS_URL=mongodb://root:changeme-local@127.0.0.1:27017/consumer_comp_db?authSource=admin`. Ops-store profile (optional): `CCA_OPERATIONAL_STORE=mongodb`, `CCA_MONGO_OPERATIONAL_URL=…/cca_operational?authSource=admin` |
| Chroma | http://127.0.0.1:8100 (host) | — | — | Host port **8100** → container 8000 (avoids Middleware `:8000`; override with `CCA_CHROMA_PORT`). **Airflow (Docker):** set `CCA_CHROMA_URL=http://host.docker.internal:8100` then Sync secrets — `127.0.0.1` inside the worker is not your Mac |
| Redis Stack | `redis://127.0.0.1:6379/0` | — | — | `CCA_REDIS_URL`. RedisInsight UI: http://127.0.0.1:8001 |

#### Required Middleware `.env` for live Airflow callbacks

| Variable | Example local value | Purpose |
|---|---|---|
| `CCA_CALLBACK_SECRET` | `cca-local-dev-callback-secret` | Shared secret; Airflow callbacks send `X-Callback-Secret` (401 without it). **Localhost fixed value only — never reuse in cloud/M90** (#211) |
| `CCA_API_URL` | `http://host.docker.internal:8000` | Base URL workers use to reach Middleware (Docker Desktop) |
| `CCA_AIRFLOW_API_PASSWORD` | `airflow` | Matches Airflow WWW user (with username `airflow`) |
| `CCA_VECTOR_STORE_PATH` | e.g. absolute path under Airflow data | JSONL vector index (`index_cfpb_all`) |
| `LOCAL_DATA_PATH_CFPB` | `$HOME/runtime_data/apps/datasets/CCA/complains_datasets/imports` | Where CFPB zips land (localhost). Use absolute `$HOME/...` in `.env`; Airflow compose bind-mounts the same path (#212) |
| `CCA_CFPB_SPLIT_SOURCE_PATH_3_MONTHS` | `$HOME/Downloads/temp/complaints_split_3_months_data` | 3-month filter input (M17-0005) |
| `CCA_CFPB_SPLIT_SOURCE_PATH_6_MONTHS` | `$HOME/Downloads/temp/complaints_split_6_months_data` | Reserved for 6-month MIO |
| `CCA_CFPB_SPLIT_SOURCE_PATH_9_MONTHS` | `$HOME/Downloads/temp/complaints_split_9_months_data` | Reserved for 9-month MIO |
| `CCA_CFPB_SPLIT_SOURCE_PATH_12_MONTHS` | `$HOME/Downloads/temp/complaints_split_12_months_data` | Reserved for 12-month MIO |
| `CCA_CFPB_SPLIT_SOURCE_PATH_ALL` | `$HOME/Downloads/temp/complaints_split_all_data` | All MIO download/stage (M17-0005) |
| `CCA_CFPB_SPLIT_SOURCE_PATH` | legacy single-folder alias | Optional fallback if per-MIO var unset |

After containers + `.env`: `npm run local:api:migrate` (SQLite/Postgres), sync Airflow Variables from Admin **Operations → Sync secrets**, then open Admin Imports.

### Superpowers plugin

> [!IMPORTANT]
> Superpowers is **required for the agent workflow** documented here, but **optional for running the product**. See the red **CAUTION** banner just above Development tooling.

This project uses the [Superpowers](https://github.com/obra/superpowers) plugin in Cursor (install on **your laptop**, not vendored into this repo). It is a core skills library that gives the AI agent structured workflows for development tasks.

Skills included:

- **Planning and design:** `brainstorming`, `writing-plans`, `executing-plans`
- **Building and testing:** `test-driven-development`, `subagent-driven-development`, `dispatching-parallel-agents`, `using-git-worktrees`
- **Debugging and quality:** `systematic-debugging`, `verification-before-completion`
- **Code review and wrap-up:** `requesting-code-review`, `receiving-code-review`, `finishing-a-development-branch`
- **Meta:** `using-superpowers`, `writing-skills`

A `sessionStart` hook loads the `using-superpowers` skill at the start of each session, so the agent checks for a relevant skill before it acts.

To install it in Cursor, run:

```
/add-plugin superpowers
```

Invoke a skill directly with `/`, for example `/brainstorming`. The agent also uses skills automatically when they apply.

#### The basic workflow

See [The Basic Workflow](https://github.com/obra/superpowers#the-basic-workflow) in the Superpowers README. In short:

1. **brainstorming:** Runs before building anything. It draws out what you want and why, then plays its understanding back for correction.
2. **using-git-worktrees:** Runs after design approval. It creates an isolated workspace on a new branch and verifies a clean test baseline.
3. **writing-plans:** Breaks the approved design into small tasks (2-5 minutes each), with exact file paths and verification steps.
4. **subagent-driven-development** or **executing-plans:** Runs the plan, either with a fresh subagent and review per task, or inline with one review of the whole branch at the end.
5. **test-driven-development:** Enforces RED-GREEN-REFACTOR during implementation.
6. **requesting-code-review:** Reviews work against the plan between tasks and reports issues by severity.
7. **finishing-a-development-branch:** Verifies tests and presents merge, PR, keep or discard options.

The agent checks for relevant skills before any task, so these workflows are mandatory rather than optional.
