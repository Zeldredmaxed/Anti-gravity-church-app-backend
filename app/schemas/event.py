"""Event system Pydantic schemas."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class EventCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    event_type: str = "service"
    location: Optional[str] = None
    start_datetime: datetime
    end_datetime: Optional[datetime] = None
    is_recurring: bool = False
    recurrence_rule: Optional[str] = None
    max_capacity: Optional[int] = None
    registration_required: bool = False
    cover_image_url: Optional[str] = None


class EventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    event_type: Optional[str] = None
    location: Optional[str] = None
    start_datetime: Optional[datetime] = None
    end_datetime: Optional[datetime] = None
    max_capacity: Optional[int] = None
    registration_required: Optional[bool] = None
    cover_image_url: Optional[str] = None
    is_published: Optional[bool] = None
    is_cancelled: Optional[bool] = None


class EventResponse(BaseModel):
    id: int
    church_id: int
    title: str
    description: Optional[str] = None
    event_type: str
    location: Optional[str] = None
    start_datetime: datetime
    end_datetime: Optional[datetime] = None
    is_recurring: bool = False
    recurrence_rule: Optional[str] = None
    max_capacity: Optional[int] = None
    rsvp_count: int = 0
    registration_required: bool = False
    cover_image_url: Optional[str] = None
    is_published: bool = True
    is_cancelled: bool = False
    created_by: int
    created_at: datetime
    my_rsvp: Optional[str] = None  # going/maybe/not_going or None

    model_config = {"from_attributes": True}


class RSVPCreate(BaseModel):
    status: str = "going"  # going, maybe, not_going
    guests_count: int = 0
    notes: Optional[str] = None


class RSVPResponse(BaseModel):
    id: int
    event_id: int
    user_id: int
    user_name: Optional[str] = None
    status: str
    guests_count: int = 0
    notes: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}
