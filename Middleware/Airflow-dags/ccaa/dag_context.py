"""Fetch DAG ops context from Middleware (no direct Postgres)."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Callable

from ccaa.status_callback import (
    CallbackHttpError,
    resolve_api_base_url,
    resolve_callback_secret,
)


def materialize_side(
    side: dict[str, Any],
    *,
    getenv: Callable[..., str | None] = os.getenv,
    get_variable: Callable[[str], str],
) -> dict[str, Any]:
    """Fill env-side values from Airflow env / Variables."""
    out = dict(side)
    if out.get("kind") == "env":
        name = str(out.get("env_var_name") or "").strip()
        if not name:
            raise ValueError("env side missing env_var_name")
        value = (getenv(name) or "").strip()
        if not value:
            try:
                value = str(get_variable(name) or "").strip()
            except Exception:
                value = ""
        if not value:
            raise RuntimeError(f"{name} is not set in the environment or as an Airflow Variable")
        out["value"] = value
    return out


def materialize_app_endpoint(
    payload: dict[str, Any],
    *,
    getenv: Callable[..., str | None] = os.getenv,
    get_variable: Callable[[str], str],
) -> dict[str, Any]:
    return {
        **payload,
        "from": materialize_side(payload["from"], getenv=getenv, get_variable=get_variable),
        "to": materialize_side(payload["to"], getenv=getenv, get_variable=get_variable),
    }


def fetch_dag_context(
    execution_id: str,
    *,
    app_endpoint: str | None = None,
    api_base_url: str | None = None,
    callback_secret: str | None = None,
    urlopen: Callable[..., Any] = urllib.request.urlopen,
    getenv: Callable[..., str | None] = os.getenv,
    get_variable: Callable[[str], str] | None = None,
) -> dict[str, Any]:
    if not execution_id or not str(execution_id).strip():
        raise ValueError("execution_id is required")

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

    path = f"/callbacks/workflow-executions/{urllib.parse.quote(str(execution_id).strip(), safe='')}/dag-context"
    if app_endpoint and str(app_endpoint).strip():
        path += "?" + urllib.parse.urlencode({"app_endpoint": str(app_endpoint).strip()})
    url = f"{base}{path}"
    req = urllib.request.Request(
        url,
        method="GET",
        headers={"X-Callback-Secret": str(secret).strip()},
    )
    try:
        with urlopen(req, timeout=30) as resp:
            code = getattr(resp, "getcode", lambda: 200)()
            raw = resp.read() if hasattr(resp, "read") else b"{}"
            if code is not None and int(code) >= 400:
                raise CallbackHttpError(f"dag-context HTTP {code}", status_code=int(code))
            data = json.loads(raw.decode("utf-8") if raw else "{}")
    except urllib.error.HTTPError as e:
        raise CallbackHttpError(f"dag-context HTTP {e.code}", status_code=e.code) from e

    if not isinstance(data, dict):
        raise ValueError("dag-context response must be an object")
    return data
