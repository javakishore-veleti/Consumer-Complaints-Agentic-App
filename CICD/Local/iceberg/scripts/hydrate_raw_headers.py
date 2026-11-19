"""Header normalize helpers for Raw hydrate (M45-0002 / #321).

Pure Python so unit checks run without Spark.
"""

from __future__ import annotations

# Live CFPB export header (15) → Iceberg snake_case. Narrative reserved as 16th source col.
CFPB_HEADER_TO_RAW = {
    "Date received": "date_received",
    "Product": "product",
    "Sub-product": "sub_product",
    "Issue": "issue",
    "Sub-issue": "sub_issue",
    "Company public response": "company_public_response",
    "Company": "company",
    "State": "state",
    "ZIP code": "zip_code",
    "Tags": "tags",
    "Submitted via": "submitted_via",
    "Date sent to company": "date_sent_to_company",
    "Company response to consumer": "company_response_to_consumer",
    "Timely response?": "timely_response",
    "Complaint ID": "complaint_id",
}

RAW_SOURCE_COLUMNS = [
    "date_received",
    "product",
    "sub_product",
    "issue",
    "sub_issue",
    "company_public_response",
    "company",
    "state",
    "zip_code",
    "tags",
    "submitted_via",
    "date_sent_to_company",
    "company_response_to_consumer",
    "timely_response",
    "complaint_id",
    "consumer_complaint_narrative",
]

AUDIT_COLUMNS = [
    "_dataset_slice",
    "_source_zip_file",
    "_ingest_ts",
    "_airflow_run_id",
    "_row_hash",
]

MANDATORY_KEYS = ("complaint_id", "date_received", "product", "company")


def normalize_header(name: str) -> str:
    cleaned = (name or "").strip().lstrip("\ufeff")
    if cleaned not in CFPB_HEADER_TO_RAW:
        raise KeyError(f"unknown CFPB header: {name!r}")
    return CFPB_HEADER_TO_RAW[cleaned]


def rename_map_for_dataframe(columns: list[str]) -> dict[str, str]:
    return {c: normalize_header(c) for c in columns}
