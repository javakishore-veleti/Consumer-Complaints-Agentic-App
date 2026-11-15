# Portals

Browser apps for this repository live under `Portals/<app-name>/` (D65).

| App | Path | Role |
|---|---|---|
| `consumer-complaints-admin` | [`consumer-complaints-admin/`](consumer-complaints-admin/) | Angular admin portal (Imports ↔ live Middleware) |

From the repository root — preferred three-step local stack:

```bash
npm run local:containers:all:start          # Docker deps (or :sqlite:start, …)
npm run local:handson:middlware:all:start   # Middleware API
npm run local:portals:all:start             # every Portals app (today: admin only)
```

Portal umbrella / single-app:

```bash
npm run local:portals:all:start|stop|status
npm run local:portal:admin:start            # admin only (API must already be on :8000)
npm run local:portal:admin:build
npm run local:portal:admin:test
npm run local:portal:admin:with-api         # Middleware then portals:all (shortcut)
```
