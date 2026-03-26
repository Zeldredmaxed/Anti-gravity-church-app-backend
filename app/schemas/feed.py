"""Feed system Pydantic schemas."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# --- Post Schemas ---

class PostCreate(BaseModel):
    content: Optional[str] = None
    media_urls: Optional[list[str]] = []
    post_type: str = "text"
    visibility: str = "members_only"


class PostUpdate(BaseModel):
    content: Optional[str] = None
    media_urls: Optional[list[str]] = None
    visibility: Optional[str] = None
    is_pinned: Optional[bool] = None


class PostResponse(BaseModel):
    id: int
    church_id: int
    author_id: int
    author_name: Optional[str] = None
    content: Optional[str] = None
    media_urls: Optional[list[str]] = []
    post_type: str
    visibility: str
    amen_count: int = 0
    comments_count: int = 0
    shares_count: int = 0
    is_pinned: bool = False
    is_amened_by_me: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# --- Comment Schemas ---

class CommentCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000)
    parent_id: Optional[int] = None


class CommentResponse(BaseModel):
    id: int
    post_id: int
    author_id: int
    author_name: Optional[str] = None
    content: str
    parent_id: Optional[int] = None
    is_deleted: bool = False
    created_at: datetime
    replies: Optional[list["CommentResponse"]] = []

    model_config = {"from_attributes": True}


# --- Post Detail ---

class PostDetailResponse(PostResponse):
    comments: list[CommentResponse] = []
