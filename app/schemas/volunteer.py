from typing import Optional
from datetime import datetime
from pydantic import BaseModel

class VolunteerScheduleBase(BaseModel):
    role_id: int
    member_id: int
    event_id: Optional[int] = None
    service_id: Optional[int] = None
    status: str = "pending"
    notes: Optional[str] = None

class VolunteerScheduleResponse(VolunteerScheduleBase):
    id: int
    church_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True
