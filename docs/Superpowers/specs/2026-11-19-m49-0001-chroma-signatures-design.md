# M49-0001 / #336 — Chroma cfpb_semantic_signatures design

## Goal
Working Chroma catalog `cfpb_semantic_signatures` from Iceberg `taxonomy.semantic_signatures` (3m U_sig ~2,924). Catalog only — not 19M complaint rows.

## Approach
1. Export/read signature rows (signature_id + 5-field text + Money Topic metadata).
2. Embed with existing `hash_embedding` (MVP / CI; BGE later).
3. Upsert into Chroma via existing `ChromaStore` (`CCA_CHROMA_URL`, default `http://127.0.0.1:8100`).
4. Prove: collection count ≈ U_sig; query returns a hit with Money Topic metadata.

## Out of scope
BGE model download, org/fingerprint catalogs, Query AST (M50), Airflow DAG wiring (follow-up).
