"""Notification Pydantic schemas."""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class AlertResponse(BaseModel):
    id: int
    church_id: Optional[int] = None
    user_id: int
    type: str
    title: str
    body: Optional[str] = None
    data: Optional[dict] = None
    is_read: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}


class AlertListResponse(BaseModel):
    items: list[AlertResponse]
    unread_count: int
    total: int
