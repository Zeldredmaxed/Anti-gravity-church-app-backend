from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    price_cents: int = Field(default=0, ge=0, description="Price in cents")
    image_url: Optional[str] = None
    category: Optional[str] = Field(default="General", max_length=50)
    inventory_count: Optional[int] = Field(default=None, ge=0)
    is_active: bool = True

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    price_cents: Optional[int] = Field(None, ge=0)
    image_url: Optional[str] = None
    category: Optional[str] = Field(None, max_length=50)
    inventory_count: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None

class ProductResponse(ProductBase):
    id: int
    church_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
