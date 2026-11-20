#!/usr/bin/env python3
"""Raw → Refined 3m hydrate with signature_id + zip3 (M46-0001 / #324)."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone

from pyspark.sql import SparkSession
from pyspark.sql import functions as F


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--source-table", default="demo.raw.cfpb_complaints_3m")
    p.add_argument("--target-table", default="demo.refined.cfpb_complaints_3m")
    p.add_argument("--run-id", default="manual")
    args = p.parse_args()

    spark = (
        SparkSession.builder.appName("cca-hydrate-refined-3m")
        .config("spark.sql.sources.partitionOverwriteMode", "dynamic")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")

    raw = spark.table(args.source_table)
    refined_ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    sig_parts = [
        F.lower(F.trim(F.coalesce(F.col(c).cast("string"), F.lit(""))))
        for c in (
            "product",
            "sub_product",
            "issue",
            "sub_issue",
            "tags",
            "company_response_to_consumer",
        )
    ]
    digits = F.regexp_replace(F.coalesce(F.col("zip_code").cast("string"), F.lit("")), r"\D", "")
    zip3 = F.when(F.length(digits) >= 3, F.substring(digits, 1, 3)).otherwise(F.lit("UNK"))

    df = (
        raw.withColumn("zip3", zip3)
        .withColumn("signature_id", F.sha2(F.concat_ws("||", *sig_parts), 256))
        .withColumn(
            "date_sent_to_company",
            F.to_date(F.col("date_sent_to_company").cast("string"), "yyyy-MM-dd"),
        )
        .withColumn("_refined_ts", F.to_timestamp(F.lit(refined_ts)))
        .select(
            "complaint_id",
            "date_received",
            "product",
            "sub_product",
            "issue",
            "sub_issue",
            "company_public_response",
            "company",
            "state",
            "zip_code",
            "zip3",
            "tags",
            "submitted_via",
            "date_sent_to_company",
            "company_response_to_consumer",
            "timely_response",
            "consumer_complaint_narrative",
            "signature_id",
            "_dataset_slice",
            "_source_zip_file",
            "_ingest_ts",
            "_airflow_run_id",
            "_row_hash",
            "_refined_ts",
        )
    )

    null_sig = df.filter(F.col("signature_id").isNull() | (F.col("signature_id") == "")).count()
    if null_sig:
        raise SystemExit(f"signature_id null/blank rows={null_sig}")

    n = df.count()
    spark.sql("CREATE NAMESPACE IF NOT EXISTS demo.refined")
    df.writeTo(args.target_table).createOrReplace()
    out = spark.table(args.target_table).count()
    distinct = spark.table(args.target_table).select("signature_id").distinct().count()
    print(
        f"hydrate_refined slice=3m rows={n} written={out} "
        f"distinct_signature_id={distinct} run_id={args.run_id}"
    )
    spark.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
