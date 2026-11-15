from app.core.common.dtos.app_endpoint_list_facade_dtos import AppEndpointListFacadeCtx
from app.core.facades.app_endpoint_list_facade_task import AppEndpointListFacadeTask
from app.core.services.objects_factory import ServicesObjectsFactory


class AppEndpointListCallServiceTask(AppEndpointListFacadeTask):
    def execute(self, ctx: AppEndpointListFacadeCtx) -> int:
        svc = ServicesObjectsFactory.get_app_endpoint_list_service()
        ctx.service_ctx.req = ctx.req
        if ctx.req.id:
            code = svc.get(ctx.service_ctx)
        else:
            code = svc.list(ctx.service_ctx)
        ctx.resp = ctx.service_ctx.resp
        return code
