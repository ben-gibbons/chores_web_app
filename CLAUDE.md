# Office Chore App

Single-machine web app for managing recurring office chores on a calendar. No auth, in-app only. One FastAPI process serves the API and a static TypeScript bundle.

## Tech stack

- **Backend**: Python 3.11+, FastAPI, SQLAlchemy 2.0 (DeclarativeBase + `Mapped` typed columns), Pydantic v2, SQLite, Jinja2.
- **Frontend**: TypeScript (strict, `noUncheckedIndexedAccess`, `verbatimModuleSyntax`), esbuild (IIFE bundle), FullCalendar v6. No UI framework — vanilla DOM.
- **Tests**: pytest for backend, `tsc --noEmit` for frontend type-checking.

## Project layout

```
app/                       FastAPI application
  main.py                  app entry, mounts routers + /static + Jinja templates
  db.py                    engine, SessionLocal, Base, get_session, init_db
  models.py                ORM models: TeamMember, Chore, Occurrence + StrEnums
  schemas.py               Pydantic request/response models
  routers/
    team_members.py        /api/team-members
    chores.py              /api/chores
    occurrences.py         /api/occurrences
  services/
    recurrence.py          pure recurrence date math, no DB
    rotation.py            pure round-robin assignee selection, no DB
    scheduler.py           DB-aware orchestrator: lazy occurrence materialisation
  templates/index.html     Jinja root, loads /static/app.js
  static/                  build output (gitignored: app.js, styles.css)
frontend/                  TypeScript source
  src/main.ts              entry; Calendar setup, list rendering, event wiring
  src/api.ts               typed fetch wrapper + `api` object
  src/modals.ts            modal builders: member / chore / occurrence
  src/types.ts             API shapes mirrored from backend schemas
  src/styles.css           copied to app/static at build time
  build.mjs                esbuild script (writes to ../app/static)
tests/                     pytest tests against pure services
chores.db                  SQLite, created on startup (gitignored)
run.bat                    builds frontend + starts uvicorn on :8000
```

## Build / run / test

```
pip install -r requirements.txt              # one-time
npm --prefix frontend install                 # one-time
run.bat                                       # build frontend, start uvicorn (reload)
npm --prefix frontend run watch               # rebuild frontend on save (separate terminal)
pytest                                        # backend unit tests
npm --prefix frontend run typecheck           # tsc --noEmit
```

The dev server is `uvicorn app.main:app --reload --host 127.0.0.1 --port 8000`. Frontend changes do NOT trigger uvicorn reload — re-run the build (or use `watch`) and refresh the browser.

## Domain model (one-line)

A `Chore` carries a recurrence rule and an assignment mode (`pinned` to one member, or `round_robin` over `rotation_order`). `Occurrence` rows are not pre-generated — they're materialised lazily for the date range the calendar requests. Soft-deletes (`active = False`) preserve historical occurrences.

Key files: `app/models.py:36`, `app/services/scheduler.py:26`, `app/routers/occurrences.py:30`.

## Adding New Features or Fixing Bugs

**IMPORTANT**: When you work on a new feature or bug, create a git branch first. Then work on changes in that branch for the remainder of the session.

## Additional documentation

When working on the relevant area, consult:

- **`.claude/docs/architectural_patterns.md`** — Architectural patterns and conventions used across the codebase (layered services, lazy materialisation, soft-delete model, assignment-mode invariants, frontend `api` object pattern, vanilla-DOM modal pattern). Read before adding a new endpoint, service, or frontend feature.
