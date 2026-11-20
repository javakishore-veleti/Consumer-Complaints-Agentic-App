# M59-0001 Admin left-nav order — design

**Story:** #402 · **Date:** 2026-11-20

## Decision

Reorder `navItems` in Admin sidebar only (no route changes):

1. Dashboard  
2. App Endpoints  
3. Schemas  
4. DataSets  
5. DB Ingest  
6. Lakehouse  
7. Vector Stores  
8. Workflow Logs  
9. Operations  

Preserve all `data-testid` values. Also tidy localhost 3m runbook: Schemas/Lakehouse after Sync secrets; drop redundant Airflow `docker compose` from happy path (postgres/mongodb/chroma npm starts already bring Airflow up).
