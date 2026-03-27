from typing import Optional, Any
from datetime import datetime
from pydantic import BaseModel


class AutomationRuleBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_active: bool = True
    trigger_type: str
    trigger_config: Optional[dict[str, Any]] = None
    action_type: str
    action_payload: Optional[dict[str, Any]] = None


class AutomationRuleCreate(AutomationRuleBase):
    pass


class AutomationRuleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    trigger_type: Optional[str] = None
    trigger_config: Optional[dict[str, Any]] = None
    action_type: Optional[str] = None
    action_payload: Optional[dict[str, Any]] = None


class AutomationRuleResponse(AutomationRuleBase):
    id: int
    church_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class AutomationRuleListResponse(BaseModel):
    data: list[AutomationRuleResponse]
    total: int
    page: int
    size: int
