# M52-0001 Query AST API design

## Goal
Expose Query AST validate/translate (and optional Spark execute) via `POST /intellect/query-ast`.

## Shape
- Canonical translator: `app/core/common/query_ast.py` (CICD script re-exports).
- Facade → service (ctx-only); API under `/intellect`.
- `execute=false` (default): return SQL only.
- `execute=true`: docker exec spark-sql when container up; enforce k-anon ≥10; else clear failure.
