import logging
import os

from app.core.common.config import get_settings
from app.core.common.dtos.airflow_upsert_secrets_dtos import (
    OUTCOME_MISSING,
    OUTCOME_SKIPPED,
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

_OPTIONAL_MARKER = "# optional"


class AirflowUpsertSecretsServiceImpl(AirflowUpsertSecretsService):
    def upsert(self, ctx: AirflowUpsertSecretsCtx) -> int:
        ctx.resp.results = []
        path = get_settings().airflow_variables_upsert_path
        try:
            # Parse list file here (D37: no helper with bare str/Path). Names after `# optional`
            # are not required (M10-0012 / #219).
            optional = False
            entries: list[tuple[str, bool]] = []
            for line in path.read_text(encoding="utf-8").splitlines():
                raw = line.strip()
                if not raw:
                    continue
                if raw.lower().startswith(_OPTIONAL_MARKER):
                    optional = True
                    continue
                if raw.startswith("#"):
                    continue
                entries.append((raw, not optional))
        except OSError:
            logger.warning("airflow variables upsert failed: list file unreadable")
            ctx.resp.code = FAILURE
            return FAILURE
        present: list[AirflowVariableUpsertItem] = []
        absent: list[UpsertSecretResult] = []
        for name, required in entries:
            value = os.environ.get(name, "").strip()
            if not value:
                outcome = OUTCOME_MISSING if required else OUTCOME_SKIPPED
                absent.append(UpsertSecretResult(name=name, outcome=outcome))
            else:
                present.append(AirflowVariableUpsertItem(name=name, value=value))
        client_ctx = AirflowVariablesUpsertCtx(req=AirflowVariablesUpsertReq(items=present))
        if present:
            code = AirflowVariablesClient().upsert_all(client_ctx)
            if code != SUCCESS:
                ctx.resp.results = list(client_ctx.resp.results) + absent
                ctx.resp.code = FAILURE
                return FAILURE
            ctx.resp.results = list(client_ctx.resp.results) + absent
        else:
            ctx.resp.results = absent
        by_name = {r.name: r for r in ctx.resp.results}
        ctx.resp.results = [by_name[n] for n, _req in entries if n in by_name]
        if any(r.outcome == OUTCOME_MISSING for r in ctx.resp.results):
            ctx.resp.code = FAILURE
            return FAILURE
        ctx.resp.code = SUCCESS
        return SUCCESS
