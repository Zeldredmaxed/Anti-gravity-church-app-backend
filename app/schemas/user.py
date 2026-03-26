"""Pydantic schemas for user and auth operations."""

from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


# --- Auth Schemas ---

class UserRegister(BaseModel):
    church_id: Optional[int] = None
    email: EmailStr
    username: Optional[str] = None
    password: str
    full_name: str
    date_of_birth: Optional[datetime] = None
    role: str = "member"


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class JoinChurchRequest(BaseModel):
    church_id: int


class TokenRefresh(BaseModel):
    refresh_token: str


# --- User Schemas ---

class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    role: str


class UserResponse(UserBase):
    id: int
    church_id: Optional[int] = None
    username: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    is_active: bool
    member_id: Optional[int] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    date_of_birth: Optional[datetime] = None


class UserRoleUpdate(BaseModel):
    role: str


class AuditLogResponse(BaseModel):
    id: int
    church_id: Optional[int] = None
    user_id: Optional[int] = None
    action: str
    resource: str
    resource_id: Optional[str] = None
    details: Optional[str] = None
    ip_address: Optional[str] = None
    timestamp: datetime

    model_config = {"from_attributes": True}
