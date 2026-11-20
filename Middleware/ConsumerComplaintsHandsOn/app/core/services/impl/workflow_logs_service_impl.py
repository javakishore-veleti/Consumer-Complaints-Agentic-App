"""WorkflowLogsService → exec-log DAO (M55-0012 / #394)."""

from app.core.common.dtos.app_wf_exec_log_dtos import AppWfExecLogCtx
from app.core.dao.objects_factory import DaoObjectsFactory
from app.core.services.workflow_logs_service import WorkflowLogsService


class WorkflowLogsServiceImpl(WorkflowLogsService):
    def list(self, ctx: AppWfExecLogCtx) -> int:
        return DaoObjectsFactory.get_app_wf_exec_log_dao().list(ctx)
