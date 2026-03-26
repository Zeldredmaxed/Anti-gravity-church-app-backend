"""Alerts router — list, mark read, mark all read."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update

from app.database import get_db
from app.models.alert import Alert
from app.models.user import User
from app.schemas.alert import AlertResponse, AlertListResponse
from app.utils.security import get_current_user

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get("", response_model=AlertListResponse)
async def list_alerts(
    limit: int = Query(30, ge=1, le=100),
    offset: int = Query(0, ge=0),
    unread_only: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)):
    """Get alerts for current user."""
    query = select(Alert).where(Alert.user_id == current_user.id)
    if unread_only:
        query = query.where(Alert.is_read == False)
    query = query.order_by(Alert.created_at.desc()).offset(offset).limit(limit)

    alerts = (await db.execute(query)).scalars().all()

    # Counts
    unread_count = (await db.execute(
        select(func.count()).where(
            Alert.user_id == current_user.id,
            Alert.is_read == False)
    )).scalar() or 0
    total = (await db.execute(
        select(func.count()).where(Alert.user_id == current_user.id)
    )).scalar() or 0

    return AlertListResponse(
        items=[AlertResponse.model_validate(n) for n in alerts],
        unread_count=unread_count,
        total=total)


@router.post("/{alert_id}/read")
async def mark_read(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)):
    n = (await db.execute(select(Alert).where(
        Alert.id == alert_id,
        Alert.user_id == current_user.id
    ))).scalar_one_or_none()
    if not n:
        raise HTTPException(status_code=404, detail="Alert not found")
    n.is_read = True
    db.add(n)
    return {"message": "Marked as read"}


@router.post("/read-all")
async def mark_all_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)):
    """Mark all alerts as read."""
    await db.execute(
        update(Alert)
        .where(Alert.user_id == current_user.id, Alert.is_read == False)
        .values(is_read=True)
    )
    return {"message": "All alerts marked as read"}
