from app.core.common.dtos.dag_context_dtos import DagContextCtx
from app.core.facades.dag_context_facade import DagContextFacade
from app.core.services.objects_factory import ServicesObjectsFactory


class DagContextFacadeImpl(DagContextFacade):
    def get(self, ctx: DagContextCtx) -> int:
        return ServicesObjectsFactory.get_dag_context_service().get(ctx)
