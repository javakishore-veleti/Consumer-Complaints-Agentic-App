from abc import abstractmethod

from app.core.common.dtos.query_ast_dtos import QueryAstCtx
from app.core.common.singleton import SingletonMeta


class QueryAstService(metaclass=SingletonMeta):
    @abstractmethod
    def run(self, ctx: QueryAstCtx) -> int: ...
