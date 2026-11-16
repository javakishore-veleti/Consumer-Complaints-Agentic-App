from abc import abstractmethod

from app.core.common.dtos.intellect_query_dtos import IntellectQueryCtx
from app.core.common.singleton import SingletonMeta


class IntellectQueryService(metaclass=SingletonMeta):
    @abstractmethod
    def query(self, ctx: IntellectQueryCtx) -> int: ...
