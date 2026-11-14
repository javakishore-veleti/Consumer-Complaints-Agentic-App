"""Thin OpenAI wrappers. Every call reports its tokens to whichever `@step` is running."""
from contextvars import ContextVar
from functools import cache

from openai import OpenAI

from .config import CHAT_MODEL, EMBED_MODEL

usage_log: ContextVar[list | None] = ContextVar("usage_log", default=None)


@cache
def client() -> OpenAI:
    return OpenAI()  # reads OPENAI_API_KEY


def _record(response) -> None:
    log = usage_log.get()
    if log is not None and getattr(response, "usage", None):
        log.append(response.usage.total_tokens)


def chat(system: str, user: str) -> str:
    r = client().chat.completions.create(
        model=CHAT_MODEL, messages=[{"role": "system", "content": system}, {"role": "user", "content": user}])
    _record(r)
    return r.choices[0].message.content.strip()


def parse(system: str, user: str, schema):
    """Structured output: returns an instance of the pydantic `schema`."""
    r = client().chat.completions.parse(
        model=CHAT_MODEL, messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        response_format=schema)
    _record(r)
    return r.choices[0].message.parsed


def embed(texts: list[str], batch: int = 256) -> list[list[float]]:
    out = []
    for i in range(0, len(texts), batch):
        r = client().embeddings.create(model=EMBED_MODEL, input=texts[i:i + batch])
        _record(r)
        out.extend(d.embedding for d in r.data)
    return out
