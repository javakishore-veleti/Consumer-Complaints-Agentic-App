"""Allowed values for data_ingest_log.status."""

STATUS_REQUESTED = "requested"
STATUS_STARTED = "started"
STATUS_COMPLETED = "completed"
STATUS_FAILED = "failed"

VALID_STATUSES = (STATUS_REQUESTED, STATUS_STARTED, STATUS_COMPLETED, STATUS_FAILED)
FINISHED_STATUSES = (STATUS_COMPLETED, STATUS_FAILED)

# Allowed status changes. The same status again is accepted and changes nothing (Airflow retries callbacks).
# completed and failed are final.
ALLOWED_TRANSITIONS = {
    STATUS_REQUESTED: (STATUS_STARTED, STATUS_FAILED),
    STATUS_STARTED: (STATUS_COMPLETED, STATUS_FAILED),
    STATUS_COMPLETED: (),
    STATUS_FAILED: (),
}

DEFAULT_LIST_LIMIT = 100
MAX_LIST_LIMIT = 500

# Operations of the data ingest facade; the facade sets one on ctx.operation before it runs its tasks.
OP_CREATE = "create"
OP_GET = "get"
OP_LIST = "list"
OP_UPDATE = "update"
OP_DELETE = "delete"
