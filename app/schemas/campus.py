from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class CampusBase(BaseModel):
    name: str
    description: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    pastor_name: Optional[str] = None
    latitude: Optional[str] = None
    longitude: Optional[str] = None
    is_main_campus: bool = False
    is_active: bool = True


class CampusCreate(CampusBase):
    pass


class CampusUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    pastor_name: Optional[str] = None
    latitude: Optional[str] = None
    longitude: Optional[str] = None
    is_main_campus: Optional[bool] = None
    is_active: Optional[bool] = None


class CampusResponse(CampusBase):
    id: int
    church_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
