-- M47-0001 / #325 — Taxonomy control plane (Iceberg).
CREATE NAMESPACE IF NOT EXISTS demo.taxonomy;

CREATE TABLE IF NOT EXISTS demo.taxonomy.money_topics (
  topic_id STRING,
  money_topic STRING,
  sort_order INT
)
USING iceberg
TBLPROPERTIES (
  'write.format.default' = 'parquet',
  'write.parquet.compression-codec' = 'zstd'
);

CREATE TABLE IF NOT EXISTS demo.taxonomy.product_crosswalk (
  product STRING,
  sub_product STRING,
  primary_money_topic STRING,
  mapping_rule STRING
)
USING iceberg
TBLPROPERTIES (
  'write.format.default' = 'parquet',
  'write.parquet.compression-codec' = 'zstd'
);

CREATE TABLE IF NOT EXISTS demo.taxonomy.semantic_signatures (
  signature_id STRING,
  product STRING,
  sub_product STRING,
  issue STRING,
  sub_issue STRING,
  tags STRING,
  primary_money_topic STRING,
  secondary_money_topic STRING,
  is_fraud_scam BOOLEAN,
  is_money_transfer BOOLEAN,
  confidence STRING,
  classifier_version STRING,
  _classified_ts TIMESTAMP
)
USING iceberg
TBLPROPERTIES (
  'write.format.default' = 'parquet',
  'write.parquet.compression-codec' = 'zstd'
);

SHOW TABLES IN demo.taxonomy;
