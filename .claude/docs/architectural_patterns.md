# Architectural Patterns

Patterns and conventions that recur across the codebase. Each entry describes the pattern, where it's used, and (where it matters) why.

---

## 1. Layered backend: routers → services → ORM

Routers are thin. They handle HTTP concerns (Pydantic body validation, status codes, 404s) and either touch the ORM directly for trivial CRUD, or delegate to a service for anything involving multiple rows or domain logic.

- Router examples: `app/routers/chores.py:38`, `app/routers/team_members.py:15`, `app/routers/occurrences.py:30`.
- Service entry points called from routers: `ensure_occurrences` (`app/services/scheduler.py:26`), `reassign_orphaned` (`app/services/scheduler.py:72`), `drop_future_uncompleted` (`app/services/scheduler.py:103`).

When adding an endpoint: if the work touches more than one resource, has side effects on `Occurrence`, or involves date arithmetic, put the logic in `app/services/` and call it from the router.

---

## 2. Pure-function services + a DB-aware orchestrator

`app/services/` is split deliberately:

- **Pure** (no DB, no I/O, take primitives, return primitives): `app/services/recurrence.py:1`, `app/services/rotation.py:1`. Both files literally start with a docstring stating "No DB access."
- **DB-aware orchestrator**: `app/services/scheduler.py` is the only service that takes a `Session` and composes the pure functions.

This split is why `tests/test_recurrence.py` and `tests/test_rotation.py` need no fixtures. Preserve it: do not import `Session` or query in `recurrence.py` / `rotation.py`. New pure logic goes alongside them; new DB-aware logic goes in `scheduler.py` (or a sibling).

---

## 3. Lazy materialisation of `Occurrence` rows

`Chore` stores the recurrence rule. `Occurrence` rows are NOT pre-generated. They're created on demand the first time a calendar fetch covers their date.

- Read path: `app/routers/occurrences.py:39` calls `ensure_occurrences` for every active chore over `[start, end]` before returning the listing.
- Write path: `ensure_occurrences` (`app/services/scheduler.py:26`) computes expected dates via `dates_in_range`, diffs against existing rows for that chore in those dates, inserts the missing ones with assignees picked at insertion time.

Implication: editing a chore's recurrence rule must invalidate future uncompleted occurrences so they get re-materialised with the new rule. That's `drop_future_uncompleted` (`app/services/scheduler.py:103`), called from `update_chore` and `delete_chore` (`app/routers/chores.py:92`, `:104`).

When adding a chore-edit feature: if the change affects future occurrences, call `drop_future_uncompleted` after the mutation, before commit.

---

## 4. Soft delete via `active: bool`

`TeamMember.active` (`app/models.py:41`) and `Chore.active` (`app/models.py:58`) are the deletion mechanism. Hard deletes would orphan or destroy historical `Occurrence` rows that the calendar still needs to render past completions.

Conventions:

- All list queries filter on `active.is_(True)` — see `app/routers/chores.py:41`, `app/routers/team_members.py:18`, `app/routers/occurrences.py:39`.
- Delete endpoints set `active = False` and then trigger cleanup: `reassign_orphaned` for members (`app/routers/team_members.py:39`), `drop_future_uncompleted` for chores (`app/routers/chores.py:104`).
- `Occurrence` has no `active` flag — completion state (`completed_at`) is the historical record; future uncompleted rows are simply deleted when the parent rule changes.

When adding a query that lists chores or members: filter on `active`. When adding a delete endpoint for a parent entity: decide what happens to its dependent occurrences and route through `scheduler.py`.

---

## 5. Assignment-mode invariant: exactly one of `pinned_member_id` / `rotation_order`

`Chore.assignment_mode` is a `StrEnum` (`PINNED` or `ROUND_ROBIN`). The two fields are mutually exclusive and the invariant is enforced at three layers:

1. **Pydantic input validation**: `ChoreBase` model_validator at `app/schemas.py:31` rejects payloads missing the field required by the chosen mode.
2. **Router normalisation on create**: `app/routers/chores.py:55` nulls out the unused field at insertion.
3. **Router normalisation on update**: `app/routers/chores.py:87` re-applies the invariant after applying the patch, regardless of which fields the client sent.
4. **Service consumption**: `ensure_occurrences` branches on `assignment_mode` (`app/services/scheduler.py:53`) — it trusts the invariant and reads only the relevant field.

When adding a new assignment mode or editing this area: update all four sites. Don't read the "other" field defensively in services — fix the invariant instead.

---

## 6. StrEnum persisted as `String` column

`RecurrenceFreq` and `AssignmentMode` (`app/models.py:20`, `:27`) are `StrEnum`, stored as `String(16)` (`app/models.py:51`, `:53`). Wire format is the string value; the frontend declares matching string-literal unions (`frontend/src/types.ts:1`).

When adding a new enum: use `StrEnum`, persist as `String`, mirror as a string-literal union in `frontend/src/types.ts`. Don't introduce integer enums or a separate lookup table.

---

## 7. Pydantic `from_attributes=True` for response models

Output schemas use `model_config = ConfigDict(from_attributes=True)` (`app/schemas.py:11`, `:57`, `:71`) so routers return ORM instances directly and FastAPI serialises them via `response_model`. The router-level return type can be the SQLAlchemy model — see `def list_chores(...) -> list[Chore]` at `app/routers/chores.py:39`.

`OccurrenceOut` is the exception: it includes denormalised `chore_title` and `assigned_member_name`, so the router builds it explicitly via `_serialize` (`app/routers/occurrences.py:17`) rather than returning the ORM object.

When adding a response schema: use `from_attributes=True` and return the ORM instance — unless you need to denormalise across joined entities, in which case build a small `_serialize` helper in the router.

---

## 8. Session-per-request via `Depends(get_session)`

`app/db.py:23` defines `get_session` as a generator dependency. Every router endpoint takes `db: Session = Depends(get_session)`. Sessions are configured `autoflush=False, expire_on_commit=False` (`app/db.py:16`) — the latter matters because routers `db.refresh(...)` and then return the instance for serialisation; expiring on commit would re-fetch.

Don't open ad-hoc sessions in services. Services accept a `Session` parameter and the caller (router) provides it.

---

## 9. Frontend: single typed `request<T>` + named `api` object

All HTTP goes through one place. `frontend/src/api.ts:3` defines a generic `request<T>` that handles JSON headers, error mapping, and the 204 case. `frontend/src/api.ts:16` exports a single `api` object with one method per endpoint. UI code (`main.ts`, `modals.ts`) imports `api` and never calls `fetch` directly.

When adding an endpoint: add a method to the `api` object, mirror the request/response in `frontend/src/types.ts`. Never sprinkle raw `fetch` into UI files.

---

## 10. Vanilla-DOM UI with imperative builders

No framework. All DOM is constructed with `document.createElement`, attributes set imperatively, listeners added inline. Patterns:

- **List rendering**: clear container's `innerHTML`, loop, append. Examples: `frontend/src/main.ts:32` (`renderMembers`), `:68` (`renderChores`).
- **Module-level cache + refresh functions**: `cachedMembers` / `cachedChores` are module-level in `main.ts`; `refreshMembers` / `refreshChores` reload from the API and re-render. After a mutation, call the relevant refresh and (if calendar-visible) `calendar?.refetchEvents()`.
- **Modals**: each modal is a function that takes data + a callback, builds a form, mounts into `#modal-root`. See `memberModal`, `choreModal`, `occurrenceModal` in `frontend/src/modals.ts`. Shared helpers at the top of the file: `open` (`:18`), `close` (`:11`), `makeButton` (`:35`), `makeField` (`:43`).

When adding UI: follow the imperative builder style. Don't introduce React/Preact/lit-html — `frontend/package.json` deliberately keeps `preact` as a transitive dep only. If you need a new modal, write a `xxxModal(data, onSubmit)` function in `modals.ts` reusing `makeField` / `makeButton` / `open` / `close`.

---

## 11. Frontend types mirror backend schemas manually

`frontend/src/types.ts` hand-declares interfaces matching `app/schemas.py` output models. There's no codegen.

When changing a Pydantic response schema: update `frontend/src/types.ts` in the same change. `npm --prefix frontend run typecheck` will catch most mismatches at the call sites in `api.ts` / `main.ts` / `modals.ts`.

---

## 12. Frontend strict-mode discipline

`tsconfig.json` enables `strict`, `noUncheckedIndexedAccess`, `noImplicitOverride`, `noFallthroughCasesInSwitch`, `verbatimModuleSyntax`. Practical consequences visible in the code:

- Array index access yields `T | undefined`. Guard with `=== undefined` rather than `!`. See the rotation reorder handlers (`frontend/src/modals.ts:182`, `:191`).
- Type-only imports must use `import type` (`verbatimModuleSyntax`). See the imports in `frontend/src/api.ts:1` and `frontend/src/main.ts:8`.
- Imports include the `.js` extension even though sources are `.ts` (`moduleResolution: "bundler"` + `verbatimModuleSyntax`). Match the existing pattern.

---

## 13. Build output flows from `frontend/` into `app/static/`

`frontend/build.mjs:7` writes the bundle to `../app/static/app.js` and copies `src/styles.css` alongside. `app/static/` is gitignored. `app/main.py:21` mounts it at `/static`; the Jinja template references `/static/app.js` and `/static/styles.css`.

Implication: the backend cannot serve a working page without the frontend having been built at least once. `run.bat` enforces this by building before starting uvicorn. CI / fresh checkouts must run the frontend build before `pytest` if any test boots the FastAPI app (current tests don't, but new integration tests would need to).
