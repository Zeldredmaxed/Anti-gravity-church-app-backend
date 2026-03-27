from typing import Optional
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel


class AssetBase(BaseModel):
    name: str
    category: Optional[str] = None
    serial_number: Optional[str] = None
    purchase_date: Optional[date] = None
    purchase_price: Optional[Decimal] = None
    status: str = "available"
    notes: Optional[str] = None
    assigned_to_id: Optional[int] = None


class AssetCreate(AssetBase):
    pass


class AssetUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    serial_number: Optional[str] = None
    purchase_date: Optional[date] = None
    purchase_price: Optional[Decimal] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    assigned_to_id: Optional[int] = None


class AssetResponse(AssetBase):
    id: int
    church_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class AssetListResponse(BaseModel):
    data: list[AssetResponse]
    total: int
    page: int
    size: int
