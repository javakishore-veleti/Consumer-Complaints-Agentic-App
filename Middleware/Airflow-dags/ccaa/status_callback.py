"""POST workflow-execution status callbacks to the API (D59 / D60 / D67)."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any, Callable


class CallbackHttpError(RuntimeError):
    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


def _first_nonblank(*values: str | None) -> str | None:
    for v in values:
        if v is not None and str(v).strip():
            return str(v).strip()
    return None


def resolve_api_base_url(
    *,
    getenv: Callable[..., str | None] = os.getenv,
    get_variable: Callable[[str], str],
) -> str:
    value = _first_nonblank(getenv("CCA_API_URL"), None)
    if value is None:
        try:
            value = _first_nonblank(get_variable("CCA_API_URL"))
        except Exception:
            value = None
    if not value:
        raise ValueError("CCA_API_URL is required (env or Airflow Variable)")
    return value.rstrip("/")


def resolve_callback_secret(
    *,
    getenv: Callable[..., str | None] = os.getenv,
    get_variable: Callable[[str], str],
) -> str:
    value = _first_nonblank(getenv("CCA_CALLBACK_SECRET"), None)
    if value is None:
        try:
            value = _first_nonblank(get_variable("CCA_CALLBACK_SECRET"))
        except Exception:
            value = None
    if not value:
        raise ValueError("CCA_CALLBACK_SECRET is required (env or Airflow Variable)")
    return value


def report_execution_status(
    execution_id: str,
    status: str,
    *,
    engine_run_id: str | None = None,
    message: str | None = None,
    rows_loaded: int | None = None,
    batch_count: int | None = None,
    increment_marker: str | None = None,
    api_base_url: str | None = None,
    callback_secret: str | None = None,
    urlopen: Callable[..., Any] = urllib.request.urlopen,
    getenv: Callable[..., str | None] = os.getenv,
    get_variable: Callable[[str], str] | None = None,
) -> None:
    if not execution_id or not str(execution_id).strip():
        raise ValueError("execution_id is required")
    if status not in ("started", "completed", "failed"):
        raise ValueError(f"unsupported status: {status}")

    if get_variable is None:
        def get_variable(name: str) -> str:  # type: ignore[misc]
            from airflow.models import Variable

            return Variable.get(name)

    base = (api_base_url or resolve_api_base_url(getenv=getenv, get_variable=get_variable)).rstrip("/")
    secret = callback_secret if callback_secret is not None else resolve_callback_secret(
        getenv=getenv, get_variable=get_variable
    )
    if not str(secret).strip():
        raise ValueError("CCA_CALLBACK_SECRET is required (env or Airflow Variable)")

    body: dict[str, Any] = {"status": status}
    if engine_run_id:
        body["engine_run_id"] = str(engine_run_id)[:128]
    if message:
        body["message"] = str(message)
    if rows_loaded is not None:
        body["rows_loaded"] = int(rows_loaded)
    if batch_count is not None:
        body["batch_count"] = int(batch_count)
    if increment_marker is not None and str(increment_marker).strip():
        body["increment_marker"] = str(increment_marker).strip()[:255]

    url = f"{base}/callbacks/workflow-executions/{execution_id}/status"
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "X-Callback-Secret": str(secret).strip(),
        },
    )
    try:
        with urlopen(req, timeout=30) as resp:
            code = getattr(resp, "getcode", lambda: 200)()
            if code is not None and int(code) >= 400 and int(code) != 409:
                raise CallbackHttpError(f"callback HTTP {code}", status_code=int(code))
    except urllib.error.HTTPError as e:
        if e.code == 409:
            return
        raise CallbackHttpError(f"callback HTTP {e.code}", status_code=e.code) from e
