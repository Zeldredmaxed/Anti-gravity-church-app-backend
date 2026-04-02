"""Pydantic schemas for member management."""

from pydantic import BaseModel, EmailStr
from typing import Optional, List, Any
from datetime import date, datetime


class MemberCreate(BaseModel):
    first_name: str
    last_name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    secondary_phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    pronouns: Optional[str] = None
    marital_status: Optional[str] = None
    photo_url: Optional[str] = None
    membership_status: str = "visitor"
    join_date: Optional[date] = None
    baptism_date: Optional[date] = None
    baptism_location: Optional[str] = None
    baptism_type: Optional[str] = None
    baptism_pastor: Optional[str] = None
    salvation_date: Optional[date] = None
    spiritual_gifts: Optional[List[str]] = None
    background_check_status: Optional[str] = None
    background_check_date: Optional[date] = None
    custom_fields: Optional[dict] = None
    family_id: Optional[int] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None


class MemberUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    secondary_phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    pronouns: Optional[str] = None
    marital_status: Optional[str] = None
    photo_url: Optional[str] = None
    membership_status: Optional[str] = None
    join_date: Optional[date] = None
    baptism_date: Optional[date] = None
    baptism_location: Optional[str] = None
    baptism_type: Optional[str] = None
    baptism_pastor: Optional[str] = None
    salvation_date: Optional[date] = None
    spiritual_gifts: Optional[List[str]] = None
    background_check_status: Optional[str] = None
    background_check_date: Optional[date] = None
    custom_fields: Optional[dict] = None
    family_id: Optional[int] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None


class MemberResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    secondary_phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    pronouns: Optional[str] = None
    marital_status: Optional[str] = None
    photo_url: Optional[str] = None
    membership_status: str
    join_date: Optional[date] = None
    baptism_date: Optional[date] = None
    baptism_location: Optional[str] = None
    baptism_type: Optional[str] = None
    baptism_pastor: Optional[str] = None
    salvation_date: Optional[date] = None
    spiritual_gifts: Optional[List[str]] = None
    background_check_status: Optional[str] = None
    background_check_date: Optional[date] = None
    custom_fields: Optional[dict] = None
    family_id: Optional[int] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MemberListResponse(BaseModel):
    items: List[MemberResponse]
    total: int
    page: int
    per_page: int
    pages: int


class MemberNoteCreate(BaseModel):
    note_type: str = "general"
    content: str
    is_confidential: bool = False


class MemberNoteResponse(BaseModel):
    id: int
    member_id: int
    author_id: int
    note_type: str
    content: str
    is_confidential: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class EngagementScore(BaseModel):
    member_id: int
    member_name: str
    attendance_score: float
    giving_score: float
    serving_score: float
    group_score: float
    overall_score: float
    level: str  # "highly_engaged", "engaged", "somewhat_engaged", "at_risk", "disengaged"
