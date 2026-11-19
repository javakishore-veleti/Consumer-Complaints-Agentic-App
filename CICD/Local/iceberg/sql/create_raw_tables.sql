-- M45-0001 / #320 — Iceberg Raw namespace + table templates (21-column contract).
-- Catalog: demo (tabulario/spark-iceberg quickstart).
-- Source: 15 live CFPB Lift headers + reserved consumer_complaint_narrative = 16;
-- Audit: 5 pipeline columns. Partition: months(date_received).

CREATE NAMESPACE IF NOT EXISTS demo.raw;

CREATE TABLE IF NOT EXISTS demo.raw.cfpb_complaints_3m (
  date_received DATE,
  product STRING,
  sub_product STRING,
  issue STRING,
  sub_issue STRING,
  company_public_response STRING,
  company STRING,
  state STRING,
  zip_code STRING,
  tags STRING,
  submitted_via STRING,
  date_sent_to_company STRING,
  company_response_to_consumer STRING,
  timely_response STRING,
  complaint_id STRING,
  consumer_complaint_narrative STRING,
  _dataset_slice STRING,
  _source_zip_file STRING,
  _ingest_ts TIMESTAMP,
  _airflow_run_id STRING,
  _row_hash STRING
)
USING iceberg
PARTITIONED BY (months(date_received))
TBLPROPERTIES (
  'write.format.default' = 'parquet',
  'write.parquet.compression-codec' = 'zstd',
  'write.distribution-mode' = 'hash'
);

CREATE TABLE IF NOT EXISTS demo.raw.cfpb_complaints_6m (
  date_received DATE,
  product STRING,
  sub_product STRING,
  issue STRING,
  sub_issue STRING,
  company_public_response STRING,
  company STRING,
  state STRING,
  zip_code STRING,
  tags STRING,
  submitted_via STRING,
  date_sent_to_company STRING,
  company_response_to_consumer STRING,
  timely_response STRING,
  complaint_id STRING,
  consumer_complaint_narrative STRING,
  _dataset_slice STRING,
  _source_zip_file STRING,
  _ingest_ts TIMESTAMP,
  _airflow_run_id STRING,
  _row_hash STRING
)
USING iceberg
PARTITIONED BY (months(date_received))
TBLPROPERTIES (
  'write.format.default' = 'parquet',
  'write.parquet.compression-codec' = 'zstd',
  'write.distribution-mode' = 'hash'
);

CREATE TABLE IF NOT EXISTS demo.raw.cfpb_complaints_9m (
  date_received DATE,
  product STRING,
  sub_product STRING,
  issue STRING,
  sub_issue STRING,
  company_public_response STRING,
  company STRING,
  state STRING,
  zip_code STRING,
  tags STRING,
  submitted_via STRING,
  date_sent_to_company STRING,
  company_response_to_consumer STRING,
  timely_response STRING,
  complaint_id STRING,
  consumer_complaint_narrative STRING,
  _dataset_slice STRING,
  _source_zip_file STRING,
  _ingest_ts TIMESTAMP,
  _airflow_run_id STRING,
  _row_hash STRING
)
USING iceberg
PARTITIONED BY (months(date_received))
TBLPROPERTIES (
  'write.format.default' = 'parquet',
  'write.parquet.compression-codec' = 'zstd',
  'write.distribution-mode' = 'hash'
);

CREATE TABLE IF NOT EXISTS demo.raw.cfpb_complaints_12m (
  date_received DATE,
  product STRING,
  sub_product STRING,
  issue STRING,
  sub_issue STRING,
  company_public_response STRING,
  company STRING,
  state STRING,
  zip_code STRING,
  tags STRING,
  submitted_via STRING,
  date_sent_to_company STRING,
  company_response_to_consumer STRING,
  timely_response STRING,
  complaint_id STRING,
  consumer_complaint_narrative STRING,
  _dataset_slice STRING,
  _source_zip_file STRING,
  _ingest_ts TIMESTAMP,
  _airflow_run_id STRING,
  _row_hash STRING
)
USING iceberg
PARTITIONED BY (months(date_received))
TBLPROPERTIES (
  'write.format.default' = 'parquet',
  'write.parquet.compression-codec' = 'zstd',
  'write.distribution-mode' = 'hash'
);

CREATE TABLE IF NOT EXISTS demo.raw.cfpb_complaints_all (
  date_received DATE,
  product STRING,
  sub_product STRING,
  issue STRING,
  sub_issue STRING,
  company_public_response STRING,
  company STRING,
  state STRING,
  zip_code STRING,
  tags STRING,
  submitted_via STRING,
  date_sent_to_company STRING,
  company_response_to_consumer STRING,
  timely_response STRING,
  complaint_id STRING,
  consumer_complaint_narrative STRING,
  _dataset_slice STRING,
  _source_zip_file STRING,
  _ingest_ts TIMESTAMP,
  _airflow_run_id STRING,
  _row_hash STRING
)
USING iceberg
PARTITIONED BY (months(date_received))
TBLPROPERTIES (
  'write.format.default' = 'parquet',
  'write.parquet.compression-codec' = 'zstd',
  'write.distribution-mode' = 'hash'
);

-- Quarantine: same 21 columns; no partition required (bad/null keys land here).
CREATE TABLE IF NOT EXISTS demo.raw.cfpb_complaints_quarantine (
  date_received DATE,
  product STRING,
  sub_product STRING,
  issue STRING,
  sub_issue STRING,
  company_public_response STRING,
  company STRING,
  state STRING,
  zip_code STRING,
  tags STRING,
  submitted_via STRING,
  date_sent_to_company STRING,
  company_response_to_consumer STRING,
  timely_response STRING,
  complaint_id STRING,
  consumer_complaint_narrative STRING,
  _dataset_slice STRING,
  _source_zip_file STRING,
  _ingest_ts TIMESTAMP,
  _airflow_run_id STRING,
  _row_hash STRING
)
USING iceberg
TBLPROPERTIES (
  'write.format.default' = 'parquet',
  'write.parquet.compression-codec' = 'zstd'
);

SHOW TABLES IN demo.raw;
