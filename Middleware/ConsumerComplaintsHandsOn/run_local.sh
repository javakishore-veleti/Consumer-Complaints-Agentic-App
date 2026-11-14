#!/usr/bin/env bash
# Local start: migrate the operational database first, then start the API.
# If the migration fails the API does not start (set -e).
set -euo pipefail
cd "$(dirname "$0")"

uv run alembic upgrade head
exec uv run uvicorn main:app --host 127.0.0.1 --port "${API_PORT:-8000}" --reload
