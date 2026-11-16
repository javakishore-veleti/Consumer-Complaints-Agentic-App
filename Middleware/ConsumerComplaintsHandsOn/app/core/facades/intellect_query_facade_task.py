from abc import abstractmethod

from app.core.common.dtos.intellect_query_facade_dtos import IntellectQueryFacadeCtx
from app.core.common.singleton import SingletonMeta


class IntellectQueryFacadeTask(metaclass=SingletonMeta):
    @abstractmethod
    def execute(self, ctx: IntellectQueryFacadeCtx) -> int: ...
