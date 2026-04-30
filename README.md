# Office Chore App

Small web app for the office to manage shared, recurring chores on a calendar. Single-machine, no auth, in-app only.

## Stack

- **Backend:** Python 3.11+, FastAPI, SQLAlchemy, SQLite
- **Frontend:** TypeScript (strict) + esbuild, FullCalendar v6, no UI framework

## One-time setup

```
pip install -r requirements.txt
npm --prefix frontend install
```

## Run

```
run.bat
```

This builds the frontend bundle then starts uvicorn on http://127.0.0.1:8000. The dev server reloads on Python changes; for frontend changes run `npm --prefix frontend run watch` in a second terminal.

## Tests

```
pytest
npm --prefix frontend run typecheck
```

## Features

- Outlook-style month/week/day calendar of chores.
- Add/remove team members.
- Add/remove chores with daily / weekly / biweekly / monthly recurrence.
- Per-chore choice of *pinned to one member* or *auto round-robin* assignment.
- Mark occurrences complete; completed entries appear muted on the calendar.
- Reassign individual occurrences.

## Architecture notes

Chores store the recurrence rule; individual `Occurrence` rows are materialised lazily when the calendar fetches a date range. Editing a chore therefore propagates to future occurrences automatically. Soft-deletes preserve historical calendar entries.
