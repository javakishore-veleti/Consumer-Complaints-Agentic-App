"""Datasets, stages and usecases (DESIGN.md, sections 3 and 4.1).

A usecase is a fixed name that maps to exactly one system_datasets row (dataset + stage). It is also the value of
data_ingest_log.purpose.
"""

from app.core.common.data_ingest_constants import STATUS_COMPLETED, STATUS_FAILED, STATUS_REQUESTED, STATUS_STARTED

DATASET_3_MONTHS = "3_months"
DATASET_ALL = "all"

STAGE_DOWNLOAD = "download"
STAGE_DB_INGEST = "db_ingest"

USECASE_DOWNLOAD_3_MONTHS = "download_3_months"
USECASE_DOWNLOAD_ALL = "download_all"
USECASE_INGEST_3_MONTHS = "ingest_3_months"
USECASE_INGEST_ALL = "ingest_all"

# usecase -> (dataset, stage)
USECASES = {
    USECASE_DOWNLOAD_3_MONTHS: (DATASET_3_MONTHS, STAGE_DOWNLOAD),
    USECASE_DOWNLOAD_ALL: (DATASET_ALL, STAGE_DOWNLOAD),
    USECASE_INGEST_3_MONTHS: (DATASET_3_MONTHS, STAGE_DB_INGEST),
    USECASE_INGEST_ALL: (DATASET_ALL, STAGE_DB_INGEST),
}
DOWNLOAD_USECASES = (USECASE_DOWNLOAD_3_MONTHS, USECASE_DOWNLOAD_ALL)

# What the portal shows. A value, not a boolean: it must tell the four states apart.
DATASET_NOT_STARTED = "not_started"
DATASET_RUNNING = "running"
DATASET_COMPLETED = "completed"
DATASET_FAILED = "failed"
VALID_DATASET_STATUSES = (DATASET_NOT_STARTED, DATASET_RUNNING, DATASET_COMPLETED, DATASET_FAILED)

# data_ingest_log.status -> system_datasets.status
DATASET_STATUS_OF_LOG_STATUS = {
    STATUS_REQUESTED: DATASET_RUNNING,
    STATUS_STARTED: DATASET_RUNNING,
    STATUS_COMPLETED: DATASET_COMPLETED,
    STATUS_FAILED: DATASET_FAILED,
}

# service operations (the service sets one on ctx.operation, like the facades do)
OP_REQUEST = "request"
OP_RECORD = "record"
