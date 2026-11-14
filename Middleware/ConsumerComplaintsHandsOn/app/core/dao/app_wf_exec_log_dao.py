"""Interface of the DAO for the app_workflows_exec_log table (one DAO per table)."""

from abc import abstractmethod

from app.core.common.dtos.app_wf_exec_log_dtos import AppWfExecLogCtx
from app.core.common.singleton import SingletonMeta


class AppWfExecLogDao(metaclass=SingletonMeta):
    """A singleton (every implementation is). Every method takes one AppWfExecLogCtx and returns an integer code
    (app.core.common.return_codes). Results are written to ctx.resp.records. If ctx.transaction is set, the call
    joins that transaction and the transaction's owner commits.

    The log is append-only: there is no delete. A row keeps the workflow's name, engine type, engine workflow id and
    config as they were when the execution was requested (DESIGN.md D56)."""

    @abstractmethod
    def create(self, ctx: AppWfExecLogCtx) -> int:
        """Needs req.workflow_id. Reads that workflow from app_workflows in the same transaction and copies its
        name, engine type, engine workflow id and config (as config_used) into a new row with the status
        "requested". The new row is returned. INVALID_INPUT without a workflow_id, NOT_FOUND if there is no such
        workflow. Does not look at the workflow's enabled flag."""

    @abstractmethod
    def get(self, ctx: AppWfExecLogCtx) -> int:
        """Needs req.id. INVALID_INPUT if it is missing, NOT_FOUND if there is no such row."""

    @abstractmethod
    def update(self, ctx: AppWfExecLogCtx) -> int:
        """Needs req.id. Changes the given status, engine_run_id (up to 128 characters) and message. The snapshot
        columns are never changed. Status moves follow D30: requested to started or failed, started to completed or
        failed, completed and failed are final, the same status again is accepted and changes nothing. started_at is
        set on the move to started, finished_at on the move to completed or failed. NOT_FOUND if there is no such
        row, INVALID_INPUT for an unknown status or a too long engine_run_id, CONFLICT for any other move; a
        CONFLICT changes nothing."""

    @abstractmethod
    def list(self, ctx: AppWfExecLogCtx) -> int:
        """Optional filters: req.workflow_id, req.status, req.engine_type; optional req.limit and req.offset.
        Newest first (requested_at descending, then id). An empty result is SUCCESS with no records."""
