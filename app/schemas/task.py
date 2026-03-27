from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

from app.models.task import TaskStatus, TaskType

class TaskBase(BaseModel):
    title: str = Field(..., max_length=255, description="Title of the task")
    description: Optional[str] = Field(None, description="Detailed instructions or context")
    assigned_to: int = Field(..., description="User ID of the person this task is assigned to")
    related_member_id: Optional[int] = Field(None, description="Member ID this task relates to, if any")
    task_type: TaskType = Field(default=TaskType.FOLLOW_UP)
    due_date: Optional[datetime] = Field(None, description="When the task should be completed")

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    assigned_to: Optional[int] = None
    related_member_id: Optional[int] = None
    task_type: Optional[TaskType] = None
    due_date: Optional[datetime] = None

class TaskStatusUpdate(BaseModel):
    status: TaskStatus = Field(..., description="New status for the task")

class TaskResponse(TaskBase):
    id: int
    church_id: int
    assigned_by: int
    status: TaskStatus
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class TaskListResponse(TaskResponse):
    assignee_name: Optional[str] = None
    creator_name: Optional[str] = None
    member_name: Optional[str] = None
