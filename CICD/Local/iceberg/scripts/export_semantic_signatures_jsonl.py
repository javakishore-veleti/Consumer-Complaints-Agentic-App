"""Spark job: dump taxonomy.semantic_signatures to warehouse JSONL (M49-0001 / #336)."""

from __future__ import annotations

import argparse

from pyspark.sql import SparkSession


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--out",
        default="/home/iceberg/warehouse/_exports/cfpb_semantic_signatures",
    )
    p.add_argument(
        "--signatures-table",
        default="demo.taxonomy.semantic_signatures",
    )
    args = p.parse_args()
    spark = SparkSession.builder.getOrCreate()
    df = spark.table(args.signatures_table).select(
        "signature_id",
        "product",
        "sub_product",
        "issue",
        "sub_issue",
        "tags",
        "primary_money_topic",
        "secondary_money_topic",
        "is_fraud_scam",
        "is_money_transfer",
    )
    (
        df.write.mode("overwrite")
        .option("compression", "none")
        .json(args.out)
    )
    print(f"exported={df.count()} path={args.out}")


if __name__ == "__main__":
    main()
