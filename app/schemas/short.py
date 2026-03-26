"""Shorts system Pydantic schemas."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ShortCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    video_url: str
    thumbnail_url: Optional[str] = None
    duration_seconds: Optional[int] = None
    category: str = "other"
    tags: Optional[list[str]] = []


class ShortUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[list[str]] = None
    is_featured: Optional[bool] = None


class ShortResponse(BaseModel):
    id: int
    author_id: int
    author_name: Optional[str] = None
    church_id: int
    church_name: Optional[str] = None
    title: str
    description: Optional[str] = None
    video_url: str
    thumbnail_url: Optional[str] = None
    duration_seconds: Optional[int] = None
    category: str
    moderation_status: str
    view_count: int = 0
    like_count: int = 0
    comment_count: int = 0
    share_count: int = 0
    is_featured: bool = False
    tags: Optional[list[str]] = []
    is_liked_by_me: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}


class ShortCommentCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=1000)
    parent_id: Optional[int] = None


class ShortCommentResponse(BaseModel):
    id: int
    short_id: int
    author_id: int
    author_name: Optional[str] = None
    content: str
    parent_id: Optional[int] = None
    is_deleted: bool = False
    created_at: datetime
    replies: Optional[list["ShortCommentResponse"]] = []

    model_config = {"from_attributes": True}


class ShortViewRecord(BaseModel):
    watched_seconds: int = 0
    completed: bool = False
