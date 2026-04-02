"""Prayer request Pydantic schemas."""

from pydantic import BaseModel, Field, model_validator
from typing import Optional
from datetime import datetime


class PrayerRequestCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    category: str = "general"
    is_anonymous: bool = False
    is_urgent: bool = False
    visibility: str = "church_only"


class PrayerRequestUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    is_urgent: Optional[bool] = None
    visibility: Optional[str] = None


class PrayerResponseSchema(BaseModel):
    id: int
    author_id: Optional[int] = None
    author_name: Optional[str] = None
    author_avatar: Optional[str] = None
    content: Optional[str] = None
    is_prayed: bool = True
    created_at: datetime

    model_config = {"from_attributes": True}


class PrayerRequestResponse(BaseModel):
    id: int
    church_id: Optional[int] = None
    author_id: Optional[int] = None
    author_name: Optional[str] = None
    author_avatar: Optional[str] = None
    title: str
    description: Optional[str] = None
    category: str = "general"
    is_anonymous: bool = False
    is_urgent: bool = False
    is_answered: bool = False
    answered_testimony: Optional[str] = None
    prayed_count: int = 0
    visibility: Optional[str] = None
    has_prayed: bool = False  # Frontend expects has_prayed
    is_prayed_by_me: bool = False  # Keep for backward compat
    created_at: datetime
    responses: Optional[list[PrayerResponseSchema]] = []

    model_config = {"from_attributes": True}

    @model_validator(mode="before")
    @classmethod
    def sync_prayed(cls, values):
        """Ensure has_prayed and is_prayed_by_me are in sync."""
        if isinstance(values, dict):
            if values.get("is_prayed_by_me") and not values.get("has_prayed"):
                values["has_prayed"] = values["is_prayed_by_me"]
            if values.get("has_prayed") and not values.get("is_prayed_by_me"):
                values["is_prayed_by_me"] = values["has_prayed"]
        return values


class PrayerResponseCreate(BaseModel):
    content: Optional[str] = None
    text: Optional[str] = None
    message: Optional[str] = None
    is_prayed: bool = True
    is_anonymous: bool = False


class PrayerAnsweredRequest(BaseModel):
    testimony: Optional[str] = None
