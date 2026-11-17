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
# uuid.uuid5(uuid.NAMESPACE_URL, "ccaa/m04-0013/ingest_cfpb_all")
INGEST_WF_ID = "0064095f-9f8e-5f09-94cf-3b4fe28e2b33"
ALL_MIO_ID = "01fa6351-cf12-520d-886d-9b8e30515451"
ALL_MIOS_DATASETS_ID = "038915b0-1a19-50e9-9333-e49f3816a0f8"
MW_ALL_DOWNLOAD_ID = "c23808b9-4e57-5a5b-b301-78dec5ac839e"
MW_3M_FILTER_ID = "edd79fde-5736-5655-9d00-c52bfe172c1f"
# uuid.uuid5(uuid.NAMESPACE_URL, "ccaa/m04-0013/mios-workflows-all-ingest")
MW_ALL_INGEST_ID = "251b44d2-9aea-5d9d-b1a0-0816e8db3f80"
# uuid.uuid5(uuid.NAMESPACE_URL, "ccaa/m04-0017/index_cfpb_all")
INDEX_WF_ID = "120e90d3-f61d-5fd4-a8c4-2a1aba9e9ba6"
# uuid.uuid5(uuid.NAMESPACE_URL, "ccaa/m04-0018/mios-workflows-all-index")
MW_ALL_INDEX_ID = "ee28b7aa-b4cf-5611-bf07-080fb3b53864"
MIO_3_MONTHS_ID = "a10fbfe0-ac03-5f3f-8d20-5132d470b03a"
# uuid.uuid5(uuid.NAMESPACE_URL, "ccaa/m04-0009/ep-cfpb-source-http-local")
APP_ENDPOINT_SOURCE_ID = "ccbce57d-bd9f-56fe-a258-fa2deb9dd393"
# uuid.uuid5(uuid.NAMESPACE_URL, "ccaa/m04-0015/ep-cfpb-ingest-local-mongo")
APP_ENDPOINT_INGEST_ID = "8ca22b0c-1c7c-5a25-be9d-d51c6063a3a5"
# uuid.uuid5(uuid.NAMESPACE_URL, "ccaa/m04-0017/ep-cfpb-index-mongo-vectors")
APP_ENDPOINT_INDEX_ID = "af151640-ce3a-5995-a390-fa1ec5212aaf"
# uuid.uuid5(uuid.NAMESPACE_URL, "ccaa/m06-0004/ep-cfpb-stage-split-local")
APP_ENDPOINT_STAGE_SPLIT_ID = "763c400e-09e1-59a5-92ed-ed910df667ac"
NOW_SPLIT = datetime(2026, 11, 16, tzinfo=timezone.utc)
# uuid.uuid5(uuid.NAMESPACE_URL, "ccaa/m07-0007/index_cfpb_pgvector")
INDEX_PG_WF_ID = "68a0fa8a-825c-53f1-864f-5db167a339a0"
# uuid.uuid5(uuid.NAMESPACE_URL, "ccaa/m07-0008/mios-workflows-all-index-pgvector")
MW_ALL_INDEX_PG_ID = "494ff42b-a7e7-5e90-8430-74b81a52dff1"
# uuid.uuid5(uuid.NAMESPACE_URL, "ccaa/m07-0008/ep-cfpb-index-mongo-pgvector")
APP_ENDPOINT_INDEX_PG_ID = "2e6bd178-2900-5ea2-80ed-507f486a2133"
NOW_PGVECTOR = datetime(2026, 11, 16, tzinfo=timezone.utc)
# uuid.uuid5(uuid.NAMESPACE_URL, "ccaa/m09-0008/index_cfpb_chroma")
INDEX_CHROMA_WF_ID = "87100dc6-f634-5bde-8539-d7175ca194ac"
# uuid.uuid5(uuid.NAMESPACE_URL, "ccaa/m09-0010/index_cfpb_redis")
INDEX_REDIS_WF_ID = "474e4e9a-5743-54c2-99f6-5ec860aa8c38"
# uuid.uuid5(uuid.NAMESPACE_URL, "ccaa/m09-0011/mios-workflows-all-index-chroma")
MW_ALL_INDEX_CHROMA_ID = "2a43462f-e29d-506c-9422-1a39dfdc16eb"
# uuid.uuid5(uuid.NAMESPACE_URL, "ccaa/m09-0011/mios-workflows-all-index-redis")
MW_ALL_INDEX_REDIS_ID = "cc9d2cc5-088a-5d57-8227-4c2d2ef1cbc9"
# uuid.uuid5(uuid.NAMESPACE_URL, "ccaa/m09-0011/ep-cfpb-index-mongo-chroma")
APP_ENDPOINT_INDEX_CHROMA_ID = "1046ad4a-b4fd-509b-9bc3-9e8501ef86c0"
# uuid.uuid5(uuid.NAMESPACE_URL, "ccaa/m09-0011/ep-cfpb-index-mongo-redis")
APP_ENDPOINT_INDEX_REDIS_ID = "bc449f1d-4055-5514-8794-c2ca504ebd99"
NOW_M09 = datetime(2026, 11, 16, tzinfo=timezone.utc)
# uuid.uuid5(uuid.NAMESPACE_URL, "ccaa/m05-0004/acl-all-internal")
ACL_ALL_ID = "814a15b9-246b-5f8f-baef-a3f75a946a72"
# uuid.uuid5(uuid.NAMESPACE_URL, "ccaa/m05-0004/acl-3m-internal")
ACL_3M_ID = "c57c33d4-f3c6-50a9-b614-5f095d4d7134"
NOW_ENDPOINTS = datetime(2026, 11, 15, tzinfo=timezone.utc)
NOW_INGEST = datetime(2026, 11, 15, tzinfo=timezone.utc)
NOW_INDEX = datetime(2026, 11, 15, tzinfo=timezone.utc)
NOW_ACL = datetime(2026, 11, 16, tzinfo=timezone.utc)

COLLECTIONS = (
    "app_workflows",
    "app_workflows_exec_log",
    "datasets",
    "datasets_location",
    "dataset_import_runs",
    "app_endpoints",
    "mios",
    "mios_datasets",
    "mios_workflows",
    "mios_acl",
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
    db["mios_acl"].create_index([("mio_id", 1), ("audience", 1)], unique=True)
    db["mios_acl"].create_index("mio_id")
    db["app_endpoints"].create_index("name", unique=True)
    db["app_endpoints"].create_index("category")
    db["app_workflows_exec_log"].create_index([("workflow_id", 1), ("status", 1)])
    db["app_workflows_exec_log"].create_index("mios_ingest_log_id")
    db["mios_ingest_log"].create_index([("mio_id", 1), ("status", 1)])
    db["dataset_import_runs"].create_index("run_folder_name", unique=True)
    db["dataset_import_runs"].create_index("status")
    db["dataset_import_runs"].create_index([("workflow_started_at", -1), ("id", -1)])


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
                "config": {
                    "dataset_code": "CFPB",
                    "source_mode": "split",
                    "source_filename_glob": "complaints_part_*.csv.zip",
                    "stage_from_env": "CCA_CFPB_SPLIT_SOURCE_PATH",
                    "app_endpoint_name": "cfpb_stage_split_to_local",
                },
                "enabled": True,
                "created_at": NOW_CATALOG,
                "updated_at": NOW_SPLIT,
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
    _upsert(
        MongoDocument(
            {
                "_collection": "app_workflows",
                "id": INGEST_WF_ID,
                "workflow_name": "ingest_cfpb_all",
                "engine_type": "apache_airflow",
                "engine_workflow_id": "ingest_cfpb_all",
                "config": {
                    "dataset_code": "CFPB",
                    "source_filename_glob": "complaints_part_*.csv.zip",
                    "batch_size": 500,
                    "app_endpoint_name": "cfpb_ingest_local_to_mongo",
                },
                "enabled": True,
                "created_at": NOW_INGEST,
                "updated_at": NOW_SPLIT,
            }
        )
    )
    _upsert(
        MongoDocument(
            {
                "_collection": "mios_workflows",
                "id": MW_ALL_INGEST_ID,
                "mio_id": ALL_MIO_ID,
                "workflow_id": INGEST_WF_ID,
                "created_at": NOW_INGEST,
            }
        )
    )
    _upsert(
        MongoDocument(
            {
                "_collection": "app_endpoints",
                "id": APP_ENDPOINT_SOURCE_ID,
                "name": "cfpb_source_http_to_local",
                "category": "source",
                "from_dataset_location_id": HTTP_LOCATION_ID,
                "from_env_var_name": None,
                "to_dataset_location_id": LOCAL_LOCATION_ID,
                "to_env_var_name": None,
                "credentials_ref": None,
                "description": "CFPB download HTTP source to local landing (D63)",
                "enabled": True,
                "created_at": NOW_ENDPOINTS,
                "updated_at": NOW_ENDPOINTS,
            }
        )
    )
    _upsert(
        MongoDocument(
            {
                "_collection": "app_endpoints",
                "id": APP_ENDPOINT_STAGE_SPLIT_ID,
                "name": "cfpb_stage_split_to_local",
                "category": "source",
                "from_dataset_location_id": None,
                "from_env_var_name": "CCA_CFPB_SPLIT_SOURCE_PATH",
                "to_dataset_location_id": None,
                "to_env_var_name": "LOCAL_DATA_PATH_CFPB",
                "credentials_ref": None,
                "description": "Stage CFPB split parts into local landing (D91)",
                "enabled": True,
                "created_at": NOW_SPLIT,
                "updated_at": NOW_SPLIT,
            }
        )
    )
    _upsert(
        MongoDocument(
            {
                "_collection": "app_endpoints",
                "id": APP_ENDPOINT_INGEST_ID,
                "name": "cfpb_ingest_local_to_mongo",
                "category": "ingest",
                "from_dataset_location_id": LOCAL_LOCATION_ID,
                "from_env_var_name": None,
                "to_dataset_location_id": None,
                "to_env_var_name": "CCA_MONGO_COMPLAINTS_URL",
                "credentials_ref": None,
                "description": "Local landing → complaint Mongo (D86/D87)",
                "enabled": True,
                "created_at": NOW_ENDPOINTS,
                "updated_at": NOW_ENDPOINTS,
            }
        )
    )
    _upsert(
        MongoDocument(
            {
                "_collection": "app_workflows",
                "id": INDEX_WF_ID,
                "workflow_name": "index_cfpb_all",
                "engine_type": "apache_airflow",
                "engine_workflow_id": "index_cfpb_all",
                "config": {
                    "dataset_code": "CFPB",
                    "batch_size": 500,
                    "app_endpoint_name": "cfpb_index_mongo_to_vectors",
                },
                "enabled": True,
                "created_at": NOW_INDEX,
                "updated_at": NOW_INDEX,
            }
        )
    )
    _upsert(
        MongoDocument(
            {
                "_collection": "mios_workflows",
                "id": MW_ALL_INDEX_ID,
                "mio_id": ALL_MIO_ID,
                "workflow_id": INDEX_WF_ID,
                "created_at": NOW_INDEX,
            }
        )
    )
    _upsert(
        MongoDocument(
            {
                "_collection": "app_endpoints",
                "id": APP_ENDPOINT_INDEX_ID,
                "name": "cfpb_index_mongo_to_vectors",
                "category": "index",
                "from_dataset_location_id": None,
                "from_env_var_name": "CCA_MONGO_COMPLAINTS_URL",
                "to_dataset_location_id": None,
                "to_env_var_name": "CCA_VECTOR_STORE_PATH",
                "credentials_ref": None,
                "description": "Complaint Mongo → local vector store (D88)",
                "enabled": True,
                "created_at": NOW_ENDPOINTS,
                "updated_at": NOW_ENDPOINTS,
            }
        )
    )
    _upsert(
        MongoDocument(
            {
                "_collection": "app_workflows",
                "id": INDEX_PG_WF_ID,
                "workflow_name": "index_cfpb_pgvector",
                "engine_type": "apache_airflow",
                "engine_workflow_id": "index_cfpb_pgvector",
                "config": {
                    "dataset_code": "CFPB",
                    "batch_size": 500,
                    "vector_backend": "pgvector",
                    "app_endpoint_name": "cfpb_index_mongo_to_pgvector",
                },
                "enabled": True,
                "created_at": NOW_PGVECTOR,
                "updated_at": NOW_PGVECTOR,
            }
        )
    )
    _upsert(
        MongoDocument(
            {
                "_collection": "mios_workflows",
                "id": MW_ALL_INDEX_PG_ID,
                "mio_id": ALL_MIO_ID,
                "workflow_id": INDEX_PG_WF_ID,
                "created_at": NOW_PGVECTOR,
            }
        )
    )
    _upsert(
        MongoDocument(
            {
                "_collection": "app_endpoints",
                "id": APP_ENDPOINT_INDEX_PG_ID,
                "name": "cfpb_index_mongo_to_pgvector",
                "category": "index",
                "from_dataset_location_id": None,
                "from_env_var_name": "CCA_MONGO_COMPLAINTS_URL",
                "to_dataset_location_id": None,
                "to_env_var_name": "CCA_PGVECTOR_URL",
                "credentials_ref": None,
                "description": "Complaint Mongo → local pgvector (D92)",
                "enabled": True,
                "created_at": NOW_PGVECTOR,
                "updated_at": NOW_PGVECTOR,
            }
        )
    )
    for wf_id, name, backend, ep_id, ep_name, env_to, mw_id in (
        (
            INDEX_CHROMA_WF_ID,
            "index_cfpb_chroma",
            "chroma",
            APP_ENDPOINT_INDEX_CHROMA_ID,
            "cfpb_index_mongo_to_chroma",
            "CCA_CHROMA_URL",
            MW_ALL_INDEX_CHROMA_ID,
        ),
        (
            INDEX_REDIS_WF_ID,
            "index_cfpb_redis",
            "redis",
            APP_ENDPOINT_INDEX_REDIS_ID,
            "cfpb_index_mongo_to_redis",
            "CCA_REDIS_URL",
            MW_ALL_INDEX_REDIS_ID,
        ),
    ):
        _upsert(
            MongoDocument(
                {
                    "_collection": "app_workflows",
                    "id": wf_id,
                    "workflow_name": name,
                    "engine_type": "apache_airflow",
                    "engine_workflow_id": name,
                    "config": {
                        "dataset_code": "CFPB",
                        "batch_size": 500,
                        "vector_backend": backend,
                        "app_endpoint_name": ep_name,
                    },
                    "enabled": True,
                    "created_at": NOW_M09,
                    "updated_at": NOW_M09,
                }
            )
        )
        _upsert(
            MongoDocument(
                {
                    "_collection": "mios_workflows",
                    "id": mw_id,
                    "mio_id": ALL_MIO_ID,
                    "workflow_id": wf_id,
                    "created_at": NOW_M09,
                }
            )
        )
        _upsert(
            MongoDocument(
                {
                    "_collection": "app_endpoints",
                    "id": ep_id,
                    "name": ep_name,
                    "category": "index",
                    "from_dataset_location_id": None,
                    "from_env_var_name": "CCA_MONGO_COMPLAINTS_URL",
                    "to_dataset_location_id": None,
                    "to_env_var_name": env_to,
                    "credentials_ref": None,
                    "description": f"Complaint Mongo → local {backend} (D94)",
                    "enabled": True,
                    "created_at": NOW_M09,
                    "updated_at": NOW_M09,
                }
            )
        )
    _upsert(
        MongoDocument(
            {
                "_collection": "mios_acl",
                "id": ACL_ALL_ID,
                "mio_id": ALL_MIO_ID,
                "audience": "internal",
                "created_at": NOW_ACL,
            }
        )
    )
    _upsert(
        MongoDocument(
            {
                "_collection": "mios_acl",
                "id": ACL_3M_ID,
                "mio_id": MIO_3_MONTHS_ID,
                "audience": "internal",
                "created_at": NOW_ACL,
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
