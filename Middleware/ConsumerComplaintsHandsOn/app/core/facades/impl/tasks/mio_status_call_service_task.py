"""Hands the read to the service and puts the service's response on the facade ctx."""

from app.core.common.dtos.mio_status_dtos import MioStatusCtx
from app.core.common.dtos.mio_status_facade_dtos import MioStatusFacadeCtx
from app.core.facades.mio_status_facade_task import MioStatusFacadeTask
from app.core.services.objects_factory import ServicesObjectsFactory


class MioStatusCallServiceTask(MioStatusFacadeTask):
    def execute(self, ctx: MioStatusFacadeCtx) -> int:
        ctx.status_ctx = MioStatusCtx(req=ctx.req)
        code = ServicesObjectsFactory.get_mio_status_service().read(ctx.status_ctx)
        ctx.resp = ctx.status_ctx.resp
        return code
