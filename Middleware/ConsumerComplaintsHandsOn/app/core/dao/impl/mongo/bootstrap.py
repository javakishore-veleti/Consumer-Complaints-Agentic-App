"""Indexes and Alembic-equivalent seeds for the Mongo operational store (D79)."""

from __future__ import annotations

from datetime import datetime, timezone

from app.core.dao.impl.mongo.client import get_mongo_db
from app.core.dao.impl.mongo.docs import MongoDocument

NOW_CATALOG = datetime(2026, 11, 14, tzinfo=timezone.utc)
NOW_FILTER = datetime(2026, 11, 15, tzinfo=timezone.utc)
HTTP_URL = "https://files.consumerfinance.gov/ccdb/complaints.csv.zip"

DATASET_ID = "5187ad0c-d8ed-56ac-829d-e49313c16dbf"
HTTP_LOCATION_ID = "776fc47e-efe7-59e6-b213-549261919d79"
LOCAL_LOCATION_ID = "2fc79860-7a4a-58b0-a0eb-45f994cfbace"
MIOS = (
    ("a10fbfe0-ac03-5f3f-8d20-5132d470b03a", "f4baf6a8-1b8c-5145-b016-9a870bdecd6f", 3),
    ("b0f8bb64-be6b-5773-9f4c-3552ca36dc37", "012a8fd8-3f34-5843-b0ca-f4cf42f070a4", 6),
    ("f34fa9f1-e361-5fc0-98e0-f557bb561176", "47081de5-5db8-5c50-8b9a-6597d5624a84", 9),
    ("eb33e86c-5972-5d25-95aa-87625bec004d", "47fa4276-bc79-5e7b-a961-c33016e56199", 12),
)
DOWNLOAD_WF_ID = "b4b8014f-d756-5bc8-a041-96899ac037ac"
FILTER_WF_ID = "4d3f1ee0-0b02-51cb-8959-2499896cc20e"
ALL_MIO_ID = "01fa6351-cf12-520d-886d-9b8e30515451"
ALL_MIOS_DATASETS_ID = "038915b0-1a19-50e9-9333-e49f3816a0f8"
MW_ALL_DOWNLOAD_ID = "c23808b9-4e57-5a5b-b301-78dec5ac839e"
MW_3M_FILTER_ID = "edd79fde-5736-5655-9d00-c52bfe172c1f"
MIO_3_MONTHS_ID = "a10fbfe0-ac03-5f3f-8d20-5132d470b03a"

COLLECTIONS = (
    "app_workflows",
    "app_workflows_exec_log",
    "datasets",
    "datasets_location",
    "mios",
    "mios_datasets",
    "mios_workflows",
    "mios_ingest_log",
)


def ensure_indexes() -> None:
    db = get_mongo_db()
    db["app_workflows"].create_index("workflow_name", unique=True)
    db["datasets"].create_index("name", unique=True)
    db["datasets"].create_index("code", unique=True)
    db["mios"].create_index("name", unique=True)
    db["datasets_location"].create_index(
        [("dataset_id", 1), ("location_type", 1), ("path", 1)],
        unique=True,
        name="uq_datasets_location_dataset_type_path",
        partialFilterExpression={"path": {"$type": "string"}},
    )
    db["datasets_location"].create_index(
        [("dataset_id", 1), ("local_env_var_name", 1)],
        unique=True,
        name="uq_datasets_location_dataset_env_var",
        partialFilterExpression={"local_env_var_name": {"$type": "string"}},
    )
    db["mios_datasets"].create_index([("mio_id", 1), ("dataset_id", 1)], unique=True)
    db["mios_workflows"].create_index([("mio_id", 1), ("workflow_id", 1)], unique=True)
    db["mios_workflows"].create_index("mio_id")
    db["mios_workflows"].create_index("workflow_id")
    db["app_workflows_exec_log"].create_index([("workflow_id", 1), ("status", 1)])
    db["app_workflows_exec_log"].create_index("mios_ingest_log_id")
    db["mios_ingest_log"].create_index([("mio_id", 1), ("status", 1)])


def _upsert(doc: MongoDocument) -> None:
    """Upsert one document; collection name is doc['_collection']."""
    collection = doc.pop("_collection")
    db = get_mongo_db()
    stored = {**doc, "_id": doc["id"]}
    db[collection].replace_one({"_id": doc["id"]}, stored, upsert=True)


def seed_if_empty() -> None:
    """Insert fixed catalog + workflow seeds when app_workflows is empty (idempotent by id)."""
    db = get_mongo_db()
    if db["app_workflows"].count_documents({}) > 0 and db["mios"].count_documents({}) > 0:
        return

    _upsert(
        MongoDocument(
            {
                "_collection": "datasets",
                "id": DATASET_ID,
                "name": "cfpb_consumer_complaints",
                "code": "CFPB",
                "description": "The full CFPB Consumer Complaint Database file",
                "created_at": NOW_CATALOG,
                "updated_at": NOW_CATALOG,
            }
        )
    )
    _upsert(
        MongoDocument(
            {
                "_collection": "datasets_location",
                "id": HTTP_LOCATION_ID,
                "dataset_id": DATASET_ID,
                "location_type": "http",
                "path": HTTP_URL,
                "local_env_var_name": None,
                "credentials_ref": None,
                "description": "The public download of the CFPB file",
                "created_at": NOW_CATALOG,
                "updated_at": NOW_CATALOG,
            }
        )
    )
    _upsert(
        MongoDocument(
            {
                "_collection": "datasets_location",
                "id": LOCAL_LOCATION_ID,
                "dataset_id": DATASET_ID,
                "location_type": "local",
                "path": None,
                "local_env_var_name": "LOCAL_DATA_PATH_CFPB",
                "credentials_ref": None,
                "description": "Where the file is kept; each environment sets the variable",
                "created_at": NOW_CATALOG,
                "updated_at": NOW_CATALOG,
            }
        )
    )
    for mio_id, link_id, months in MIOS:
        _upsert(
            MongoDocument(
                {
                    "_collection": "mios",
                    "id": mio_id,
                    "name": f"Customer complaints {months} months 2026",
                    "description": "A label only. The data is what mios_datasets links.",
                    "created_at": NOW_CATALOG,
                    "updated_at": NOW_CATALOG,
                }
            )
        )
        _upsert(
            MongoDocument(
                {
                    "_collection": "mios_datasets",
                    "id": link_id,
                    "mio_id": mio_id,
                    "dataset_id": DATASET_ID,
                    "dataset_location_id": HTTP_LOCATION_ID,
                    "created_at": NOW_CATALOG,
                }
            )
        )
    _upsert(
        MongoDocument(
            {
                "_collection": "mios",
                "id": ALL_MIO_ID,
                "name": "Customer complaints all 2026",
                "description": "A label only. The data is what mios_datasets links.",
                "created_at": NOW_FILTER,
                "updated_at": NOW_FILTER,
            }
        )
    )
    _upsert(
        MongoDocument(
            {
                "_collection": "mios_datasets",
                "id": ALL_MIOS_DATASETS_ID,
                "mio_id": ALL_MIO_ID,
                "dataset_id": DATASET_ID,
                "dataset_location_id": HTTP_LOCATION_ID,
                "created_at": NOW_FILTER,
            }
        )
    )
    _upsert(
        MongoDocument(
            {
                "_collection": "app_workflows",
                "id": DOWNLOAD_WF_ID,
                "workflow_name": "download_cfpb_all",
                "engine_type": "apache_airflow",
                "engine_workflow_id": "download_cfpb_all",
                "config": {"dataset_code": "CFPB"},
                "enabled": True,
                "created_at": NOW_CATALOG,
                "updated_at": NOW_CATALOG,
            }
        )
    )
    _upsert(
        MongoDocument(
            {
                "_collection": "app_workflows",
                "id": FILTER_WF_ID,
                "workflow_name": "filter_cfpb_3_months",
                "engine_type": "apache_airflow",
                "engine_workflow_id": "filter_cfpb_3_months",
                "config": {
                    "dataset_code": "CFPB",
                    "months": 3,
                    "source_filename": "complaints.csv.zip",
                    "output_filename": "complaints_3_months.csv.zip",
                    "date_column": "Date received",
                },
                "enabled": True,
                "created_at": NOW_FILTER,
                "updated_at": NOW_FILTER,
            }
        )
    )
    _upsert(
        MongoDocument(
            {
                "_collection": "mios_workflows",
                "id": MW_ALL_DOWNLOAD_ID,
                "mio_id": ALL_MIO_ID,
                "workflow_id": DOWNLOAD_WF_ID,
                "created_at": NOW_FILTER,
            }
        )
    )
    _upsert(
        MongoDocument(
            {
                "_collection": "mios_workflows",
                "id": MW_3M_FILTER_ID,
                "mio_id": MIO_3_MONTHS_ID,
                "workflow_id": FILTER_WF_ID,
                "created_at": NOW_FILTER,
            }
        )
    )


def bootstrap_operational_mongo() -> None:
    ensure_indexes()
    seed_if_empty()


def drop_all_collections() -> None:
    db = get_mongo_db()
    for name in COLLECTIONS:
        db[name].drop()
