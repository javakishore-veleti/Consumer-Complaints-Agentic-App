# M02-0030 (#80) Object factory `init()` and bean registry (D45)

Decisions: D4, D25, D26, D31, D45, D52, D54 in `Middleware/ConsumerComplaintsHandsOn/DESIGN.md`. Decided without the user present (D54 MVP); review and reverse if needed. No new DESIGN.md decision number.

## Goal

A small shared bean registry in `app/core/common`, and an `init()` on every package `objects_factory`, called once from `main` at startup (and safe to call twice). Lookups are deterministic: one registered implementation → that instance; several → a list in registration order. Duplicate registration raises. Call sites keep using `get_*()`; those methods become thin wrappers over the registry after `init()`.

## Approaches considered

| | Approach | Trade-off |
|---|---|---|
| A (chosen) | Shared `BeanRegistry` + `init()` on all four factories now; `get_*` auto-calls `init()` if needed; `main` calls inits in dependency order | Meets #80 acceptance; existing tests keep working; one cutover with clear tests |
| B | Registry only + `init()` on one package (e.g. services) as a demo | Leaves `main` half-wired; next stories re-touch every factory; weaker acceptance |
| C | Replace every `get_*` with `registry.get_one(Interface)` at call sites | Large noisy diff; rejects D45 "nothing is retrofitted in one go" for callers |

## Current state (before this story)

| Factory | Pattern today |
|---|---|
| `DaoObjectsFactory` | Lazy `Impl()` per `get_*` (SingletonMeta makes them singletons) |
| `ServicesObjectsFactory` | Same |
| `FacadesObjectsFactory` | Same |
| `ApiObjectsFactory` | Lazy `_app` with a lock; other API beans via `Class()` (SingletonMeta) |
| `main.py` | `app = ApiObjectsFactory.get_app()` only |
| `common/objects_factory.py` | Missing (D4 lists it; out of scope — no common beans yet) |

No multi-impl interface yet. First consumer of `get_all` is story #83 (workflow engines / D52). This story still implements and tests `get_all` on the registry so #83 only registers engines.

## Naming

| What | Name |
|---|---|
| Registry class | `BeanRegistry` in `app/core/common/bean_registry.py` |
| Process-wide instance | module attribute `bean_registry` (one shared registry) |
| Errors | `DuplicateBeanError`, `BeanNotFoundError`, `BeanAmbiguousError` (same module) |
| Factory hook | `XxxObjectsFactory.init() -> None` on dao, services, facades, api |
| Lookups (unchanged names) | existing `get_*` methods |

## Registry API

```python
class BeanRegistry:
    def register(self, interface: type, instance: object) -> None: ...
    def get_one(self, interface: type) -> object: ...   # exactly one; else BeanNotFoundError / BeanAmbiguousError
    def get_all(self, interface: type) -> list[object]: ...  # registration order; empty list if none
```

Rules:

1. **`register`:** appends `instance` under `interface`. Raises `DuplicateBeanError` if that same object (`is`) is already registered for that interface. Different instances under one interface are allowed (multi-impl).
2. **`get_one`:** exactly one → return it; zero → `BeanNotFoundError`; two or more → `BeanAmbiguousError`.
3. **`get_all`:** list in registration order (fixed, deterministic). Empty if none.
4. Thread-safe (`threading.RLock`), so `init()` may nest (a factory may build something that triggers another package's lazy `init()`).
5. Unit tests construct a **fresh** `BeanRegistry()`; factories use the module-level `bean_registry` only.

No `clear()` in production API (YAGNI). Tests that need isolation use a local registry instance.

## Factory `init()` contract

For each of `DaoObjectsFactory`, `ServicesObjectsFactory`, `FacadesObjectsFactory`, `ApiObjectsFactory`:

1. Class flag `_initialized: bool` + class `threading.RLock`.
2. `init()`: if already initialized, return immediately (safe twice). Otherwise, under the lock, construct each known impl (`Impl()` / build FastAPI app), `bean_registry.register(Interface, instance)`, set `_initialized = True`.
3. `get_*()`: if not initialized, call `init()`; then `return bean_registry.get_one(Interface)` (typed with a cast / annotation as today).
4. **No change** to which interfaces exist or which impl class is chosen (still SQLAlchemy DAOs, same facade/service impls). Lazy imports of `impl/` stay inside the factory (D4).

### Init order and `main`

```text
DaoObjectsFactory.init()
ServicesObjectsFactory.init()
FacadesObjectsFactory.init()
ApiObjectsFactory.init()
app = ApiObjectsFactory.get_app()
```

`main.py` runs that sequence (api `init` builds and registers the FastAPI app). Uvicorn still loads `main:app`.

### Api special case

`_build_app` today calls `get_mio_status_api()` / `get_callback_secret_auth()` while building. During `ApiObjectsFactory.init()`, construct and register API beans **first**, then build the app using **local variables** (not `get_*`), then `register(FastAPI, app)`. That avoids re-entrancy through `get_app` while `_initialized` is still false. After init, `get_app()` / `get_*` read the registry.

`FastAPI` is registered by concrete type (it is not a project interface with `SingletonMeta`). Acceptable MVP.

## Compatibility with existing tests

- `test_singletons.py` and every test that calls `get_*` without `main`: still green because `get_*` lazy-inits.
- `test_import_contracts.py` / `lint-imports`: common still depends on no layer; factories still own `impl/` imports. **7 contracts kept.**
- `test_ctx_only_signatures.py`: unchanged (no new multi-arg methods).
- `conftest.py` TestClient: still `ApiObjectsFactory.get_app()`; lazy init is enough. Optional: call the four `init()`s in a session fixture later — not required for MVP.

## Out of scope

- `CommonObjectsFactory` (D4) — no common beans yet.
- Changing call sites away from `get_*`.
- Workflow engine multi-impl registration (#83) — only the registry `get_all` API is ready.
- Resetting `SingletonMeta._instances` or the global registry between tests.
- Dependency-injection frameworks (Spring-like XML/annotations).

## Docs to update when implementing

| File | Change |
|---|---|
| `DESIGN.md` D45 | Mark built by story #80; drop "**Not built yet.**" |
| `ARCHITECTURE.md` § factories | Mention `init()` + shared `bean_registry`; `get_*` remain the public lookups |
| This story's acceptance on #80 | Checked by implementation, not in this design commit |

## Acceptance mapping

| Acceptance | Design |
|---|---|
| Registry returns one instance, or a list in fixed order | `get_one` / `get_all` |
| One-instance lookup with none or several raises; duplicate registration raises | `BeanNotFoundError` / `BeanAmbiguousError` / `DuplicateBeanError` |
| `init()` creates singletons and is safe to call twice | Factory `init()` + `_initialized` |
| `main` calls `init()` at startup | `main.py` sequence above |
| Layering and ctx-only tests stay green | No new layer imports; no new multi-arg methods |
