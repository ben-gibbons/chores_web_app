from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import AssignmentMode, Chore, TeamMember
from app.schemas import ChoreCreate, ChoreOut, ChoreUpdate
from app.services.scheduler import drop_future_uncompleted

router = APIRouter(prefix="/api/chores", tags=["chores"])


def _validate_member_refs(
    db: Session,
    pinned_member_id: int | None,
    rotation_order: list[int] | None,
) -> None:
    ids: set[int] = set()
    if pinned_member_id is not None:
        ids.add(pinned_member_id)
    if rotation_order:
        ids.update(rotation_order)
    if not ids:
        return
    found = db.execute(
        select(TeamMember.id).where(TeamMember.id.in_(ids), TeamMember.active.is_(True))
    ).scalars().all()
    missing = ids - set(found)
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown or inactive team member ids: {sorted(missing)}",
        )


@router.get("", response_model=list[ChoreOut])
def list_chores(db: Session = Depends(get_session)) -> list[Chore]:
    rows = db.execute(
        select(Chore).where(Chore.active.is_(True)).order_by(Chore.title)
    ).scalars().all()
    return list(rows)


@router.post("", response_model=ChoreOut, status_code=status.HTTP_201_CREATED)
def create_chore(body: ChoreCreate, db: Session = Depends(get_session)) -> Chore:
    _validate_member_refs(db, body.pinned_member_id, body.rotation_order)
    chore = Chore(
        title=body.title.strip(),
        description=body.description,
        recurrence_freq=body.recurrence_freq,
        start_date=body.start_date,
        assignment_mode=body.assignment_mode,
        pinned_member_id=body.pinned_member_id
        if body.assignment_mode == AssignmentMode.PINNED
        else None,
        rotation_order=body.rotation_order
        if body.assignment_mode == AssignmentMode.ROUND_ROBIN
        else None,
    )
    db.add(chore)
    db.commit()
    db.refresh(chore)
    return chore


@router.patch("/{chore_id}", response_model=ChoreOut)
def update_chore(
    chore_id: int, body: ChoreUpdate, db: Session = Depends(get_session)
) -> Chore:
    chore = db.get(Chore, chore_id)
    if chore is None or not chore.active:
        raise HTTPException(status_code=404, detail="Chore not found")

    data = body.model_dump(exclude_unset=True)
    if "pinned_member_id" in data or "rotation_order" in data:
        _validate_member_refs(
            db,
            data.get("pinned_member_id", chore.pinned_member_id),
            data.get("rotation_order", chore.rotation_order),
        )

    for field, value in data.items():
        setattr(chore, field, value)

    if chore.assignment_mode == AssignmentMode.PINNED:
        chore.rotation_order = None
    elif chore.assignment_mode == AssignmentMode.ROUND_ROBIN:
        chore.pinned_member_id = None

    drop_future_uncompleted(db, chore.id)
    db.commit()
    db.refresh(chore)
    return chore


@router.delete("/{chore_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_chore(chore_id: int, db: Session = Depends(get_session)) -> None:
    chore = db.get(Chore, chore_id)
    if chore is None or not chore.active:
        raise HTTPException(status_code=404, detail="Chore not found")
    chore.active = False
    drop_future_uncompleted(db, chore.id)
    db.commit()
