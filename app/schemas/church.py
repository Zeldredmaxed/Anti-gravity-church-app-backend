"""Church management schemas."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ChurchCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    subdomain: str = Field(..., min_length=2, max_length=100, pattern=r"^[a-z0-9-]+$")
    description: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    pastor_name: Optional[str] = None


class ChurchUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    logo_url: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    pastor_name: Optional[str] = None
    settings: Optional[dict] = None


class ChurchPublicResponse(BaseModel):
    id: int
    name: str
    subdomain: str
    logo_url: Optional[str] = None
    is_active: bool

    model_config = {"from_attributes": True}


class ChurchResponse(BaseModel):
    id: int
    name: str
    subdomain: str
    description: Optional[str] = None
    logo_url: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    pastor_name: Optional[str] = None
    youtube_channel_id: Optional[str] = None
    settings: Optional[dict] = None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ChurchOnboardRequest(BaseModel):
    """Register a new church + its first admin user in one request."""
    church: ChurchCreate
    admin_email: str
    admin_password: str = Field(..., min_length=6)
    admin_name: str
    registration_key: str = Field(..., min_length=5, description="Paid-user registration invite key")
