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


def _callback_request(
    path: str,
    body: dict[str, Any],
    *,
    method: str = "POST",
    api_base_url: str | None = None,
    callback_secret: str | None = None,
    urlopen: Callable[..., Any] = urllib.request.urlopen,
    getenv: Callable[..., str | None] = os.getenv,
    get_variable: Callable[[str], str] | None = None,
) -> dict[str, Any]:
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

    url = f"{base}{path}"
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Content-Type": "application/json",
            "X-Callback-Secret": str(secret).strip(),
        },
    )
    try:
        with urlopen(req, timeout=30) as resp:
            code = getattr(resp, "getcode", lambda: 200)()
            raw = resp.read() if hasattr(resp, "read") else b"{}"
            if code is not None and int(code) >= 400 and int(code) != 409:
                raise CallbackHttpError(f"callback HTTP {code}", status_code=int(code))
            if not raw:
                return {}
            return json.loads(raw.decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 409:
            return {}
        raise CallbackHttpError(f"callback HTTP {e.code}", status_code=e.code) from e


def task_instance_for(context: dict[str, Any], task_id: str) -> Any | None:
    """Resolve a task instance from DAG context (Airflow 2 + 3).

    Airflow 3 removed ``DagRun.get_task_instance``. Prefer
    ``get_task_instances()`` and fall back to ``get_task_instance`` when present.
    """
    if not task_id or not str(task_id).strip():
        return None
    wanted = str(task_id).strip()
    dag_run = context.get("dag_run")
    if dag_run is None:
        return None

    get_tis = getattr(dag_run, "get_task_instances", None)
    if callable(get_tis):
        try:
            tis = get_tis() or []
        except TypeError:
            # Some signatures require keyword-only args; retry empty.
            try:
                tis = get_tis(state=None) or []
            except Exception:
                tis = []
        except Exception:
            tis = []
        for ti in tis:
            if getattr(ti, "task_id", None) == wanted:
                return ti

    get_ti = getattr(dag_run, "get_task_instance", None)
    if callable(get_ti):
        try:
            return get_ti(wanted)
        except Exception:
            return None
    return None


def _state_is_success(state: Any) -> bool:
    if state is None:
        return False
    text = str(getattr(state, "value", state) or "").strip().lower()
    return text in {"success", "taskinstancestate.success"}


def _xcom_indicates_success(context: dict[str, Any], task_id: str) -> bool:
    """Airflow 3 worker fallback: successful PythonOperators push a return XCom.

    Our CCAA work tasks always return a non-None value on success. Failed tasks
    do not push return_value, so ``xcom_pull`` is ``None``.
    """
    current = context.get("ti")
    if current is None or not hasattr(current, "xcom_pull"):
        return False
    wanted = str(task_id).strip()
    for tids in (wanted, [wanted]):
        try:
            value = current.xcom_pull(task_ids=tids, key="return_value")
        except TypeError:
            try:
                value = current.xcom_pull(task_ids=tids)
            except Exception:
                value = None
        except Exception:
            value = None
        if value is not None:
            return True
    return False


def _ti_state_from_orm(context: dict[str, Any], task_id: str) -> Any | None:
    """Airflow 3: DagRun.get_task_instances() is often empty in the task SDK.

    Read TaskInstance.state from the metadata DB when context TI/XCom are inconclusive
    (M17-0011 / #260 — wrapper finalize false-failed with state=None).
    """
    wanted = str(task_id).strip()
    if not wanted:
        return None
    dag_run = context.get("dag_run")
    dag_id = getattr(dag_run, "dag_id", None) if dag_run is not None else None
    run_id = context.get("run_id")
    if run_id is None and dag_run is not None:
        run_id = getattr(dag_run, "run_id", None)
    if not dag_id or run_id is None or not str(run_id).strip():
        return None
    try:
        from airflow.models.taskinstance import TaskInstance
        from airflow.utils.session import create_session
    except Exception:
        return None
    try:
        with create_session() as session:
            ti = (
                session.query(TaskInstance)
                .filter(
                    TaskInstance.dag_id == str(dag_id),
                    TaskInstance.run_id == str(run_id),
                    TaskInstance.task_id == wanted,
                )
                .one_or_none()
            )
            if ti is None:
                return None
            return getattr(ti, "state", None)
    except Exception:
        return None


def upstream_succeeded(context: dict[str, Any], task_id: str) -> bool:
    """True when the named upstream task succeeded (TI state, XCom, or ORM)."""
    ti = task_instance_for(context, task_id)
    if ti is not None:
        state = getattr(ti, "state", None)
        if state is not None:
            return _state_is_success(state)
        # TI row present but state unloaded (common in Airflow 3 task SDK).
        if _xcom_indicates_success(context, task_id):
            return True
        orm_state = _ti_state_from_orm(context, task_id)
        if orm_state is not None:
            return _state_is_success(orm_state)
        return False
    if _xcom_indicates_success(context, task_id):
        return True
    orm_state = _ti_state_from_orm(context, task_id)
    if orm_state is not None:
        return _state_is_success(orm_state)
    return False


def _execution_id_from_context(context: dict[str, Any]) -> str | None:
    conf: dict[str, Any] = {}
    dag_run = context.get("dag_run")
    if dag_run is not None:
        raw = getattr(dag_run, "conf", None) or {}
        if isinstance(raw, dict):
            conf.update(raw)
    params = context.get("params") or {}
    if isinstance(params, dict):
        conf.update(params)
    dag_run_conf = context.get("dag_run_conf") or {}
    if isinstance(dag_run_conf, dict):
        conf.update(dag_run_conf)
    value = conf.get("execution_id")
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _engine_run_id_from_context(context: dict[str, Any]) -> str | None:
    run_id = context.get("run_id")
    if run_id is not None and str(run_id).strip():
        return str(run_id).strip()
    dag_run = context.get("dag_run")
    if dag_run is not None:
        rid = getattr(dag_run, "run_id", None)
        if rid is not None and str(rid).strip():
            return str(rid).strip()
    return None


def notify_execution_finished(
    context: dict[str, Any],
    work_task_id: str,
    *,
    execution_id: str | None = None,
    engine_run_id: str | None = None,
    completed_kwargs: dict[str, Any] | None = None,
    report: Callable[..., Any] = report_execution_status,
) -> None:
    """Report completed/failed for a DAG run without Airflow-2-only APIs.

    Always attempts a callback when ``execution_id`` is present. Uses
    :func:`task_instance_for` so finalize never raises ``AttributeError`` on
    Airflow 3 ``DagRun`` objects that lack ``get_task_instance``.
    """
    exec_id = execution_id if execution_id is not None else _execution_id_from_context(context)
    if not exec_id:
        return
    eng = engine_run_id if engine_run_id is not None else _engine_run_id_from_context(context)
    ok = upstream_succeeded(context, work_task_id)
    if ok:
        payload: dict[str, Any] = {}
        if completed_kwargs:
            payload.update(completed_kwargs)
        report(exec_id, "completed", engine_run_id=eng, **payload)
        return
    upstream = task_instance_for(context, work_task_id)
    state = getattr(upstream, "state", None) if upstream is not None else None
    if state is None:
        state = _ti_state_from_orm(context, work_task_id)
    report(
        exec_id,
        "failed",
        engine_run_id=eng,
        message=f"{work_task_id} did not succeed (state={state})",
    )


def report_import_run_create(
    payload: dict[str, Any],
    **kwargs: Any,
) -> dict[str, Any]:
    """POST /callbacks/dataset-import-runs — register a staging/landed import run."""
    return _callback_request("/callbacks/dataset-import-runs", payload, method="POST", **kwargs)


def report_import_run_update(
    import_id: str,
    payload: dict[str, Any],
    **kwargs: Any,
) -> dict[str, Any]:
    """PATCH /callbacks/dataset-import-runs/{id} — finalize status / part_count."""
    if not import_id or not str(import_id).strip():
        raise ValueError("import_id is required")
    return _callback_request(
        f"/callbacks/dataset-import-runs/{str(import_id).strip()}",
        payload,
        method="PATCH",
        **kwargs,
    )
