from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class CareCaseBase(BaseModel):
    requester_name: str
    requester_avatar: Optional[str] = None
    care_type: str
    sub_type: Optional[str] = None
    summary: str
    assigned_leader_id: Optional[int] = None
    status: str = "NEW"

class CareCaseCreate(CareCaseBase):
    pass

class CareCaseUpdate(BaseModel):
    requester_name: Optional[str] = None
    requester_avatar: Optional[str] = None
    care_type: Optional[str] = None
    sub_type: Optional[str] = None
    summary: Optional[str] = None
    assigned_leader_id: Optional[int] = None
    status: Optional[str] = None

class CareCaseResponse(CareCaseBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    church_id: int
    assigned_leader_name: Optional[str] = None
    assigned_leader_avatar: Optional[str] = None
    created_at: datetime
    updated_at: datetime
