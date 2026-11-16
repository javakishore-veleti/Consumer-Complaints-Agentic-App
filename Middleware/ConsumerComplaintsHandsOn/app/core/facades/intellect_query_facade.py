from abc import abstractmethod

from app.core.common.dtos.intellect_query_facade_dtos import IntellectQueryFacadeCtx
from app.core.common.singleton import SingletonMeta


class IntellectQueryFacade(metaclass=SingletonMeta):
    @abstractmethod
    def query(self, ctx: IntellectQueryFacadeCtx) -> int: ...
