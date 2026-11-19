from dataclasses import dataclass, field

from app.core.common.dtos.query_ast_dtos import QueryAstReq, QueryAstResp


@dataclass
class QueryAstFacadeCtx:
    req: QueryAstReq = field(default_factory=QueryAstReq)
    resp: QueryAstResp = field(default_factory=QueryAstResp)
