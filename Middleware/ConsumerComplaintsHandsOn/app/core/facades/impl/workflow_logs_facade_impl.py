"""WorkflowLogsFacade → service (M55-0012 / #394)."""

from app.core.common.dtos.app_wf_exec_log_dtos import AppWfExecLogCtx
from app.core.facades.workflow_logs_facade import WorkflowLogsFacade
from app.core.services.objects_factory import ServicesObjectsFactory


class WorkflowLogsFacadeImpl(WorkflowLogsFacade):
    def list(self, ctx: AppWfExecLogCtx) -> int:
        return ServicesObjectsFactory.get_workflow_logs_service().list(ctx)
