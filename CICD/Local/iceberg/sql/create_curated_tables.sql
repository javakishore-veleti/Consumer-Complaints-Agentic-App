-- M48-0001 / #326 — Curated (Gold) 3m + org aliases.
CREATE NAMESPACE IF NOT EXISTS demo.curated;
CREATE NAMESPACE IF NOT EXISTS demo.taxonomy;

CREATE TABLE IF NOT EXISTS demo.taxonomy.organization_aliases (
  alias_key STRING,
  parent_org_name STRING,
  parent_org_id STRING
)
USING iceberg
TBLPROPERTIES (
  'write.format.default' = 'parquet',
  'write.parquet.compression-codec' = 'zstd'
);

CREATE TABLE IF NOT EXISTS demo.curated.cfpb_complaints_3m (
  complaint_id STRING,
  date_received DATE,
  product STRING,
  sub_product STRING,
  issue STRING,
  sub_issue STRING,
  company_raw STRING,
  parent_org_id STRING,
  parent_org_name STRING,
  state STRING,
  zip3 STRING,
  tags STRING,
  submitted_via STRING,
  date_sent_to_company DATE,
  company_response_to_consumer STRING,
  timely_response STRING,
  registry_signature_id STRING,
  primary_money_topic STRING,
  secondary_money_topic STRING,
  is_fraud_scam BOOLEAN,
  is_money_transfer BOOLEAN,
  confidence STRING,
  classifier_version STRING,
  refined_signature_id STRING,
  _dataset_slice STRING,
  _row_hash STRING,
  _curated_ts TIMESTAMP
)
USING iceberg
PARTITIONED BY (months(date_received))
TBLPROPERTIES (
  'write.format.default' = 'parquet',
  'write.parquet.compression-codec' = 'zstd',
  'write.distribution-mode' = 'hash'
);

SHOW TABLES IN demo.curated;
