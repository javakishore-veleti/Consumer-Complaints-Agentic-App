# M48-0001 / #326 — curated.cfpb_complaints_3m design

## Goal
Working Curated (Gold) 3m table: refined facts + Mode 2 Money Topics + parent_org via broadcast join.

## Pipeline
1. DDL `demo.curated.cfpb_complaints_3m` (+ optional `demo.taxonomy.organization_aliases`).
2. Join refined 3m → `semantic_signatures` on normalized 5-field U_sig keys.
3. `parent_org_id` = SHA-256 of normalized company name; alias table overrides for known Capital One variants.
4. DELETE+append replace curated; prove COUNT + SparkSQL/DuckDB group-by Money Topic.

## Out of scope
Full 31-col Gold expansion, embeddings, Chroma (M49).
