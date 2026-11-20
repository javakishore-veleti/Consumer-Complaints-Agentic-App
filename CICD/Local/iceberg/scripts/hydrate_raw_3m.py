#!/usr/bin/env python3
"""Lift Zone → demo.raw.cfpb_complaints_3m hydrate (M45-0002 / #321).

Expects staged CSV files under --stage-dir (from stage_unzip_3m.sh).
Runs inside cca-spark-iceberg (tabulario/spark-iceberg).
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timezone

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

# Copied alongside this file into the container.
from hydrate_raw_headers import (  # noqa: E402
    AUDIT_COLUMNS,
    CFPB_HEADER_TO_RAW,
    MANDATORY_KEYS,
    RAW_SOURCE_COLUMNS,
)


def build_spark(app_name: str) -> SparkSession:
    return (
        SparkSession.builder.appName(app_name)
        .config("spark.sql.sources.partitionOverwriteMode", "dynamic")
        .getOrCreate()
    )


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Hydrate demo.raw.cfpb_complaints_3m from staged CSVs")
    p.add_argument("--stage-dir", required=True, help="Directory of unzipped *.csv files")
    p.add_argument("--run-id", required=True, help="Airflow/manual run id for audit column")
    p.add_argument("--slice", default="3m")
    p.add_argument("--target-table", default="demo.raw.cfpb_complaints_3m")
    p.add_argument("--quarantine-table", default="demo.raw.cfpb_complaints_quarantine")
    p.add_argument("--limit", type=int, default=0, help="Optional row limit for smoke tests")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    stage = args.stage_dir
    if not os.path.isdir(stage):
        print(f"stage dir missing: {stage}", file=sys.stderr)
        return 2

    csv_files = sorted(
        os.path.join(stage, f) for f in os.listdir(stage) if f.lower().endswith(".csv")
    )
    if not csv_files:
        print(f"no CSV files in {stage}", file=sys.stderr)
        return 2

    spark = build_spark(f"cca-hydrate-raw-{args.slice}")
    spark.sparkContext.setLogLevel("WARN")

    # Read with multi-line / quote resilience; keep source zip name from filename.
    frames = []
    for path in csv_files:
        base = os.path.basename(path)
        # complaints_part_001_3_months.csv → zip name used in Lift
        zip_name = base + ".zip" if not base.endswith(".zip") else base
        df = (
            spark.read.option("header", True)
            .option("multiLine", True)
            .option("escape", '"')
            .option("quote", '"')
            .option("mode", "PERMISSIVE")
            .csv(path)
        )
        for c in df.columns:
            key = c.lstrip("\ufeff").strip()
            if key not in CFPB_HEADER_TO_RAW:
                raise SystemExit(f"unexpected header {c!r} in {path}")
            df = df.withColumnRenamed(c, CFPB_HEADER_TO_RAW[key])
        # Lift object name is <csv>.zip
        _ = zip_name  # retained for clarity / future path maps
        df = df.withColumn("_source_zip_file", F.lit(base + ".zip"))
        frames.append(df)

    raw = frames[0]
    for extra in frames[1:]:
        raw = raw.unionByName(extra, allowMissingColumns=True)

    if args.limit and args.limit > 0:
        raw = raw.limit(args.limit)

    # Parse date; add reserved narrative + audit
    ingest_ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    df = (
        raw.withColumn(
            "date_received",
            F.to_date(F.col("date_received"), "yyyy-MM-dd"),
        )
        .withColumn("consumer_complaint_narrative", F.lit(None).cast("string"))
        .withColumn("_dataset_slice", F.lit(args.slice))
        .withColumn("_ingest_ts", F.to_timestamp(F.lit(ingest_ts)))
        .withColumn("_airflow_run_id", F.lit(args.run_id))
    )

    # Deterministic row hash over source business columns (pre-audit except zip already set)
    hash_cols = [F.coalesce(F.col(c).cast("string"), F.lit("")) for c in RAW_SOURCE_COLUMNS if c != "consumer_complaint_narrative"]
    hash_cols.append(F.coalesce(F.col("consumer_complaint_narrative").cast("string"), F.lit("")))
    df = df.withColumn("_row_hash", F.sha2(F.concat_ws("||", *hash_cols), 256))

    # Select exact 21-column contract order
    ordered = RAW_SOURCE_COLUMNS + AUDIT_COLUMNS
    df = df.select(*ordered)

    bad = None
    good = df
    for key in MANDATORY_KEYS:
        if key == "date_received":
            cond = F.col(key).isNull()
        else:
            cond = F.col(key).isNull() | (F.trim(F.col(key).cast("string")) == "")
        piece = good.filter(cond)
        bad = piece if bad is None else bad.unionByName(piece)
        good = good.filter(~cond)

    q_count = bad.count() if bad is not None else 0
    g_count = good.count()
    print(f"hydrate slice={args.slice} good={g_count} quarantine={q_count}")

    # Fresh local Iceberg volumes have no demo.raw yet (DDL is optional).
    spark.sql("CREATE NAMESPACE IF NOT EXISTS demo.raw")

    if q_count > 0:
        writer = bad.writeTo(args.quarantine_table).option("fanout-enabled", "true")
        if spark.catalog.tableExists(args.quarantine_table):
            writer.append()
        else:
            writer.create()
        print(f"wrote {q_count} rows to {args.quarantine_table}")

    # Full-slice replace: createOrReplace works on first run and later re-hydrates
    # (DELETE FROM fails when the table does not exist yet).
    good.writeTo(args.target_table).createOrReplace()
    print(f"wrote {g_count} rows to {args.target_table} (createOrReplace)")

    # Quick verify
    total = spark.table(args.target_table).count()
    print(f"VERIFY COUNT(*) FROM {args.target_table} = {total}")
    spark.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
