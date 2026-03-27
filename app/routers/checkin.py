import secrets
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import Optional
from app.database import get_db
from app.models.child_checkin import CheckinSession
from app.models.member import Member
from app.models.user import User
from app.schemas.child_checkin import (
    CheckinCreate, CheckinCheckout, CheckinResponse, CheckinListResponse
)
from app.utils.security import get_current_user, require_role, get_church_id
from app.dependencies import PaginationParams

router = APIRouter(prefix="/checkin", tags=["Child Check-in"])


@router.get("", response_model=CheckinListResponse)
async def list_checkins(
    event_id: Optional[int] = Query(None),
    service_id: Optional[int] = Query(None),
    is_active_only: bool = Query(False, description="Show only children currently checked in"),
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(require_role("admin", "pastor", "staff", "ministry_leader", "volunteer")),
    db: AsyncSession = Depends(get_db),
):
    """List check-in sessions for a specific event or service."""
    query = select(CheckinSession).where(CheckinSession.church_id == current_user.church_id)

    if event_id:
        query = query.where(CheckinSession.event_id == event_id)
    if service_id:
        query = query.where(CheckinSession.service_id == service_id)
    if is_active_only:
        query = query.where(CheckinSession.checkout_time == None)

    total_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(total_query)

    query = query.offset(pagination.skip).limit(pagination.limit).order_by(CheckinSession.checkin_time.desc())
    result = await db.execute(query)
    sessions = result.scalars().all()

    return {
        "data": sessions,
        "total": total,
        "page": pagination.page,
        "size": pagination.size
    }


@router.post("", response_model=CheckinResponse)
async def perform_checkin(
    checkin_in: CheckinCreate,
    current_user: User = Depends(require_role("admin", "pastor", "staff", "volunteer")),
    db: AsyncSession = Depends(get_db),
):
    """Check a child into a service/event and generate matching label."""
    # Verify child exists
    result = await db.execute(
        select(Member).where(Member.id == checkin_in.child_id, Member.church_id == current_user.church_id)
    )
    child = result.scalar_one_or_none()
    if not child:
        raise HTTPException(status_code=404, detail="Child/Member not found")

    # Generate security matching ID
    matching_id = secrets.token_hex(3).upper() # e.g. "8A2B4F"

    session = CheckinSession(
        **checkin_in.model_dump(),
        church_id=current_user.church_id,
        parent_matching_id=matching_id,
        checked_in_by=current_user.id
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


@router.post("/{session_id}/checkout", response_model=CheckinResponse)
async def perform_checkout(
    session_id: int,
    checkout_in: CheckinCheckout,
    current_user: User = Depends(require_role("admin", "pastor", "staff", "volunteer")),
    db: AsyncSession = Depends(get_db),
):
    """Check out a child, verifying the security code."""
    result = await db.execute(
        select(CheckinSession).where(
            CheckinSession.id == session_id,
            CheckinSession.church_id == current_user.church_id
        )
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Checkin session not found")
        
    if session.checkout_time is not None:
        raise HTTPException(status_code=400, detail="Child already checked out")
        
    if session.parent_matching_id != checkout_in.parent_matching_id:
        raise HTTPException(status_code=403, detail="Invalid security matching code!")

    session.checkout_time = datetime.now(timezone.utc)
    session.checked_out_by = current_user.id

    await db.commit()
    await db.refresh(session)
    return session
