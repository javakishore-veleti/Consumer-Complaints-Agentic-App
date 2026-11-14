"""`@step`: time, count tokens, trace and memoise every function of the pipeline.

Same idea as the notebook's `@step`, without LangSmith:
- saves each result in `experiments/steps.json` with the seconds and tokens it took (a step runs once per input,
  a rerun reads it back, so reruns are free and show the same times);
- appends one line per call to the current question's trace.
"""
import json
import time
from contextlib import nullcontext
from contextvars import ContextVar
from functools import wraps
from threading import Lock

from .config import EXPERIMENTS_DIR, STEPS_PATH
from .llm import usage_log

current_trace: ContextVar[list | None] = ContextVar("current_trace", default=None)
_saved: dict | None = None
_io = Lock()


def saved() -> dict:
    global _saved
    if _saved is None:
        _saved = json.loads(STEPS_PATH.read_text()) if STEPS_PATH.exists() else {}
    return _saved


def save() -> None:
    EXPERIMENTS_DIR.mkdir(exist_ok=True)
    with _io:
        STEPS_PATH.write_text(json.dumps(saved(), ensure_ascii=False))


def reset_memory() -> None:
    """Forget every saved step result (use after changing prompts or the index)."""
    global _saved
    _saved = {}
    STEPS_PATH.unlink(missing_ok=True)


def step(name: str, lock=None):
    def wrap(fn):
        @wraps(fn)
        def run(*args):
            memo = saved().setdefault(name, {})
            key = json.dumps(args, default=str)
            if key not in memo:
                with lock or nullcontext():
                    log = []
                    token = usage_log.set(log)
                    start = time.perf_counter()
                    try:
                        result = fn(*args)
                    finally:
                        usage_log.reset(token)
                    memo[key] = {"result": result, "seconds": round(time.perf_counter() - start, 3),
                                 "tokens": sum(log)}
            hit, trace = memo[key], current_trace.get()
            if trace is not None:
                trace.append({"step": name, "input": " ".join(str(args[0]).split())[:70],
                              "seconds": hit["seconds"], "tokens": hit["tokens"]})
            return hit["result"]
        return run
    return wrap
