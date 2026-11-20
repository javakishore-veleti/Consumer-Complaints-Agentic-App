#!/usr/bin/env python3
"""Refined ⋈ semantic_signatures → curated 3m (M48-0001 / #326)."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql import types as T

from parent_org import ORG_ALIASES, canonical_parent_org_name, parent_org_id_from_company


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--refined-table", default="demo.refined.cfpb_complaints_3m")
    p.add_argument("--signatures-table", default="demo.taxonomy.semantic_signatures")
    p.add_argument("--target-table", default="demo.curated.cfpb_complaints_3m")
    p.add_argument("--run-id", default="manual")
    args = p.parse_args()

    spark = SparkSession.builder.appName("cca-hydrate-curated-3m").getOrCreate()
    spark.sparkContext.setLogLevel("WARN")
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    # Seed organization_aliases
    alias_rows = []
    for alias_key, parent_name in ORG_ALIASES.items():
        alias_rows.append(
            {
                "alias_key": alias_key,
                "parent_org_name": parent_name,
                "parent_org_id": parent_org_id_from_company(parent_name),
            }
        )
    alias_df = spark.createDataFrame(alias_rows)
    spark.sql("CREATE NAMESPACE IF NOT EXISTS demo.taxonomy")
    alias_df.writeTo("demo.taxonomy.organization_aliases").createOrReplace()
    print(f"organization_aliases={alias_df.count()}")

    def _n(col: str):
        return F.lower(F.trim(F.coalesce(F.col(col).cast("string"), F.lit(""))))

    refined = spark.table(args.refined_table)
    sigs = spark.table(args.signatures_table).alias("s")

    r = refined.alias("r")
    joined = r.join(
        sigs,
        (
            (_n("r.product") == _n("s.product"))
            & (_n("r.sub_product") == _n("s.sub_product"))
            & (_n("r.issue") == _n("s.issue"))
            & (_n("r.sub_issue") == _n("s.sub_issue"))
            & (_n("r.tags") == _n("s.tags"))
        ),
        "inner",
    )

    # Parent org via Python UDF (alias map is small).
    @F.udf(returnType=T.StringType())
    def udf_parent_id(company: str) -> str:
        return parent_org_id_from_company(company)

    @F.udf(returnType=T.StringType())
    def udf_parent_name(company: str) -> str:
        return canonical_parent_org_name(company)

    curated = joined.select(
        F.col("r.complaint_id").alias("complaint_id"),
        F.col("r.date_received").alias("date_received"),
        F.col("r.product").alias("product"),
        F.col("r.sub_product").alias("sub_product"),
        F.col("r.issue").alias("issue"),
        F.col("r.sub_issue").alias("sub_issue"),
        F.col("r.company").alias("company_raw"),
        udf_parent_id(F.col("r.company")).alias("parent_org_id"),
        udf_parent_name(F.col("r.company")).alias("parent_org_name"),
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

    n = curated.count()
    null_topic = curated.filter(
        F.col("primary_money_topic").isNull() | (F.trim(F.col("primary_money_topic")) == "")
    ).count()
    if null_topic:
        raise SystemExit(f"primary_money_topic null/blank={null_topic}")

    spark.sql("CREATE NAMESPACE IF NOT EXISTS demo.curated")
    curated.writeTo(args.target_table).createOrReplace()
    out = spark.table(args.target_table).count()
    print(f"hydrate_curated rows={n} written={out} run_id={args.run_id}")
    spark.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
