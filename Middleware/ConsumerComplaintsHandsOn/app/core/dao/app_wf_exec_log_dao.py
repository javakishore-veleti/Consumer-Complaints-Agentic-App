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
