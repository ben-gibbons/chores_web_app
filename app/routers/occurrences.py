from __future__ import annotations

from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import Chore, Occurrence, TeamMember
from app.schemas import OccurrenceOut, ReassignBody
from app.services.scheduler import ensure_occurrences

router = APIRouter(prefix="/api/occurrences", tags=["occurrences"])


def _serialize(occ: Occurrence, chore: Chore, member: TeamMember | None) -> OccurrenceOut:
    return OccurrenceOut(
        id=occ.id,
        chore_id=occ.chore_id,
        chore_title=chore.title,
        scheduled_date=occ.scheduled_date,
        assigned_member_id=occ.assigned_member_id,
        assigned_member_name=member.name if member else None,
        assigned_member_color=member.color if member else None,
        completed_at=occ.completed_at,
        completed_by_member_id=occ.completed_by_member_id,
    )


@router.get("", response_model=list[OccurrenceOut])
def list_occurrences(
    start: date = Query(...),
    end: date = Query(...),
    db: Session = Depends(get_session),
) -> list[OccurrenceOut]:
    if end < start:
        raise HTTPException(status_code=400, detail="end must be >= start")

    chores = db.execute(select(Chore).where(Chore.active.is_(True))).scalars().all()
    for chore in chores:
        ensure_occurrences(db, chore, start, end)
    db.commit()

    rows = db.execute(
        select(Occurrence, Chore, TeamMember)
        .join(Chore, Chore.id == Occurrence.chore_id)
        .outerjoin(TeamMember, TeamMember.id == Occurrence.assigned_member_id)
        .where(Occurrence.scheduled_date >= start, Occurrence.scheduled_date <= end)
        .order_by(Occurrence.scheduled_date)
    ).all()
    return [_serialize(occ, chore, member) for occ, chore, member in rows]


@router.patch("/{occ_id}/complete", response_model=OccurrenceOut)
def mark_complete(occ_id: int, db: Session = Depends(get_session)) -> OccurrenceOut:
    occ = db.get(Occurrence, occ_id)
    if occ is None:
        raise HTTPException(status_code=404, detail="Occurrence not found")
    occ.completed_at = datetime.now(timezone.utc)
    occ.completed_by_member_id = occ.assigned_member_id
    db.commit()
    db.refresh(occ)
    chore = db.get(Chore, occ.chore_id)
    member = (
        db.get(TeamMember, occ.assigned_member_id) if occ.assigned_member_id else None
    )
    assert chore is not None
    return _serialize(occ, chore, member)


@router.delete("/{occ_id}/complete", response_model=OccurrenceOut)
def mark_uncomplete(occ_id: int, db: Session = Depends(get_session)) -> OccurrenceOut:
    occ = db.get(Occurrence, occ_id)
    if occ is None:
        raise HTTPException(status_code=404, detail="Occurrence not found")
    occ.completed_at = None
    occ.completed_by_member_id = None
    db.commit()
    db.refresh(occ)
    chore = db.get(Chore, occ.chore_id)
    member = (
        db.get(TeamMember, occ.assigned_member_id) if occ.assigned_member_id else None
    )
    assert chore is not None
    return _serialize(occ, chore, member)


@router.patch("/{occ_id}/reassign", response_model=OccurrenceOut)
def reassign(
    occ_id: int, body: ReassignBody, db: Session = Depends(get_session)
) -> OccurrenceOut:
    occ = db.get(Occurrence, occ_id)
    if occ is None:
        raise HTTPException(status_code=404, detail="Occurrence not found")
    member = db.get(TeamMember, body.member_id)
    if member is None or not member.active:
        raise HTTPException(status_code=400, detail="Unknown or inactive team member")
    occ.assigned_member_id = body.member_id
    db.commit()
    db.refresh(occ)
    chore = db.get(Chore, occ.chore_id)
    assert chore is not None
    return _serialize(occ, chore, member)
