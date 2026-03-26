"""Pydantic schemas for group management."""

from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime


class GroupCreate(BaseModel):
    name: str
    description: Optional[str] = None
    group_type: str = "small_group"
    leader_id: Optional[int] = None
    meeting_day: Optional[str] = None
    meeting_time: Optional[str] = None
    meeting_location: Optional[str] = None
    max_capacity: Optional[int] = None
    campus: Optional[str] = None


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


class GroupDetailResponse(GroupResponse):
    members: List[GroupMemberResponse] = []
