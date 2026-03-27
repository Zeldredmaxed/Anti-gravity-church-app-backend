from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class DiscipleshipStepBase(BaseModel):
    name: str
    description: Optional[str] = None
    order_index: int = 0
    is_active: bool = True

class DiscipleshipStepCreate(DiscipleshipStepBase):
    pass

class DiscipleshipStepUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    order_index: Optional[int] = None
    is_active: Optional[bool] = None

class DiscipleshipStepResponse(DiscipleshipStepBase):
    id: int
    church_id: int
    created_at: datetime
    class Config:
        from_attributes = True


class MemberDiscipleshipProgressBase(BaseModel):
    step_id: int
    status: str = "planned"
    notes: Optional[str] = None
    completed_at: Optional[datetime] = None

class MemberDiscipleshipProgressCreate(MemberDiscipleshipProgressBase):
    member_id: int

class MemberDiscipleshipProgressUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None
    completed_at: Optional[datetime] = None

class MemberDiscipleshipProgressResponse(MemberDiscipleshipProgressBase):
    id: int
    member_id: int
    created_at: datetime
    updated_at: datetime
    step: Optional[DiscipleshipStepResponse] = None

    class Config:
        from_attributes = True
