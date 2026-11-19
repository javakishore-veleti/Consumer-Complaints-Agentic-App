# M54 Query AST zero-hit relaxation

`POST /intellect/query-ast` with `relax: true` returns ordered broaden steps (drop zip3 → product → state → org) with SQL trail. Execute retries candidates until k-anon ok.
