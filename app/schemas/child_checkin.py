from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class CheckinBase(BaseModel):
    child_id: int
    event_id: Optional[int] = None
    service_id: Optional[int] = None
    room_assignment: Optional[str] = None
    alerts: Optional[str] = None


class CheckinCreate(CheckinBase):
    pass


class CheckinCheckout(BaseModel):
    parent_matching_id: str


class CheckinResponse(CheckinBase):
    id: int
    church_id: int
    parent_matching_id: str
    checkin_time: datetime
    checkout_time: Optional[datetime] = None
    checked_in_by: Optional[int] = None
    checked_out_by: Optional[int] = None

    class Config:
        from_attributes = True

class CheckinListResponse(BaseModel):
    data: list[CheckinResponse]
    total: int
    page: int
    size: int
