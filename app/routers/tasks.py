"""Ministry tasks and follow-ups router."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from typing import Optional
from datetime import datetime, timezone

from app.database import get_db
from app.models.task import Task, TaskStatus, TaskType
from app.models.user import User
from app.models.member import Member
from app.schemas.task import TaskCreate, TaskUpdate, TaskStatusUpdate, TaskResponse, TaskListResponse
from app.utils.security import get_current_user, require_role
from app.dependencies import PaginationParams
from app.models.alert import create_alert

router = APIRouter(prefix="/tasks", tags=["Tasks"])

async def _enrich_task(db: AsyncSession, task: Task) -> dict:
    # Get names for display mapping
    assignee = (await db.execute(select(User).where(User.id == task.assigned_to))).scalar_one_or_none()
    creator = (await db.execute(select(User).where(User.id == task.assigned_by))).scalar_one_or_none()
    
    member_name = None
    if task.related_member_id:
        member = (await db.execute(select(Member).where(Member.id == task.related_member_id))).scalar_one_or_none()
        if member:
            member_name = f"{member.first_name} {member.last_name}"
            
    # Serialize to dict and add enriched fields
    data = {c.name: getattr(task, c.name) for c in task.__table__.columns}
    data["assignee_name"] = assignee.full_name if assignee else "Unknown"
    data["creator_name"] = creator.full_name if creator else "Unknown"
    data["member_name"] = member_name
    return data

@router.get("/my-tasks", response_model=list[TaskListResponse])
async def get_my_tasks(
    status: Optional[TaskStatus] = None,
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get tasks assigned to the current user."""
    query = select(Task).where(
        Task.church_id == current_user.church_id,
        Task.assigned_to == current_user.id
    )
    if status:
        query = query.where(Task.status == status.value)
        
    query = query.order_by(
        Task.due_date.asc().nulls_last(),
        Task.created_at.desc()
    ).offset(pagination.offset).limit(pagination.per_page)
    
    tasks = (await db.execute(query)).scalars().all()
    
    return [await _enrich_task(db, t) for t in tasks]


@router.get("/assigned-by-me", response_model=list[TaskListResponse])
async def get_tasks_assigned_by_me(
    status: Optional[TaskStatus] = None,
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get tasks the current user has assigned to others."""
    query = select(Task).where(
        Task.church_id == current_user.church_id,
        Task.assigned_by == current_user.id
    )
    if status:
        query = query.where(Task.status == status.value)
        
    query = query.order_by(Task.created_at.desc()).offset(pagination.offset).limit(pagination.per_page)
    tasks = (await db.execute(query)).scalars().all()
    
    return [await _enrich_task(db, t) for t in tasks]


@router.post("", response_model=TaskResponse, status_code=201)
async def create_task(
    data: TaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new task and assign it to a leader/staff member."""
    # Verify assignee exists and is in same church
    assignee = (await db.execute(select(User).where(
        User.id == data.assigned_to, User.church_id == current_user.church_id
    ))).scalar_one_or_none()
    if not assignee:
        raise HTTPException(status_code=404, detail="Assignee not found or not in your church")
        
    task = Task(
        church_id=current_user.church_id,
        assigned_by=current_user.id,
        assigned_to=data.assigned_to,
        related_member_id=data.related_member_id,
        title=data.title,
        description=data.description,
        task_type=data.task_type.value,
        due_date=data.due_date,
        status=TaskStatus.PENDING.value
    )
    
    db.add(task)
    await db.commit()
    await db.refresh(task)
    
    # Notify assignee if it's not self-assigned
    if task.assigned_to != current_user.id:
        await create_alert(
            db=db,
            user_id=task.assigned_to,
            type="system",
            title="New Task Assigned",
            body=f"{current_user.full_name} assigned a task to you: {task.title}",
            data={"link_type": "task", "link_id": task.id},
            church_id=current_user.church_id
        )
        
    return task


@router.get("/{task_id}", response_model=TaskListResponse)
async def get_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task = (await db.execute(select(Task).where(
        Task.id == task_id, Task.church_id == current_user.church_id
    ))).scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    return await _enrich_task(db, task)


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    data: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task = (await db.execute(select(Task).where(
        Task.id == task_id, Task.church_id == current_user.church_id
    ))).scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    # Only creator or admin can change core task aspects (title, assignee, due date)
    if task.assigned_by != current_user.id and current_user.role not in ["admin", "pastor"]:
        raise HTTPException(status_code=403, detail="Only creator or admin can update task details")
        
    if data.title is not None:
        task.title = data.title
    if data.description is not None:
        task.description = data.description
    if data.assigned_to is not None:
        task.assigned_to = data.assigned_to
    if data.related_member_id is not None:
        task.related_member_id = data.related_member_id
    if data.task_type is not None:
        task.task_type = data.task_type.value
    if data.due_date is not None:
        task.due_date = data.due_date
        
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


@router.put("/{task_id}/status", response_model=TaskResponse)
async def update_task_status(
    task_id: int,
    data: TaskStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update the status of a task. Can be done by assignee or creator."""
    task = (await db.execute(select(Task).where(
        Task.id == task_id, Task.church_id == current_user.church_id
    ))).scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    if task.assigned_to != current_user.id and task.assigned_by != current_user.id and current_user.role not in ["admin", "pastor"]:
        raise HTTPException(status_code=403, detail="Not authorized to update this task")
        
    # If marking as completed
    if data.status.value == TaskStatus.COMPLETED.value and task.status != TaskStatus.COMPLETED.value:
        task.completed_at = datetime.now(timezone.utc)
    # If moving away from completed
    elif data.status.value != TaskStatus.COMPLETED.value and task.status == TaskStatus.COMPLETED.value:
        task.completed_at = None
        
    task.status = data.status.value
    db.add(task)
    
    # Notify creator if assignee completes it
    if data.status.value == TaskStatus.COMPLETED.value and task.assigned_by != current_user.id:
        await create_alert(
            db=db,
            user_id=task.assigned_by,
            type="system",
            title="Task Completed",
            body=f"{current_user.full_name} completed task: {task.title}",
            data={"link_type": "task", "link_id": task.id},
            church_id=current_user.church_id
        )
        
    await db.commit()
    await db.refresh(task)
    return task
