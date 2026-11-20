#!/usr/bin/env python3
"""Seed taxonomy + Mode 2 classify 3m U_sig (M47-0001 / #325)."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql import types as T

from mode2_classify import MONEY_TOPICS, classify_signature, primary_topic_from_product


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--refined-table", default="demo.refined.cfpb_complaints_3m")
    p.add_argument("--money-topics-json", default="/opt/cca/iceberg/taxonomy/money_topics.json")
    p.add_argument("--run-id", default="manual")
    args = p.parse_args()

    spark = SparkSession.builder.appName("cca-taxonomy-mode2-3m").getOrCreate()
    spark.sparkContext.setLogLevel("WARN")
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    # --- money_topics ---
    topics_path = Path(args.money_topics_json)
    if not topics_path.is_file():
        # fallback when docker-cp'd next to script
        topics_path = Path("/tmp/money_topics.json")
    topics = json.loads(topics_path.read_text(encoding="utf-8"))
    assert len(topics) == 12
    assert {t["money_topic"] for t in topics} == set(MONEY_TOPICS)
    topics_df = spark.createDataFrame(topics)
    spark.sql("CREATE NAMESPACE IF NOT EXISTS demo.taxonomy")
    topics_df.writeTo("demo.taxonomy.money_topics").createOrReplace()
    print(f"money_topics={topics_df.count()}")

    # --- product_crosswalk from refined U_prod ---
    refined = spark.table(args.refined_table)
    uprod = (
        refined.select(
            F.coalesce(F.col("product"), F.lit("")).alias("product"),
            F.coalesce(F.col("sub_product"), F.lit("")).alias("sub_product"),
        )
        .distinct()
        .collect()
    )
    xwalk_rows = []
    for r in uprod:
        topic = primary_topic_from_product(r["product"], r["sub_product"])
        xwalk_rows.append(
            {
                "product": r["product"],
                "sub_product": r["sub_product"],
                "primary_money_topic": topic,
                "mapping_rule": "mode2-product-cue-v1",
            }
        )
    xwalk_df = spark.createDataFrame(xwalk_rows)
    xwalk_df.writeTo("demo.taxonomy.product_crosswalk").createOrReplace()
    print(f"product_crosswalk={xwalk_df.count()}")

    # --- distinct U_sig (5-field, normalized) + classify ---
    def _n(col: str):
        return F.lower(F.trim(F.coalesce(F.col(col).cast("string"), F.lit(""))))

    sigs = refined.select(
        _n("product").alias("product"),
        _n("sub_product").alias("sub_product"),
        _n("issue").alias("issue"),
        _n("sub_issue").alias("sub_issue"),
        _n("tags").alias("tags"),
    ).distinct()

    # Classify on driver for ~3k rows (Mode 2 rules are cheap/deterministic).
    classified = []
    for r in sigs.collect():
        out = classify_signature(
            r["product"], r["sub_product"], r["issue"], r["sub_issue"], r["tags"]
        )
        classified.append(
            {
                "signature_id": out["signature_id"],
                "product": r["product"],
                "sub_product": r["sub_product"],
                "issue": r["issue"],
                "sub_issue": r["sub_issue"],
                "tags": r["tags"],
                "primary_money_topic": out["primary_money_topic"],
                "secondary_money_topic": out["secondary_money_topic"],
                "is_fraud_scam": out["is_fraud_scam"],
                "is_money_transfer": out["is_money_transfer"],
                "confidence": out["confidence"],
                "classifier_version": out["classifier_version"],
                "_classified_ts": ts,
            }
        )

    schema = T.StructType(
        [
            T.StructField("signature_id", T.StringType(), False),
            T.StructField("product", T.StringType(), True),
            T.StructField("sub_product", T.StringType(), True),
            T.StructField("issue", T.StringType(), True),
            T.StructField("sub_issue", T.StringType(), True),
            T.StructField("tags", T.StringType(), True),
            T.StructField("primary_money_topic", T.StringType(), True),
            T.StructField("secondary_money_topic", T.StringType(), True),
            T.StructField("is_fraud_scam", T.BooleanType(), True),
            T.StructField("is_money_transfer", T.BooleanType(), True),
            T.StructField("confidence", T.StringType(), True),
            T.StructField("classifier_version", T.StringType(), True),
            T.StructField("_classified_ts", T.StringType(), True),
        ]
    )
    sig_df = spark.createDataFrame(classified, schema=schema).withColumn(
        "_classified_ts", F.to_timestamp(F.col("_classified_ts"))
    )
    sig_df.writeTo("demo.taxonomy.semantic_signatures").createOrReplace()
    n = spark.table("demo.taxonomy.semantic_signatures").count()
    print(f"semantic_signatures={n} run_id={args.run_id}")
    spark.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
