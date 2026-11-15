# M03-0017 — TailAdmin Free Admin shell + Home ops dashboard

**Story:** #139 · **Decision:** D83

## Problem

Able Pro restyles (#135, #137) kept iterating on heritage Admin CSS. Home still exposed scaffold `apiBaseUrl`. The approved visual source of truth is **TailAdmin Angular Free**.

## Approach

1. Replace `Portals/consumer-complaints-admin` with MIT [TailAdmin/free-angular-tailwind-dashboard](https://github.com/TailAdmin/free-angular-tailwind-dashboard).
2. Port only CCAA API modules (`src/app/core/*` HTTP helpers), `environments`, and `proxy.conf.json`.
3. Do **not** copy legacy `.cca-*` HTML/CSS or `shared/ui`.
4. Home: KPI cards from `GET /mios/status`; CTA to Imports; never show API base URL.
5. Imports: TailAdmin components + existing `data-testid`s and live Middleware behavior.

## Attribution

`Portals/consumer-complaints-admin/TAILADMIN-LICENSE.md` (MIT).
