# Retired (D94 / M09)

pgvector now runs on the **ops Postgres** image (`CICD/Local/postgres` → `pgvector/pgvector:pg16`).

- Start: `npm run local:containers:postgres:start`
- Env: `CCA_PGVECTOR_URL=postgresql://postgres:postgres@127.0.0.1:5432/cca`
- npm profile `pgvector` aliases to the `postgres` profile (no second container)
