from __future__ import annotations

from datetime import date, datetime, timezone
from enum import StrEnum

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class RecurrenceFreq(StrEnum):
    DAILY = "daily"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"


class AssignmentMode(StrEnum):
    PINNED = "pinned"
    ROUND_ROBIN = "round_robin"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TeamMember(Base):
    __tablename__ = "team_members"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)


class Chore(Base):
    __tablename__ = "chores"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(String(2000), default="", nullable=False)
    recurrence_freq: Mapped[RecurrenceFreq] = mapped_column(String(16), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    assignment_mode: Mapped[AssignmentMode] = mapped_column(String(16), nullable=False)
    pinned_member_id: Mapped[int | None] = mapped_column(
        ForeignKey("team_members.id"), nullable=True
    )
    rotation_order: Mapped[list[int] | None] = mapped_column(JSON, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)

    pinned_member: Mapped[TeamMember | None] = relationship(foreign_keys=[pinned_member_id])


class Occurrence(Base):
    __tablename__ = "occurrences"
    __table_args__ = (UniqueConstraint("chore_id", "scheduled_date", name="uq_chore_date"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    chore_id: Mapped[int] = mapped_column(ForeignKey("chores.id"), nullable=False)
    scheduled_date: Mapped[date] = mapped_column(Date, nullable=False)
    assigned_member_id: Mapped[int | None] = mapped_column(
        ForeignKey("team_members.id"), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_by_member_id: Mapped[int | None] = mapped_column(
        ForeignKey("team_members.id"), nullable=True
    )

    chore: Mapped[Chore] = relationship(foreign_keys=[chore_id])
    assigned_member: Mapped[TeamMember | None] = relationship(foreign_keys=[assigned_member_id])
    completed_by_member: Mapped[TeamMember | None] = relationship(
        foreign_keys=[completed_by_member_id]
    )
