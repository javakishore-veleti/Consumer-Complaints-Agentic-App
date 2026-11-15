from abc import abstractmethod

from app.core.common.dtos.app_endpoint_list_dtos import AppEndpointListCtx
from app.core.common.singleton import SingletonMeta


class AppEndpointListService(metaclass=SingletonMeta):
    @abstractmethod
    def list(self, ctx: AppEndpointListCtx) -> int: ...

    @abstractmethod
    def get(self, ctx: AppEndpointListCtx) -> int: ...
