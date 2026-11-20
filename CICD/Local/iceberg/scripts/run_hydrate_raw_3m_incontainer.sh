#!/usr/bin/env bash
# Run inside cca-spark-iceberg (no docker CLI). Used by Airflow DAG + optional manual exec.
set -euo pipefail

SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# CCA_RAW_RUN_ID should be Middleware execution_id (UUID). Sanitize anyway for
# manual/engine fallbacks that may contain ':' / '+' (Spark URI path rules).
RUN_ID="${CCA_RAW_RUN_ID:-manual-$(date -u +%Y%m%dT%H%M%SZ)}"
STAGE_RUN_ID="$(printf '%s' "$RUN_ID" | tr ':/+' '___')"
LIMIT_ARGS=()
if [ "${CCA_RAW_LIMIT:-0}" != "0" ]; then
  LIMIT_ARGS=(--limit "${CCA_RAW_LIMIT}")
fi

export CCA_LIFT_ZONE_IN_CONTAINER="${CCA_LIFT_ZONE_IN_CONTAINER:-/lift}"
STAGE_DIR=$(bash "${SCRIPTS_DIR}/stage_unzip_3m.sh" "$STAGE_RUN_ID" | tee /dev/stderr | tail -1)

export PYTHONPATH="${SCRIPTS_DIR}:${PYTHONPATH:-}"
/opt/spark/bin/spark-submit "${SCRIPTS_DIR}/hydrate_raw_3m.py" \
  --stage-dir "$STAGE_DIR" \
  --run-id "$RUN_ID" \
  --slice 3m \
  "${LIMIT_ARGS[@]+"${LIMIT_ARGS[@]}"}"

echo "done run_id=$RUN_ID stage=$STAGE_DIR"
