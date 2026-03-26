"""Notifications router — list, mark read, mark all read."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update

from app.database import get_db
from app.models.notification import Notification
from app.models.user import User
from app.schemas.notification import NotificationResponse, NotificationListResponse
from app.utils.security import get_current_user

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", response_model=NotificationListResponse)
async def list_notifications(
    limit: int = Query(30, ge=1, le=100),
    offset: int = Query(0, ge=0),
    unread_only: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)):
    """Get notifications for current user."""
    query = select(Notification).where(Notification.user_id == current_user.id)
    if unread_only:
        query = query.where(Notification.is_read == False)
    query = query.order_by(Notification.created_at.desc()).offset(offset).limit(limit)

    notifs = (await db.execute(query)).scalars().all()

    # Counts
    unread_count = (await db.execute(
        select(func.count()).where(
            Notification.user_id == current_user.id,
            Notification.is_read == False)
    )).scalar() or 0
    total = (await db.execute(
        select(func.count()).where(Notification.user_id == current_user.id)
    )).scalar() or 0

    return NotificationListResponse(
        items=[NotificationResponse.model_validate(n) for n in notifs],
        unread_count=unread_count,
        total=total)


@router.post("/{notification_id}/read")
async def mark_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)):
    n = (await db.execute(select(Notification).where(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    ))).scalar_one_or_none()
    if not n:
        raise HTTPException(status_code=404, detail="Notification not found")
    n.is_read = True
    db.add(n)
    return {"message": "Marked as read"}


@router.post("/read-all")
async def mark_all_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)):
    """Mark all notifications as read."""
    await db.execute(
        update(Notification)
        .where(Notification.user_id == current_user.id, Notification.is_read == False)
        .values(is_read=True)
    )
    return {"message": "All notifications marked as read"}
