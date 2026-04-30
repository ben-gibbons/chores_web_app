from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import TeamMember
from app.schemas import TeamMemberCreate, TeamMemberOut
from app.services.scheduler import reassign_orphaned

router = APIRouter(prefix="/api/team-members", tags=["team-members"])


@router.get("", response_model=list[TeamMemberOut])
def list_members(db: Session = Depends(get_session)) -> list[TeamMember]:
    rows = db.execute(
        select(TeamMember).where(TeamMember.active.is_(True)).order_by(TeamMember.name)
    ).scalars().all()
    return list(rows)


@router.post("", response_model=TeamMemberOut, status_code=status.HTTP_201_CREATED)
def create_member(body: TeamMemberCreate, db: Session = Depends(get_session)) -> TeamMember:
    member = TeamMember(name=body.name.strip())
    db.add(member)
    db.commit()
    db.refresh(member)
    return member


@router.delete("/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_member(member_id: int, db: Session = Depends(get_session)) -> None:
    member = db.get(TeamMember, member_id)
    if member is None or not member.active:
        raise HTTPException(status_code=404, detail="Team member not found")
    member.active = False
    db.flush()
    reassign_orphaned(db, member_id)
    db.commit()
