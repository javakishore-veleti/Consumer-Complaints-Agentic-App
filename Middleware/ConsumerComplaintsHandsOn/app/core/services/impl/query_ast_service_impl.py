"""Translate Query AST; optional execute + M54 relaxation (M52-0001 / #352; M54-0001 / #366)."""

from __future__ import annotations

import logging
import os
import re
import subprocess
from typing import NamedTuple

from app.core.common.dtos.query_ast_dtos import QueryAstCtx, QueryAstRelaxStep
from app.core.common.query_ast import (
    AstToSqlReq,
    KAnonReq,
    RelaxAstReq,
    assert_k_anonymous,
    ast_to_sql,
    relax_ast,
)
from app.core.common.return_codes import FAILURE, INVALID_INPUT, SUCCESS
from app.core.services.query_ast_service import QueryAstService

log = logging.getLogger(__name__)


class _ParseCountReq(NamedTuple):
    spark_out: str


class _ContainerRunningReq(NamedTuple):
    container: str


class _SparkCountReq(NamedTuple):
    sql: str
    container: str


def _parse_count(req: _ParseCountReq) -> int:
    spark_out = req.spark_out
    nums = re.findall(r"(?m)^(\d+)\s*$", spark_out)
    if nums:
        return int(nums[-1])
    for line in reversed(spark_out.splitlines()):
        line = line.strip()
        if line.isdigit():
            return int(line)
    raise ValueError(f"could not parse COUNT from spark output:\n{spark_out[-500:]}")


def _container_running(req: _ContainerRunningReq) -> bool:
    try:
        out = subprocess.check_output(
            ["docker", "inspect", "-f", "{{.State.Running}}", req.container],
            text=True,
            stderr=subprocess.DEVNULL,
        )
        return out.strip() == "true"
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def _spark_count(req: _SparkCountReq) -> int:
    out = subprocess.check_output(
        ["docker", "exec", req.container, "spark-sql", "-e", req.sql],
        text=True,
        stderr=subprocess.STDOUT,
    )
    return _parse_count(_ParseCountReq(out))


class QueryAstServiceImpl(QueryAstService):
    def run(self, ctx: QueryAstCtx) -> int:
        ctx.resp.sql = ""
        ctx.resp.executed = False
        ctx.resp.count = None
        ctx.resp.k_anon_ok = None
        ctx.resp.relaxation = []
        ctx.resp.error = ""
        ast = ctx.req.ast
        if not isinstance(ast, dict) or not ast:
            ctx.resp.code = INVALID_INPUT
            ctx.resp.error = "ast is required"
            return INVALID_INPUT
        try:
            sql = ast_to_sql(AstToSqlReq(ast))
        except ValueError as exc:
            ctx.resp.code = INVALID_INPUT
            ctx.resp.error = str(exc)
            return INVALID_INPUT
        ctx.resp.sql = sql

        if ctx.req.relax:
            try:
                steps = relax_ast(RelaxAstReq(ast))
            except ValueError as exc:
                ctx.resp.code = INVALID_INPUT
                ctx.resp.error = str(exc)
                return INVALID_INPUT
            ctx.resp.relaxation = [
                QueryAstRelaxStep(step=s.step, reason=s.reason, sql=s.sql, ast=s.ast) for s in steps
            ]

        if not ctx.req.execute:
            ctx.resp.code = SUCCESS
            return SUCCESS

        container = os.environ.get("CCA_ICEBERG_SPARK_CONTAINER", "cca-spark-iceberg")
        if not _container_running(_ContainerRunningReq(container)):
            ctx.resp.code = FAILURE
            ctx.resp.error = f"warehouse unavailable (container {container} not running)"
            return FAILURE

        candidates: list[tuple[str, dict]] = [(sql, ast)]
        for step in ctx.resp.relaxation:
            candidates.append((step.sql, step.ast))

        last_err = ""
        for cand_sql, cand_ast in candidates:
            try:
                n = _spark_count(_SparkCountReq(sql=cand_sql, container=container))
                assert_k_anonymous(KAnonReq(n))
                ctx.resp.sql = cand_sql
                ctx.resp.count = n
                ctx.resp.k_anon_ok = True
                ctx.resp.executed = True
                ctx.resp.code = SUCCESS
                ctx.req.ast = cand_ast
                return SUCCESS
            except ValueError as exc:
                last_err = str(exc)
                continue
            except Exception:
                log.exception("query-ast execute failed")
                ctx.resp.code = FAILURE
                ctx.resp.error = "execute failed"
                return FAILURE

        ctx.resp.code = INVALID_INPUT
        ctx.resp.error = last_err or "relaxation exhausted without k-anon ok"
        ctx.resp.k_anon_ok = False
        return INVALID_INPUT
