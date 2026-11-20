#!/usr/bin/env python3
"""Refined ⋈ semantic_signatures → curated 3m (M48-0001 / #326; OOM fix M55-0008)."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

from parent_org import ORG_ALIASES, parent_org_id_from_company


def _norm(col: str):
    """Lower/trim string column for join keys (Spark-native, no Python UDF)."""
    return F.lower(F.trim(F.coalesce(F.col(col).cast("string"), F.lit(""))))


def _company_key(col):
    """Match parent_org.normalize_company_key in Spark SQL."""
    s = F.lower(F.trim(F.coalesce(col.cast("string"), F.lit(""))))
    s = F.regexp_replace(s, r"[^a-z0-9\s]+", " ")
    return F.trim(F.regexp_replace(s, r"\s+", " "))


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--refined-table", default="demo.refined.cfpb_complaints_3m")
    p.add_argument("--signatures-table", default="demo.taxonomy.semantic_signatures")
    p.add_argument("--target-table", default="demo.curated.cfpb_complaints_3m")
    p.add_argument("--run-id", default="manual")
    # M55-0011: optional partition batch from Middleware claim (≤5 keys). Empty = full table.
    p.add_argument(
        "--partition-keys",
        default="",
        help="Comma-separated keys from POST /ingestion-logs/curated/claim (max 5)",
    )
    p.add_argument(
        "--num-buckets",
        type=int,
        default=20,
        help="pmod(hash(complaint_id), N) bucket count when --partition-keys is set",
    )
    args = p.parse_args()
    partition_keys = [k.strip() for k in args.partition_keys.split(",") if k.strip()]
    if len(partition_keys) > 5:
        raise SystemExit("--partition-keys accepts at most 5 keys (Middleware claim cap)")

    spark = SparkSession.builder.appName("cca-hydrate-curated-3m").getOrCreate()
    spark.sparkContext.setLogLevel("WARN")
    # Fit ~8GiB Docker Desktop headroom (M55-0009). maxResultSize is static — set only via spark-submit.
    spark.conf.set("spark.sql.shuffle.partitions", "8")
    spark.conf.set("spark.sql.adaptive.enabled", "true")
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    # Seed organization_aliases (tiny; broadcast later for parent-org lookup).
    alias_rows = [
        {
            "alias_key": alias_key,
            "parent_org_name": parent_name,
            "parent_org_id": parent_org_id_from_company(parent_name),
        }
        for alias_key, parent_name in ORG_ALIASES.items()
    ]
    alias_df = spark.createDataFrame(alias_rows)
    spark.sql("CREATE NAMESPACE IF NOT EXISTS demo.taxonomy")
    alias_df.writeTo("demo.taxonomy.organization_aliases").createOrReplace()
    print(f"organization_aliases={alias_df.count()}")

    refined = spark.table(args.refined_table)
    if partition_keys:
        # Durable queue: process only claimed hash buckets (M55-0011).
        bucket = F.pmod(F.hash(F.col("complaint_id").cast("string")), F.lit(int(args.num_buckets)))
        refined = refined.where(bucket.isin([int(k) for k in partition_keys]))
        print(f"hydrate_curated partition_keys={partition_keys} num_buckets={args.num_buckets}")
    sigs = spark.table(args.signatures_table)

    # Pre-normalize join keys once; broadcast ~3k signature rows.
    r = refined.select(
        "*",
        _norm("product").alias("_jp"),
        _norm("sub_product").alias("_jsp"),
        _norm("issue").alias("_ji"),
        _norm("sub_issue").alias("_jsi"),
        _norm("tags").alias("_jt"),
        _company_key(F.col("company")).alias("_ck"),
    ).alias("r")
    s = F.broadcast(
        sigs.select(
            "*",
            _norm("product").alias("_jp"),
            _norm("sub_product").alias("_jsp"),
            _norm("issue").alias("_ji"),
            _norm("sub_issue").alias("_jsi"),
            _norm("tags").alias("_jt"),
        )
    ).alias("s")
    aliases = F.broadcast(spark.table("demo.taxonomy.organization_aliases")).alias("a")

    joined = (
        r.join(
            s,
            (F.col("r._jp") == F.col("s._jp"))
            & (F.col("r._jsp") == F.col("s._jsp"))
            & (F.col("r._ji") == F.col("s._ji"))
            & (F.col("r._jsi") == F.col("s._jsi"))
            & (F.col("r._jt") == F.col("s._jt")),
            "inner",
        )
        .join(aliases, F.col("r._ck") == F.col("a.alias_key"), "left")
    )

    fallback_name = F.when(
        F.trim(F.coalesce(F.col("r.company").cast("string"), F.lit(""))) == "",
        F.lit("UNKNOWN"),
    ).otherwise(F.trim(F.col("r.company").cast("string")))
    parent_name = F.coalesce(F.col("a.parent_org_name"), fallback_name)
    parent_id = F.coalesce(
        F.col("a.parent_org_id"),
        F.sha2(_company_key(parent_name), 256),
    )

    curated = joined.select(
        F.col("r.complaint_id").alias("complaint_id"),
        F.col("r.date_received").alias("date_received"),
        F.col("r.product").alias("product"),
        F.col("r.sub_product").alias("sub_product"),
        F.col("r.issue").alias("issue"),
        F.col("r.sub_issue").alias("sub_issue"),
        F.col("r.company").alias("company_raw"),
        parent_id.alias("parent_org_id"),
        parent_name.alias("parent_org_name"),
        F.col("r.state").alias("state"),
        F.col("r.zip3").alias("zip3"),
        F.col("r.tags").alias("tags"),
        F.col("r.submitted_via").alias("submitted_via"),
        F.col("r.date_sent_to_company").alias("date_sent_to_company"),
        F.col("r.company_response_to_consumer").alias("company_response_to_consumer"),
        F.col("r.timely_response").alias("timely_response"),
        F.col("s.signature_id").alias("registry_signature_id"),
        F.col("s.primary_money_topic").alias("primary_money_topic"),
        F.col("s.secondary_money_topic").alias("secondary_money_topic"),
        F.col("s.is_fraud_scam").alias("is_fraud_scam"),
        F.col("s.is_money_transfer").alias("is_money_transfer"),
        F.col("s.confidence").alias("confidence"),
        F.col("s.classifier_version").alias("classifier_version"),
        F.col("r.signature_id").alias("refined_signature_id"),
        F.col("r._dataset_slice").alias("_dataset_slice"),
        F.col("r._row_hash").alias("_row_hash"),
        F.to_timestamp(F.lit(ts)).alias("_curated_ts"),
    )

    spark.sql("CREATE NAMESPACE IF NOT EXISTS demo.curated")
    curated.writeTo(args.target_table).createOrReplace()
    written = spark.table(args.target_table)
    out = written.count()
    null_topic = written.filter(
        F.col("primary_money_topic").isNull() | (F.trim(F.col("primary_money_topic")) == "")
    ).limit(1).count()
    if null_topic:
        raise SystemExit(f"primary_money_topic null/blank present after write rows={out}")
    print(f"hydrate_curated rows={out} written={out} run_id={args.run_id}")
    spark.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
