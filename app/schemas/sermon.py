"""Sermon Pydantic schemas for request/response validation."""

from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel


# ── Sermon ──────────────────────────────
class SermonCreate(BaseModel):
    title: str
    description: Optional[str] = None
    speaker: Optional[str] = None
    series_name: Optional[str] = None
    scripture_reference: Optional[str] = None
    video_url: Optional[str] = None
    video_type: str = "upload"
    youtube_video_id: Optional[str] = None
    thumbnail_url: Optional[str] = None
    duration_seconds: Optional[int] = None
    transcript: Optional[str] = None
    recorded_date: Optional[date] = None
    tags: list[str] = []
    is_published: bool = True


class SermonUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    speaker: Optional[str] = None
    series_name: Optional[str] = None
    scripture_reference: Optional[str] = None
    video_url: Optional[str] = None
    video_type: Optional[str] = None
    youtube_video_id: Optional[str] = None
    thumbnail_url: Optional[str] = None
    duration_seconds: Optional[int] = None
    transcript: Optional[str] = None
    recorded_date: Optional[date] = None
    tags: Optional[list[str]] = None
    is_published: Optional[bool] = None
    is_live: Optional[bool] = None


class SermonResponse(BaseModel):
    id: int
    church_id: int
    title: str
    description: Optional[str] = None
    speaker: Optional[str] = None
    series_name: Optional[str] = None
    scripture_reference: Optional[str] = None
    video_url: Optional[str] = None
    video_type: str
    youtube_video_id: Optional[str] = None
    thumbnail_url: Optional[str] = None
    duration_seconds: Optional[int] = None
    transcript: Optional[str] = None
    recorded_date: Optional[date] = None
    is_live: bool
    view_count: int
    amen_count: int
    tags: list = []
    is_published: bool
    created_at: datetime
    updated_at: datetime
    uploader_name: Optional[str] = None

    class Config:
        from_attributes = True


# ── Sermon Notes ────────────────────────
class SermonNoteCreate(BaseModel):
    content: str
    timestamp_marker: Optional[int] = None      # seconds into sermon


class SermonNoteUpdate(BaseModel):
    content: Optional[str] = None
    timestamp_marker: Optional[int] = None


class SermonNoteResponse(BaseModel):
    id: int
    sermon_id: int
    user_id: int
    content: str
    timestamp_marker: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    sermon_title: Optional[str] = None

    class Config:
        from_attributes = True
