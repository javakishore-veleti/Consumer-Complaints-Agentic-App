"""Indexes and Alembic-equivalent seeds for the Mongo operational store (D79)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import NamedTuple

from app.core.dao.impl.mongo.client import get_mongo_db
from app.core.dao.impl.mongo.docs import MongoDocument

NOW_CATALOG = datetime(2026, 11, 14, tzinfo=UTC)
NOW_FILTER = datetime(2026, 11, 15, tzinfo=UTC)
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
# uuid.uuid5(uuid.NAMESPACE_URL, "ccaa/m11/ingest_cfpb_imports_wrapper")
INGEST_WRAPPER_WF_ID = "e64365bd-98f4-52a4-a3bc-e26455915c6b"
# uuid.uuid5(uuid.NAMESPACE_URL, "ccaa/m11/mios-workflows-all-ingest-wrapper")
MW_ALL_INGEST_WRAPPER_ID = "3075d780-d9eb-5fe5-8b03-2cdcab384cc9"
NOW_M11 = datetime(2026, 11, 17, tzinfo=UTC)
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
NOW_SPLIT = datetime(2026, 11, 16, tzinfo=UTC)
# uuid.uuid5(uuid.NAMESPACE_URL, "ccaa/m07-0007/index_cfpb_pgvector")
INDEX_PG_WF_ID = "68a0fa8a-825c-53f1-864f-5db167a339a0"
# uuid.uuid5(uuid.NAMESPACE_URL, "ccaa/m07-0008/mios-workflows-all-index-pgvector")
MW_ALL_INDEX_PG_ID = "494ff42b-a7e7-5e90-8430-74b81a52dff1"
# uuid.uuid5(uuid.NAMESPACE_URL, "ccaa/m07-0008/ep-cfpb-index-mongo-pgvector")
APP_ENDPOINT_INDEX_PG_ID = "2e6bd178-2900-5ea2-80ed-507f486a2133"
NOW_PGVECTOR = datetime(2026, 11, 16, tzinfo=UTC)
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
NOW_M09 = datetime(2026, 11, 16, tzinfo=UTC)
# uuid.uuid5(uuid.NAMESPACE_URL, "ccaa/m05-0004/acl-all-internal")
ACL_ALL_ID = "814a15b9-246b-5f8f-baef-a3f75a946a72"
# uuid.uuid5(uuid.NAMESPACE_URL, "ccaa/m05-0004/acl-3m-internal")
ACL_3M_ID = "c57c33d4-f3c6-50a9-b614-5f095d4d7134"
NOW_ENDPOINTS = datetime(2026, 11, 15, tzinfo=UTC)
NOW_INGEST = datetime(2026, 11, 15, tzinfo=UTC)
NOW_INDEX = datetime(2026, 11, 15, tzinfo=UTC)
NOW_ACL = datetime(2026, 11, 16, tzinfo=UTC)
# uuid.uuid5(uuid.NAMESPACE_URL, "ccaa/m51-0001/hydrate_raw_iceberg_3m")
HYDRATE_RAW_ICEBERG_WF_ID = "e73565a9-73dc-542e-b45d-18c9b6de39cf"
# uuid.uuid5(uuid.NAMESPACE_URL, "ccaa/m51-0001/mios-workflows-3m-hydrate-raw")
MW_3M_HYDRATE_RAW_ID = "a9d57ca1-63a8-5a7e-8ebb-c742102cc5e7"
NOW_M51 = datetime(2026, 11, 19, tzinfo=UTC)
# uuid.uuid5(uuid.NAMESPACE_URL, "ccaa/m51-0002/hydrate_refined_iceberg_3m")
HYDRATE_REFINED_ICEBERG_WF_ID = "e5d00f51-f8af-5055-a153-23426590c86d"
# uuid.uuid5(uuid.NAMESPACE_URL, "ccaa/m51-0002/mios-workflows-3m-hydrate-refined")
MW_3M_HYDRATE_REFINED_ID = "f26e2cea-3e5c-55cb-9a37-2e2cf6c07572"
HYDRATE_TAXONOMY_WF_ID = "0f362cca-2dd3-55d1-b0d4-7d4cc769defd"
MW_3M_HYDRATE_TAXONOMY_ID = "c7661b4d-92d2-59eb-b778-f2cde5bf0e56"
HYDRATE_CURATED_WF_ID = "24e5f80c-68cc-5f99-8f33-2fd3ea48d4b0"
MW_3M_HYDRATE_CURATED_ID = "e1043a76-3059-57de-945f-a376c6ad3a78"
HYDRATE_CHROMA_WF_ID = "0663b30e-987d-5938-85d5-cf919bd8f017"
MW_3M_HYDRATE_CHROMA_ID = "7808b2a0-b480-5ab8-b631-10f32aa82f90"

COLLECTIONS = (
    "app_workflows",
    "app_workflows_exec_log",
    "datasets",
    "datasets_location",
    "dataset_import_runs",
    "dataset_import_run_tags",
    "app_endpoints",
    "mios",
    "mios_datasets",
    "mios_workflows",
    "mios_acl",
    "mios_ingest_log",
    "ingest_log_raw",
    "ingest_log_refined",
    "ingest_log_curated",
    "ingest_log_taxonomy",
    "ingest_log_chroma",
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
    db["dataset_import_run_tags"].create_index("tag")
    db["dataset_import_run_tags"].create_index(
        [("import_run_id", 1), ("tag", 1)],
        unique=True,
        name="uq_dataset_import_run_tags_run_tag",
    )
    for zone in ("raw", "refined", "curated", "taxonomy", "chroma"):
        coll = f"ingest_log_{zone}"
        db[coll].create_index(
            [("partition_key", 1), ("source_end_point_id", 1), ("dest_end_point_id", 1)],
            unique=True,
            name=f"uq_ingest_log_{zone}_partition_endpoints",
        )
        db[coll].create_index([("status", 1), ("status_updated_on", -1)], name=f"ix_ingest_log_{zone}_status_updated")
        db[coll].create_index("workflow_execution_id", name=f"ix_ingest_log_{zone}_workflow_execution_id")
        db[coll].create_index([("status_updated_on", -1)], name=f"ix_ingest_log_{zone}_status_updated_on")


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
                    "stage_from_env": "CCA_CFPB_SPLIT_SOURCE_PATH_ALL",
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
                    "source_path_env": "CCA_CFPB_SPLIT_SOURCE_PATH_3_MONTHS",
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
                "_collection": "app_workflows",
                "id": INGEST_WRAPPER_WF_ID,
                "workflow_name": "ingest_cfpb_imports_wrapper",
                "engine_type": "apache_airflow",
                "engine_workflow_id": "ingest_cfpb_imports_wrapper",
                "config": {
                    "dataset_code": "CFPB",
                    "source_filename_glob": "complaints_part_*.csv.zip",
                    "batch_size": 500,
                },
                "enabled": True,
                "created_at": NOW_M11,
                "updated_at": NOW_M11,
            }
        )
    )
    _upsert(
        MongoDocument(
            {
                "_collection": "mios_workflows",
                "id": MW_ALL_INGEST_WRAPPER_ID,
                "mio_id": ALL_MIO_ID,
                "workflow_id": INGEST_WRAPPER_WF_ID,
                "created_at": NOW_M11,
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
                "from_env_var_name": "CCA_CFPB_SPLIT_SOURCE_PATH_ALL",
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


def ensure_m51_hydrate_raw_iceberg_seed() -> None:
    """Idempotent seed for Admin-triggerable Raw Iceberg hydrate (M51-0001 / #341)."""
    _upsert(
        MongoDocument(
            {
                "_collection": "app_workflows",
                "id": HYDRATE_RAW_ICEBERG_WF_ID,
                "workflow_name": "hydrate_raw_iceberg_3m",
                "engine_type": "apache_airflow",
                "engine_workflow_id": "hydrate_raw_iceberg_3m",
                "config": {
                    "dataset_code": "CFPB",
                    "dataset_slice": "3m",
                    "lakehouse_zone": "raw",
                },
                "enabled": True,
                "created_at": NOW_M51,
                "updated_at": NOW_M51,
            }
        )
    )
    _upsert(
        MongoDocument(
            {
                "_collection": "mios_workflows",
                "id": MW_3M_HYDRATE_RAW_ID,
                "mio_id": MIO_3_MONTHS_ID,
                "workflow_id": HYDRATE_RAW_ICEBERG_WF_ID,
                "created_at": NOW_M51,
            }
        )
    )


def ensure_m51_hydrate_refined_iceberg_seed() -> None:
    """Idempotent seed for Admin-triggerable Refined Iceberg hydrate (M51-0002 / #342)."""
    _upsert(
        MongoDocument(
            {
                "_collection": "app_workflows",
                "id": HYDRATE_REFINED_ICEBERG_WF_ID,
                "workflow_name": "hydrate_refined_iceberg_3m",
                "engine_type": "apache_airflow",
                "engine_workflow_id": "hydrate_refined_iceberg_3m",
                "config": {
                    "dataset_code": "CFPB",
                    "dataset_slice": "3m",
                    "lakehouse_zone": "refined",
                },
                "enabled": True,
                "created_at": NOW_M51,
                "updated_at": NOW_M51,
            }
        )
    )
    _upsert(
        MongoDocument(
            {
                "_collection": "mios_workflows",
                "id": MW_3M_HYDRATE_REFINED_ID,
                "mio_id": MIO_3_MONTHS_ID,
                "workflow_id": HYDRATE_REFINED_ICEBERG_WF_ID,
                "created_at": NOW_M51,
            }
        )
    )


class _M51HydrateSeed(NamedTuple):
    wf_id: str
    bind_id: str
    workflow_name: str
    lakehouse_zone: str


def _ensure_m51_hydrate_workflow(seed: _M51HydrateSeed) -> None:
    _upsert(
        MongoDocument(
            {
                "_collection": "app_workflows",
                "id": seed.wf_id,
                "workflow_name": seed.workflow_name,
                "engine_type": "apache_airflow",
                "engine_workflow_id": seed.workflow_name,
                "config": {
                    "dataset_code": "CFPB",
                    "dataset_slice": "3m",
                    "lakehouse_zone": seed.lakehouse_zone,
                },
                "enabled": True,
                "created_at": NOW_M51,
                "updated_at": NOW_M51,
            }
        )
    )
    _upsert(
        MongoDocument(
            {
                "_collection": "mios_workflows",
                "id": seed.bind_id,
                "mio_id": MIO_3_MONTHS_ID,
                "workflow_id": seed.wf_id,
                "created_at": NOW_M51,
            }
        )
    )


def bootstrap_operational_mongo() -> None:
    ensure_indexes()
    seed_if_empty()
    ensure_m51_hydrate_raw_iceberg_seed()
    ensure_m51_hydrate_refined_iceberg_seed()
    _ensure_m51_hydrate_workflow(
        _M51HydrateSeed(
            HYDRATE_TAXONOMY_WF_ID,
            MW_3M_HYDRATE_TAXONOMY_ID,
            "hydrate_taxonomy_mode2_3m",
            "taxonomy",
        )
    )
    _ensure_m51_hydrate_workflow(
        _M51HydrateSeed(
            HYDRATE_CURATED_WF_ID,
            MW_3M_HYDRATE_CURATED_ID,
            "hydrate_curated_iceberg_3m",
            "curated",
        )
    )
    _ensure_m51_hydrate_workflow(
        _M51HydrateSeed(
            HYDRATE_CHROMA_WF_ID,
            MW_3M_HYDRATE_CHROMA_ID,
            "hydrate_chroma_signatures_3m",
            "chroma",
        )
    )


def drop_all_collections() -> None:
    db = get_mongo_db()
    for name in COLLECTIONS:
        db[name].drop()
