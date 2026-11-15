from abc import abstractmethod

from app.core.common.dtos.app_endpoint_list_facade_dtos import AppEndpointListFacadeCtx
from app.core.common.singleton import SingletonMeta


class AppEndpointListFacadeTask(metaclass=SingletonMeta):
    @abstractmethod
    def execute(self, ctx: AppEndpointListFacadeCtx) -> int: ...
