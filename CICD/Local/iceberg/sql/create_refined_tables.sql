-- M46-0001 / #324 — Iceberg Refined namespace + 3m table (24-column contract).
CREATE NAMESPACE IF NOT EXISTS demo.refined;

CREATE TABLE IF NOT EXISTS demo.refined.cfpb_complaints_3m (
  complaint_id STRING,
  date_received DATE,
  product STRING,
  sub_product STRING,
  issue STRING,
  sub_issue STRING,
  company_public_response STRING,
  company STRING,
  state STRING,
  zip_code STRING,
  zip3 STRING,
  tags STRING,
  submitted_via STRING,
  date_sent_to_company DATE,
  company_response_to_consumer STRING,
  timely_response STRING,
  consumer_complaint_narrative STRING,
  signature_id STRING,
  _dataset_slice STRING,
  _source_zip_file STRING,
  _ingest_ts TIMESTAMP,
  _airflow_run_id STRING,
  _row_hash STRING,
  _refined_ts TIMESTAMP
)
USING iceberg
PARTITIONED BY (months(date_received))
TBLPROPERTIES (
  'write.format.default' = 'parquet',
  'write.parquet.compression-codec' = 'zstd',
  'write.distribution-mode' = 'hash'
);

SHOW TABLES IN demo.refined;
