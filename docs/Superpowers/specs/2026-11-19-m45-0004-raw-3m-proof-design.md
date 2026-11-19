# M45-0004 / #323 — Raw 3m count reconcile proof

## Goal
Prove `SELECT COUNT(*) FROM demo.raw.cfpb_complaints_3m` equals Lift Zone 3m CSV row count (~1.97M), mandatory keys 0% null/blank, quarantine rate noted.

## Method
1. Host-count rows in latest `*3_months*.csv.zip`.
2. Full hydrate with table replace (DELETE + append) to avoid partial-partition residue.
3. SparkSQL COUNT + bad-key sum + sample SELECT; write evidence under `runtime_data/tmp/raw-3m-proof-*.txt`.
4. Record operator steps in Iceberg README + 3m runbook.
