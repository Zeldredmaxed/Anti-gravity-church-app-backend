"""Prayer request Pydantic schemas."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class PrayerRequestCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    category: str = "other"
    is_anonymous: bool = False
    is_urgent: bool = False
    visibility: str = "church_only"


class PrayerRequestUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    is_urgent: Optional[bool] = None
    visibility: Optional[str] = None


class PrayerRequestResponse(BaseModel):
    id: int
    church_id: int
    author_id: Optional[int] = None  # Hidden if anonymous
    author_name: Optional[str] = None
    author_avatar: Optional[str] = None
    title: str
    description: Optional[str] = None
    category: str
    is_anonymous: bool = False
    is_urgent: bool = False
    is_answered: bool = False
    answered_testimony: Optional[str] = None
    prayed_count: int = 0
    visibility: str
    is_prayed_by_me: bool = False
    created_at: datetime
    responses: Optional[list["PrayerResponseSchema"]] = []

    model_config = {"from_attributes": True}


class PrayerResponseCreate(BaseModel):
    content: Optional[str] = None
    is_prayed: bool = True


class PrayerResponseSchema(BaseModel):
    id: int
    author_id: Optional[int] = None
    author_name: Optional[str] = None
    author_avatar: Optional[str] = None
    content: Optional[str] = None
    is_prayed: bool = True
    created_at: datetime

    model_config = {"from_attributes": True}


class PrayerAnsweredRequest(BaseModel):
    testimony: Optional[str] = None
