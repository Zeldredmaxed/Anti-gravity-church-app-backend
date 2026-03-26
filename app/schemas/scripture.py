"""Service Scripture Pydantic schemas."""

from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel


class ServiceScriptureCreate(BaseModel):
    title: Optional[str] = None
    book: str
    chapter: int
    verse_start: int
    verse_end: Optional[int] = None
    pastor_notes: Optional[str] = None
    service_date: Optional[date] = None


class ServiceScriptureUpdate(BaseModel):
    title: Optional[str] = None
    book: Optional[str] = None
    chapter: Optional[int] = None
    verse_start: Optional[int] = None
    verse_end: Optional[int] = None
    pastor_notes: Optional[str] = None
    is_active: Optional[bool] = None
    service_date: Optional[date] = None


class ServiceScriptureResponse(BaseModel):
    id: int
    church_id: int
    title: Optional[str] = None
    book: str
    chapter: int
    verse_start: int
    verse_end: Optional[int] = None
    pastor_notes: Optional[str] = None
    is_active: bool
    service_date: Optional[date] = None
    created_at: datetime
    updated_at: datetime

    # Resolved verse text from KJV data
    verse_text: Optional[str] = None
    set_by_name: Optional[str] = None

    class Config:
        from_attributes = True
