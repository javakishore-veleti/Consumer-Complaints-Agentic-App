# Portals

Browser apps for this repository live under `Portals/<app-name>/` (D65).

| App | Path | Role |
|---|---|---|
| `consumer-complaints-admin` | [`consumer-complaints-admin/`](consumer-complaints-admin/) | Angular admin portal (Imports ↔ live Middleware) |

From the repository root:

```bash
npm run local:portal:admin:with-api   # Middleware + portal (one command)
npm run local:portal:admin:start      # portal only (API must already be on :8000)
npm run local:portal:admin:build
npm run local:portal:admin:test
```
