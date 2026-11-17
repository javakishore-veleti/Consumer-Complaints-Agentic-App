"""Looks up WorkflowEngine by type and starts the run (D73); no engine-specific imports."""

from app.core.common.dtos.start_wf_facade_dtos import StartWfFacadeCtx
from app.core.common.dtos.workflow_engine_dtos import WorkflowEngineCtx, WorkflowEngineReq
from app.core.common.return_codes import INVALID_INPUT
from app.core.facades.start_wf_facade_task import StartWfFacadeTask
from app.core.services.objects_factory import ServicesObjectsFactory


class StartWfTriggerEngineTask(StartWfFacadeTask):
    def execute(self, ctx: StartWfFacadeCtx) -> int:
        execution_id = ctx.resp.execution_id
        engine_type = ctx.resp.engine_type
        if not execution_id or not engine_type:
            ctx.resp.code = INVALID_INPUT
            return INVALID_INPUT
        engine = next(
            (e for e in ServicesObjectsFactory.get_workflow_engines() if e.engine_type == engine_type),
            None,
        )
        if engine is None:
            ctx.resp.code = INVALID_INPUT
            return INVALID_INPUT
        eng_ctx = WorkflowEngineCtx(
            req=WorkflowEngineReq(
                execution_id=execution_id,
                dag_conf=dict(ctx.resp.dag_conf or {}),
            )
        )
        code = engine.start(eng_ctx)
        ctx.resp.code = code
        return code
