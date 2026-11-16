# M04-0014 (#160) Admin DB Ingest screen

## Goal

Enable **DB Ingest** nav; page mirrors Imports (MIO status, start/refresh) but picker shows only `ingest_*` workflows. Imports picker excludes `ingest_*` / `index_*`.

## Design

1. `DbIngestPageComponent` under `pages/datasets/db-ingest/` — same HTTP helpers as Imports.
2. Route `/datasets/db-ingest`; sidebar item enabled (`left-nav-db-ingest`).
3. Start disabled while running **or** when latest status is not `completed` (download must finish first).
4. No AppEndpoints panel on this page (Imports keeps it).
5. Portal unit tests for route shell + ingest workflow filter.

## Out of scope

AppEndpoint resolution in DAGs (#161), location UX copy (#162).
