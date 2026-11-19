#!/usr/bin/env bash
# Unzip latest Lift Zone 3m CSV parts into a staging dir (M45-0002 / #321).
# Prefer running inside cca-spark-iceberg where /lift is mounted; host path also OK.
set -euo pipefail

LIFT_ROOT="${CCA_LIFT_ZONE_IN_CONTAINER:-${CCA_LIFT_ZONE:-/lift}}"
RUN_ID="${1:-manual-$(date -u +%Y%m%dT%H%M%SZ)}"
STAGE_ROOT="${CCA_RAW_STAGE_ROOT:-/tmp/cca_raw_stage}"
STAGE_DIR="${STAGE_ROOT}/${RUN_ID}"

if [ ! -d "$LIFT_ROOT" ]; then
  echo "Lift root missing: $LIFT_ROOT" >&2
  exit 1
fi

# Latest imports/*/dataset that has at least one *3_months*.csv.zip
LATEST=""
# shellcheck disable=SC2044
for d in $(find "$LIFT_ROOT/imports" -type d -name dataset 2>/dev/null | sort); do
  if ls "$d"/*3_months*.csv.zip >/dev/null 2>&1; then
    LATEST="$d"
  fi
done

if [ -z "$LATEST" ]; then
  echo "no *3_months*.csv.zip under $LIFT_ROOT/imports" >&2
  exit 1
fi

mkdir -p "$STAGE_DIR"
echo "lift_batch=$LATEST"
echo "stage_dir=$STAGE_DIR"

# Unzip only archives with non-zero payload (skip empty parts).
shopt -s nullglob
for z in "$LATEST"/*3_months*.csv.zip; do
  # Skip empty compressed parts quickly via unzip -l size
  size=$(unzip -l "$z" | awk 'END{print $1}')
  if [ "${size:-0}" = "0" ] || [ -z "$size" ]; then
    echo "skip empty $z"
    continue
  fi
  echo "unzip $z"
  unzip -o -q "$z" -d "$STAGE_DIR"
done

count=$(find "$STAGE_DIR" -maxdepth 1 -type f -name '*.csv' | wc -l | tr -d ' ')
if [ "$count" -lt 1 ]; then
  echo "no CSV staged in $STAGE_DIR" >&2
  exit 1
fi
echo "staged_csv_count=$count"
echo "$STAGE_DIR"
