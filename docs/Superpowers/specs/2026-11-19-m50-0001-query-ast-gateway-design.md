# M50-0001 / #338 — Query AST Gateway golden query design

## Goal
Working Neutral Query AST → SparkSQL translator that answers ≥1 Golden query against `demo.curated.cfpb_complaints_3m`.

## Approach
1. LCD AST: EQ/NEQ/IN/NOT_IN + AND/OR/NOT (depth ≤ 3); allow-listed curated columns only.
2. `ast_to_sql` compiles to `SELECT COUNT(*) … WHERE …`.
3. Golden suite JSON: Capital One `parent_org_id` + Credit Cards → exact count 3844 (verified 2026-11-19).
4. k-anonymity gate: reject n < 10.

## Out of scope
NL-to-AST LLM, vector hybrid, cloud SQL adapters, relaxation cascade, FastAPI edge (follow-up).
