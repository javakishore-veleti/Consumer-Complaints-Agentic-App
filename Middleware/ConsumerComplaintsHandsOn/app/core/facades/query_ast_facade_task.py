from abc import abstractmethod

from app.core.common.dtos.query_ast_facade_dtos import QueryAstFacadeCtx
from app.core.common.singleton import SingletonMeta


class QueryAstFacadeTask(metaclass=SingletonMeta):
    @abstractmethod
    def execute(self, ctx: QueryAstFacadeCtx) -> int: ...
