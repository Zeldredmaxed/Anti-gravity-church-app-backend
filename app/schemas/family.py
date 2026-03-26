"""Pydantic schemas for family management."""

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class FamilyCreate(BaseModel):
    family_name: str
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    phone: Optional[str] = None


class FamilyUpdate(BaseModel):
    family_name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    phone: Optional[str] = None


class FamilyMemberAdd(BaseModel):
    member_id: int
    relationship_type: str = "other"


class FamilyRelationshipResponse(BaseModel):
    id: int
    member_id: int
    relationship_type: str
    member_name: Optional[str] = None

    model_config = {"from_attributes": True}


class FamilyResponse(BaseModel):
    id: int
    family_name: str
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    phone: Optional[str] = None
    member_count: int = 0
    created_at: datetime

    model_config = {"from_attributes": True}


class FamilyDetailResponse(FamilyResponse):
    relationships: List[FamilyRelationshipResponse] = []
