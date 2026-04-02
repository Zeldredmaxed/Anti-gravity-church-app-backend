"""Pydantic schemas for group management."""

from pydantic import BaseModel, model_validator
from typing import Optional, List
from datetime import date, datetime


class GroupCreate(BaseModel):
    name: str
    description: Optional[str] = None
    group_type: Optional[str] = None
    type: Optional[str] = None  # Frontend alias
    leader_id: Optional[int] = None
    meeting_day: Optional[str] = None
    meeting_time: Optional[str] = None
    meeting_location: Optional[str] = None
    max_capacity: Optional[int] = None
    campus: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def normalize_type(cls, values):
        if isinstance(values, dict):
            if not values.get("group_type") and values.get("type"):
                values["group_type"] = values["type"]
            if not values.get("group_type"):
                values["group_type"] = "small_group"
        return values

    def to_db_dict(self):
        return self.model_dump(exclude={"type"}, exclude_none=False)


class GroupUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    group_type: Optional[str] = None
    leader_id: Optional[int] = None
    meeting_day: Optional[str] = None
    meeting_time: Optional[str] = None
    meeting_location: Optional[str] = None
    is_active: Optional[bool] = None
    max_capacity: Optional[int] = None
    campus: Optional[str] = None


class GroupMemberAdd(BaseModel):
    member_id: int
    role: str = "member"


class GroupMemberResponse(BaseModel):
    id: int
    member_id: int
    member_name: Optional[str] = None
    role: str
    joined_date: Optional[date] = None

    model_config = {"from_attributes": True}


class GroupResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    group_type: str
    type: Optional[str] = None  # Mirror of group_type for frontend
    leader_id: Optional[int] = None
    leader_name: Optional[str] = None
    meeting_day: Optional[str] = None
    meeting_time: Optional[str] = None
    meeting_location: Optional[str] = None
    is_active: bool
    max_capacity: Optional[int] = None
    member_count: int = 0
    campus: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}

    @model_validator(mode="before")
    @classmethod
    def populate_type(cls, values):
        if isinstance(values, dict):
            if values.get("group_type") and not values.get("type"):
                values["type"] = values["group_type"]
        return values


class GroupDetailResponse(GroupResponse):
    members: List[GroupMemberResponse] = []
