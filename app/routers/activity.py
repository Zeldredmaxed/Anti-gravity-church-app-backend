"""Member activity timeline router — logs and retrieves member lifecycle events."""

from datetime import datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from pydantic import BaseModel, ConfigDict

from app.database import get_db
from app.models.activity_log import MemberActivityLog, ActivityType
from app.models.member import Member
from app.models.user import User
from app.utils.security import get_current_user

router = APIRouter(prefix="/members", tags=["Member Activity"])


class ActivityLogCreate(BaseModel):
    activity_type: str = ActivityType.CUSTOM.value
    description: str
    metadata_json: Optional[dict] = None
    occurred_at: Optional[datetime] = None


class ActivityLogResponse(BaseModel):
    id: int
    member_id: int
    activity_type: str
    description: str
    metadata_json: Optional[dict] = None
    occurred_at: datetime
    logged_by: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


@router.get("/{member_id}/timeline", response_model=List[ActivityLogResponse])
async def get_member_timeline(
    member_id: int,
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the paginated activity timeline for a member."""
    offset = (page - 1) * per_page
    result = await db.execute(
        select(MemberActivityLog)
        .where(MemberActivityLog.member_id == member_id)
        .order_by(desc(MemberActivityLog.occurred_at))
        .offset(offset)
        .limit(per_page)
    )
    return result.scalars().all()


@router.post("/{member_id}/timeline", response_model=ActivityLogResponse, status_code=201)
async def log_member_activity(
    member_id: int,
    data: ActivityLogCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Manually log a milestone or activity on a member's timeline."""
    # Verify member exists
    member = (await db.execute(select(Member).where(Member.id == member_id))).scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    log = MemberActivityLog(
        church_id=member.church_id,
        member_id=member_id,
        activity_type=data.activity_type,
        description=data.description,
        metadata_json=data.metadata_json,
        occurred_at=data.occurred_at or datetime.now(timezone.utc),
        logged_by=current_user.id,
    )
    db.add(log)
    await db.flush()
    await db.refresh(log)
    return log


# ── Helper function for internal use by other routers ──

async def _log_activity(
    db: AsyncSession,
    church_id: int,
    member_id: int,
    activity_type: str,
    description: str,
    metadata_json: Optional[dict] = None,
    logged_by: Optional[int] = None,
):
    """Internal helper — call from donations, groups, attendance routers to auto-log activity."""
    log = MemberActivityLog(
        church_id=church_id,
        member_id=member_id,
        activity_type=activity_type,
        description=description,
        metadata_json=metadata_json,
        logged_by=logged_by,
    )
    db.add(log)
