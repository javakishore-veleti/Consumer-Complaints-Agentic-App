from abc import abstractmethod

from app.core.common.dtos.app_endpoint_list_facade_dtos import AppEndpointListFacadeCtx
from app.core.common.singleton import SingletonMeta


class AppEndpointListFacade(metaclass=SingletonMeta):
    @abstractmethod
    def list(self, ctx: AppEndpointListFacadeCtx) -> int: ...

    @abstractmethod
    def get(self, ctx: AppEndpointListFacadeCtx) -> int: ...
