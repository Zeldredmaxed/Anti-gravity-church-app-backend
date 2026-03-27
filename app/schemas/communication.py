from typing import Optional
from pydantic import BaseModel

class SegmentFilter(BaseModel):
    membership_status: Optional[str] = None
    min_age: Optional[int] = None
    max_age: Optional[int] = None
    gender: Optional[str] = None
    is_serving: Optional[bool] = None
    not_attended_days: Optional[int] = None
    has_children: Optional[bool] = None

class MessagePayload(BaseModel):
    medium: str # 'email', 'sms', 'push'
    subject: Optional[str] = None
    body: str
    target_member_ids: list[int]

class MessageResponse(BaseModel):
    status: str
    messages_queued: int
    failed_enqueued: int
