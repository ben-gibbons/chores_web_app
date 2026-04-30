"""Lazy occurrence materialisation: only creates rows when asked."""
from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AssignmentMode, Chore, Occurrence, TeamMember
from app.services.recurrence import dates_in_range
from app.services.rotation import pick_assignee


def _active_member_ids(db: Session) -> set[int]:
    rows = db.execute(select(TeamMember.id).where(TeamMember.active.is_(True))).all()
    return {row[0] for row in rows}


def _occurrence_index(start_date: date, freq: str, target: date) -> int:
    """0-based index of `target` among the chore's occurrences."""
    if target < start_date:
        return 0
    return max(0, len(dates_in_range(freq, start_date, start_date, target)) - 1)


def ensure_occurrences(
    db: Session,
    chore: Chore,
    range_start: date,
    range_end: date,
) -> list[Occurrence]:
    """Generate any missing Occurrence rows for `chore` in the given range."""
    expected = dates_in_range(chore.recurrence_freq, chore.start_date, range_start, range_end)
    if not expected:
        return []

    existing = db.execute(
        select(Occurrence).where(
            Occurrence.chore_id == chore.id,
            Occurrence.scheduled_date.in_(expected),
        )
    ).scalars().all()
    existing_dates = {o.scheduled_date for o in existing}

    missing = [d for d in expected if d not in existing_dates]
    if not missing:
        return list(existing)

    active_ids = _active_member_ids(db)
    new_rows: list[Occurrence] = []
    for d in missing:
        assignee_id: int | None
        if chore.assignment_mode == AssignmentMode.PINNED:
            assignee_id = (
                chore.pinned_member_id if chore.pinned_member_id in active_ids else None
            )
        else:
            idx = _occurrence_index(chore.start_date, chore.recurrence_freq, d)
            assignee_id = pick_assignee(chore.rotation_order or [], idx, active_ids)
        new_rows.append(
            Occurrence(
                chore_id=chore.id,
                scheduled_date=d,
                assigned_member_id=assignee_id,
            )
        )
    db.add_all(new_rows)
    db.flush()
    return list(existing) + new_rows


def reassign_orphaned(db: Session, removed_member_id: int) -> None:
    """After soft-deleting a member, re-pick assignees for their future
    uncompleted occurrences using the current rotation rules."""
    from datetime import date as _date

    today = _date.today()
    active_ids = _active_member_ids(db)
    affected = db.execute(
        select(Occurrence).where(
            Occurrence.assigned_member_id == removed_member_id,
            Occurrence.completed_at.is_(None),
            Occurrence.scheduled_date >= today,
        )
    ).scalars().all()

    for occ in affected:
        chore = db.get(Chore, occ.chore_id)
        if chore is None or not chore.active:
            occ.assigned_member_id = None
            continue
        if chore.assignment_mode == AssignmentMode.PINNED:
            occ.assigned_member_id = (
                chore.pinned_member_id if chore.pinned_member_id in active_ids else None
            )
        else:
            idx = _occurrence_index(chore.start_date, chore.recurrence_freq, occ.scheduled_date)
            occ.assigned_member_id = pick_assignee(
                chore.rotation_order or [], idx, active_ids
            )


def drop_future_uncompleted(db: Session, chore_id: int) -> None:
    """Delete a chore's future, uncompleted occurrences (used on chore delete/edit)."""
    from datetime import date as _date

    today = _date.today()
    db.query(Occurrence).filter(
        Occurrence.chore_id == chore_id,
        Occurrence.completed_at.is_(None),
        Occurrence.scheduled_date >= today,
    ).delete(synchronize_session=False)
