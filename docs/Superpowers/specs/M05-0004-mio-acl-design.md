# M05-0004 (#165) MIO ACL model and enforce on start

Decision **D89**. Next free: **D90**.

## D89

1. Table `mios_acl` (admin schema): `id`, `mio_id`, `audience` (`internal`|`partner`|`user`), `created_at`; unique `(mio_id, audience)`. No DB FKs (D57).
2. When `POST /workflows/{id}/start` includes `mio_id`, require header **`X-CCA-Audience`** (default `internal` if omitted). Start succeeds only if a matching `mios_acl` row exists. No `mio_id` → no ACL check.
3. Seed: All MIO + 3-months MIO → `internal` (Admin local). Partner/user audiences later.
4. Admin portal sends `X-CCA-Audience: internal` on start.
5. Local only; not real IdP auth.

## Out of scope

Full users DB, SSO, Admin ACL CRUD UI.
