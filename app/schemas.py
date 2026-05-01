from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models import MEMBER_COLORS, AssignmentMode, RecurrenceFreq


class TeamMemberOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    color: str
    active: bool


class TeamMemberCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    color: str

    @field_validator("color")
    @classmethod
    def _check_color(cls, v: str) -> str:
        if v not in MEMBER_COLORS:
            raise ValueError(f"color must be one of {MEMBER_COLORS}")
        return v


class ChoreBase(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=2000)
    recurrence_freq: RecurrenceFreq
    start_date: date
    assignment_mode: AssignmentMode
    pinned_member_id: int | None = None
    rotation_order: list[int] | None = None

    @model_validator(mode="after")
    def _check_assignment(self) -> "ChoreBase":
        if self.assignment_mode == AssignmentMode.PINNED:
            if self.pinned_member_id is None:
                raise ValueError("pinned_member_id required when assignment_mode is pinned")
        elif self.assignment_mode == AssignmentMode.ROUND_ROBIN:
            if not self.rotation_order:
                raise ValueError("rotation_order required when assignment_mode is round_robin")
        return self


class ChoreCreate(ChoreBase):
    pass


class ChoreUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    recurrence_freq: RecurrenceFreq | None = None
    start_date: date | None = None
    assignment_mode: AssignmentMode | None = None
    pinned_member_id: int | None = None
    rotation_order: list[int] | None = None


class ChoreOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    recurrence_freq: RecurrenceFreq
    start_date: date
    assignment_mode: AssignmentMode
    pinned_member_id: int | None
    rotation_order: list[int] | None
    active: bool


class OccurrenceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    chore_id: int
    chore_title: str
    scheduled_date: date
    assigned_member_id: int | None
    assigned_member_name: str | None
    assigned_member_color: str | None
    completed_at: datetime | None
    completed_by_member_id: int | None


class ReassignBody(BaseModel):
    member_id: int
