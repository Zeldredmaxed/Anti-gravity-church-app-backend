"""Event system Pydantic schemas."""

from pydantic import BaseModel, Field, model_validator
from typing import Optional
from datetime import datetime


class EventCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    event_type: Optional[str] = None
    type: Optional[str] = None  # Alias accepted from frontend
    location: Optional[str] = None
    start_datetime: Optional[datetime] = None
    start_date: Optional[datetime] = None  # Frontend sends this
    end_datetime: Optional[datetime] = None
    end_date: Optional[datetime] = None  # Frontend sends this
    is_recurring: bool = False
    recurrence_rule: Optional[str] = None
    max_capacity: Optional[int] = None
    registration_required: bool = False
    cover_image_url: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def normalize_fields(cls, values):
        """Accept start_date OR start_datetime, and type OR event_type."""
        if isinstance(values, dict):
            # Normalize datetime fields
            if not values.get("start_datetime") and values.get("start_date"):
                values["start_datetime"] = values["start_date"]
            if not values.get("end_datetime") and values.get("end_date"):
                values["end_datetime"] = values["end_date"]
            # Normalize type field
            if not values.get("event_type") and values.get("type"):
                values["event_type"] = values["type"]
            # Default event_type
            if not values.get("event_type"):
                values["event_type"] = "service"
        return values

    def to_db_dict(self):
        """Return dict with only the DB column names."""
        d = self.model_dump(exclude={"start_date", "end_date", "type"}, exclude_none=False)
        return d


class EventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    event_type: Optional[str] = None
    type: Optional[str] = None
    location: Optional[str] = None
    start_datetime: Optional[datetime] = None
    start_date: Optional[datetime] = None
    end_datetime: Optional[datetime] = None
    end_date: Optional[datetime] = None
    max_capacity: Optional[int] = None
    registration_required: Optional[bool] = None
    cover_image_url: Optional[str] = None
    is_published: Optional[bool] = None
    is_cancelled: Optional[bool] = None

    @model_validator(mode="before")
    @classmethod
    def normalize_fields(cls, values):
        if isinstance(values, dict):
            if not values.get("start_datetime") and values.get("start_date"):
                values["start_datetime"] = values["start_date"]
            if not values.get("end_datetime") and values.get("end_date"):
                values["end_datetime"] = values["end_date"]
            if not values.get("event_type") and values.get("type"):
                values["event_type"] = values["type"]
        return values

    def to_db_dict(self):
        """Return dict with only the DB column names, excluding unset."""
        d = self.model_dump(
            exclude={"start_date", "end_date", "type"},
            exclude_unset=True,
        )
        return d


class EventResponse(BaseModel):
    id: int
    church_id: Optional[int] = None
    title: str
    description: Optional[str] = None
    event_type: Optional[str] = None
    type: Optional[str] = None  # Mirror of event_type for frontend
    location: Optional[str] = None
    start_datetime: Optional[datetime] = None
    start_date: Optional[datetime] = None  # Mirror for frontend
    end_datetime: Optional[datetime] = None
    end_date: Optional[datetime] = None  # Mirror for frontend
    is_recurring: bool = False
    recurrence_rule: Optional[str] = None
    max_capacity: Optional[int] = None
    rsvp_count: int = 0
    registration_required: bool = False
    cover_image_url: Optional[str] = None
    is_published: bool = True
    is_cancelled: bool = False
    status: Optional[str] = None  # "upcoming", "cancelled", "past"
    created_by: Optional[int] = None
    created_at: Optional[datetime] = None
    my_rsvp: Optional[str] = None  # going/maybe/not_going or None

    model_config = {"from_attributes": True}

    @model_validator(mode="before")
    @classmethod
    def populate_mirrors(cls, values):
        """Populate mirror fields for the frontend."""
        if isinstance(values, dict):
            # Mirror datetime fields
            if values.get("start_datetime") and not values.get("start_date"):
                values["start_date"] = values["start_datetime"]
            if values.get("end_datetime") and not values.get("end_date"):
                values["end_date"] = values["end_datetime"]
            # Mirror type field
            if values.get("event_type") and not values.get("type"):
                values["type"] = values["event_type"]
            # Compute status
            if not values.get("status"):
                if values.get("is_cancelled"):
                    values["status"] = "cancelled"
                else:
                    values["status"] = "upcoming"
        return values


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
