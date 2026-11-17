# Milestone M10 - Local stack polish

**Scope:** Local DX after M09 — compose port conflicts and smoke-path friction. Cloud = M90.

**Status: in progress.**

## Build order

| # | Issue | Key | Type | Title |
|---|---|---|---|---|
| 1 | #208 | M10-0001 | Story | Chroma host port default must not collide with Middleware :8000 |
| 2 | #209 | M10-0002 | Story | Bootstrap local Middleware .env for live smoke |

## Notes

- Chroma host default **8100** → container 8000; Middleware stays **8000**.
