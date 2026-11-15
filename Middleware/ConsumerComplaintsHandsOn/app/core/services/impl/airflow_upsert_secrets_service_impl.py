import logging
import os

from app.core.common.config import get_settings
from app.core.common.dtos.airflow_upsert_secrets_dtos import (
    OUTCOME_MISSING,
    AirflowUpsertSecretsCtx,
    AirflowVariableUpsertItem,
    AirflowVariablesUpsertCtx,
    AirflowVariablesUpsertReq,
    UpsertSecretResult,
)
from app.core.common.return_codes import FAILURE, SUCCESS
from app.core.services.airflow_upsert_secrets_service import AirflowUpsertSecretsService
from app.core.services.impl.airflow_variables_client import AirflowVariablesClient

logger = logging.getLogger(__name__)


class AirflowUpsertSecretsServiceImpl(AirflowUpsertSecretsService):
    def upsert(self, ctx: AirflowUpsertSecretsCtx) -> int:
        ctx.resp.results = []
        path = get_settings().airflow_variables_upsert_path
        try:
            names: list[str] = []
            for line in path.read_text(encoding="utf-8").splitlines():
                text = line.strip()
                if not text or text.startswith("#"):
                    continue
                names.append(text)
        except OSError:
            logger.warning("airflow variables upsert failed: list file unreadable")
            ctx.resp.code = FAILURE
            return FAILURE
        present: list[AirflowVariableUpsertItem] = []
        missing: list[UpsertSecretResult] = []
        for name in names:
            value = os.environ.get(name, "").strip()
            if not value:
                missing.append(UpsertSecretResult(name=name, outcome=OUTCOME_MISSING))
            else:
                present.append(AirflowVariableUpsertItem(name=name, value=value))
        client_ctx = AirflowVariablesUpsertCtx(req=AirflowVariablesUpsertReq(items=present))
        if present:
            code = AirflowVariablesClient().upsert_all(client_ctx)
            if code != SUCCESS:
                ctx.resp.results = list(client_ctx.resp.results) + missing
                ctx.resp.code = FAILURE
                return FAILURE
            ctx.resp.results = list(client_ctx.resp.results) + missing
        else:
            ctx.resp.results = missing
        by_name = {r.name: r for r in ctx.resp.results}
        ctx.resp.results = [by_name[n] for n in names if n in by_name]
        if missing:
            ctx.resp.code = FAILURE
            return FAILURE
        ctx.resp.code = SUCCESS
        return SUCCESS
