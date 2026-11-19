# M47-0001 / #325 — Taxonomy + Mode 2 semantic_signatures design

## Goal
Working taxonomy control plane + Mode 2 classify of 3m U_sig (~2,924) into `semantic_signatures`.

## Store
Iceberg `demo.taxonomy.*` (Spark-joinable; Parquet snapshot style per charter). Tables:
- `money_topics` — 12 CFPB Money Topics
- `product_crosswalk` — (product, sub_product) → primary_money_topic for all 3m U_prod (~55)
- `semantic_signatures` — one row per 5-field U_sig

## Mode 2 (v1 working product)
1. **Rules:** product/sub-product → primary via crosswalk.
2. **Overlay:** keyword cues on issue/sub_issue/tags for Fraud & Scams / Money Transfers → flags + optional secondary topic.
3. No GPU NLI required for this story; `classifier_version=mode2-rules-v1`.

## signature_id (registry)
SHA-256 of normalized `product|sub_product|issue|sub_issue|tags` (charter U_sig; not M46’s 6-field hash).

## Demo
Lookup a Capital One refined row’s 5-field signature → `primary_money_topic`.
