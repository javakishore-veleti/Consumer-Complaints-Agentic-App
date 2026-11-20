#!/usr/bin/env bash
# Apply Iceberg foundational DDL for all zones (Raw → Refined → Taxonomy → Curated).
# Runs inside cca-spark-iceberg (M58-0001 / #400). Idempotent CREATE IF NOT EXISTS SQL.
set -euo pipefail

SQL_ROOT="${CCA_ICEBERG_SQL_ROOT:-/opt/cca/iceberg/sql}"
ORDER=(
  create_raw_tables.sql
  create_refined_tables.sql
  create_taxonomy_tables.sql
  create_curated_tables.sql
)

for name in "${ORDER[@]}"; do
  path="${SQL_ROOT}/${name}"
  if [ ! -f "$path" ]; then
    echo "missing SQL: $path" >&2
    exit 1
  fi
  echo "==> spark-sql -f $path"
  spark-sql -f "$path"
done

echo "==> verify namespaces"
spark-sql -e "SHOW NAMESPACES IN demo;"
spark-sql -e "SHOW TABLES IN demo.raw;"
spark-sql -e "SHOW TABLES IN demo.refined;"
spark-sql -e "SHOW TABLES IN demo.curated;"
echo "==> foundational Iceberg DDL done"
