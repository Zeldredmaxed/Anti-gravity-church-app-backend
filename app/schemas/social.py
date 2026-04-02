"""Pydantic schemas for social features: followers, mentions, bookmarks, reports."""

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from .user import UserResponse


class FollowerResponse(BaseModel):
    id: int
    follower_id: int
    followed_id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class FollowerListResponse(BaseModel):
    user: UserResponse
    created_at: datetime


class BookmarkResponse(BaseModel):
    id: int
    user_id: int
    entity_type: str
    entity_id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class BookmarkCreate(BaseModel):
    entity_type: str
    entity_id: int


class MentionResponse(BaseModel):
    id: int
    user_id: int
    author_id: int
    entity_type: str
    entity_id: int
    is_read: bool
    created_at: datetime
    author: Optional[UserResponse] = None

    model_config = {"from_attributes": True}


class ReportCreate(BaseModel):
    entity_type: str
    entity_id: int
    reason: str


class ReportResponse(BaseModel):
    id: int
    reporter_id: Optional[int] = None
    entity_type: str
    entity_id: int
    reason: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}
