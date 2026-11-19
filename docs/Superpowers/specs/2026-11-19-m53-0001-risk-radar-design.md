# M53-0001 risk-radar API

`GET`/`POST /intellect/risk-radar` returns cohort velocity alerts for Systemic Risk Radar MVP.

- `source=fixture` (default): golden JSON alerts; always 200 in CI.
- `source=warehouse`: requires Iceberg Spark container; else 503.
- Each alert includes `drilldown_ast` for Query AST handoff; `k_anon_ok` when count ≥ 10.
