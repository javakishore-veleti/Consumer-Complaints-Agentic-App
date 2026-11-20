"""Service for Admin Workflow Logs list (M55-0012 / #394)."""

from abc import abstractmethod

from app.core.common.dtos.app_wf_exec_log_dtos import AppWfExecLogCtx
from app.core.common.singleton import SingletonMeta


class WorkflowLogsService(metaclass=SingletonMeta):
    @abstractmethod
    def list(self, ctx: AppWfExecLogCtx) -> int: ...
