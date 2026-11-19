# M45-0001 / #320 — Implementation plan

1. Add `iceberg=iceberg` to `CICD/Local/profiles.map`.
2. Add npm scripts `local:containers:iceberg:{start,stop,status}` in root `package.json`.
3. Add `CICD/Local/iceberg/sql/create_raw_tables.sql` (CREATE NAMESPACE + tables).
4. Add `CICD/Local/iceberg/scripts/apply_raw_ddl.sh` to run SQL in `cca-spark-iceberg`.
5. Update `CICD/Local/iceberg/README.md` and `docs/Runbooks/Localhost/3m-pgvector-chroma.md` §0.1 with npm stop/start.
6. Start iceberg via npm, apply DDL, verify `SHOW TABLES IN raw`.
7. Commit-push; PR/merge; story-complete.
