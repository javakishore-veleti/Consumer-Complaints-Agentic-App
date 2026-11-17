# M10-0015 (#222) Runbook operator plain language

## Decision
1. Operator runbook must not depend on GitHub issue numbers (`#221`, `M10-…`) to explain what to do.
2. Container stop/start instructions use `npm run local:containers:*` only (not raw `docker compose` paths).
