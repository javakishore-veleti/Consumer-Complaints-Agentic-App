# M03-0010 (#120) Lite local runtime profiles — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** SQLite-lite default container set (Airflow only); Postgres and Mongo opt-in via npm/docker profiles; document sets; leave `local:containers:all:*` intact.

**Architecture:** Machine-readable `CICD/Local/profiles.map` drives bash helpers and a small pytest. Existing `docker-all-*.sh` gain `--profile`; new `CICD/Local/postgres` compose for operational CCA Postgres (D77/D78).

**Tech Stack:** bash, docker compose, npm scripts, pytest.

Spec: `docs/Superpowers/specs/M03-0010-local-runtime-profiles-design.md`. Decision: **D78**.

## Global Constraints

- Do not change no-args behavior of `local:containers:all:*`.
- Do not implement Mongo DAO (#119). Touch `.env.example` only with additive profile-script comments (parallel #119).
- Commit with `/ccaa-commit-push 120`. Author `javakishore-veleti`; strip AI trailers.
- Next free decision **D79+**.

## File Structure

| File | Responsibility |
|---|---|
| Spec + plan under `docs/Superpowers/` | Design / plan |
| `CICD/Local/profiles.map` | profile → space-separated services |
| `CICD/Local/docker-profiles.sh` | parse map; resolve `--profile` |
| `CICD/Local/docker-all-{up,down,status}.sh` | honor `--profile` |
| `CICD/Local/postgres/docker-compose.yaml` | operational Postgres 16 |
| `package.json` | named profile npm scripts |
| `DESIGN.md` / `ARCHITECTURE.md` / `README.md` / `.env.example` | D78 + docs |
| `Middleware/.../tests/test_local_container_profiles.py` | map + script contract |
| `Milestone_03.md` | workflow; next decision D79+ |

---

### Task 1: Spec, plan, D78 docs scaffold

- [x] Write spec + plan; add D78; milestone note D79+.
- [ ] Commit: `M03-0010 #120: document lite runtime profiles (D78)`

### Task 2: profiles.map + scripts + postgres compose (TDD)

- [ ] Add failing `test_local_container_profiles.py` for map contents and `--profile` help/usage.
- [ ] Add `profiles.map`, `docker-profiles.sh`, enhance `docker-all-*.sh`, add `postgres` compose, npm scripts.
- [ ] Green tests; commit: `M03-0010 #120: add sqlite/postgres/mongodb container profiles`

### Task 3: Docs + verify + finish

- [ ] README + ARCHITECTURE container sets; `.env.example` pointer.
- [ ] `npm run local:api:lint` / `npm run local:api:test`.
- [ ] PR → main, merge green, `/ccaa-story-complete 120`, `/ccaa-feature-complete 113`.
