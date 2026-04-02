"""Dashboard analytics — aggregation layer with chart-ready endpoints."""

from datetime import date, datetime, timedelta, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from pydantic import BaseModel

from app.database import get_db
from app.models.member import Member
from app.models.donation import Donation
from app.models.attendance import AttendanceRecord
from app.models.group import Group
from app.models.event import Event
from app.models.care import CareCase
from app.models.volunteer import VolunteerHoursLog
from app.models.prayer import PrayerRequest
from app.models.activity_log import MemberActivityLog
from app.models.user import User, AuditLog
from app.utils.security import get_current_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard Analytics"])


# ── Response schemas ──

class MetricCard(BaseModel):
    total: float
    trend: Optional[float] = None  # percentage change vs previous period
    label: Optional[str] = None


class ChartPoint(BaseModel):
    date: str
    value: float


class ActivityItem(BaseModel):
    id: int
    description: str
    activity_type: Optional[str] = None
    occurred_at: str


class EventPreview(BaseModel):
    id: int
    title: str
    date: Optional[str] = None
    location: Optional[str] = None


class CareSummaryItem(BaseModel):
    status: str
    count: int


# ── KPI Cards ──

@router.get("/metrics")
async def get_dashboard_metrics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get aggregated KPI metrics for the main dashboard."""
    church_id = current_user.church_id
    now = datetime.now(timezone.utc)
    first_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    thirty_days_ago = now - timedelta(days=30)
    sixty_days_ago = now - timedelta(days=60)

    # ── Members ──
    total_members = (await db.execute(
        select(func.count(Member.id)).where(Member.church_id == church_id, Member.is_deleted == False)
    )).scalar() or 0

    new_members_this_month = (await db.execute(
        select(func.count(Member.id)).where(
            Member.church_id == church_id, Member.created_at >= first_of_month
        )
    )).scalar() or 0

    # ── Giving (MTD) ──
    giving_mtd = (await db.execute(
        select(func.coalesce(func.sum(Donation.amount), 0)).where(
            Donation.church_id == church_id,
            Donation.date >= first_of_month.date(),
            Donation.status == "completed",
        )
    )).scalar() or 0

    # Previous month giving for trend
    prev_month_start = (first_of_month - timedelta(days=1)).replace(day=1)
    giving_prev = (await db.execute(
        select(func.coalesce(func.sum(Donation.amount), 0)).where(
            Donation.church_id == church_id,
            Donation.date >= prev_month_start.date(),
            Donation.date < first_of_month.date(),
            Donation.status == "completed",
        )
    )).scalar() or 0

    giving_trend = 0
    if giving_prev and float(giving_prev) > 0:
        giving_trend = round(((float(giving_mtd) - float(giving_prev)) / float(giving_prev)) * 100, 1)

    # ── Attendance (30 days) ──
    attendance_30d = (await db.execute(
        select(func.count(AttendanceRecord.id)).where(
            AttendanceRecord.church_id == church_id,
            AttendanceRecord.date >= thirty_days_ago.date(),
        )
    )).scalar() or 0

    attendance_prev_30d = (await db.execute(
        select(func.count(AttendanceRecord.id)).where(
            AttendanceRecord.church_id == church_id,
            AttendanceRecord.date >= sixty_days_ago.date(),
            AttendanceRecord.date < thirty_days_ago.date(),
        )
    )).scalar() or 0

    attendance_trend = 0
    if attendance_prev_30d and attendance_prev_30d > 0:
        attendance_trend = round(((attendance_30d - attendance_prev_30d) / attendance_prev_30d) * 100, 1)

    # ── Groups ──
    total_groups = (await db.execute(
        select(func.count(Group.id)).where(Group.church_id == church_id, Group.is_active == True)
    )).scalar() or 0

    # ── Care Cases ──
    open_care_cases = (await db.execute(
        select(func.count(CareCase.id)).where(
            CareCase.church_id == church_id,
            CareCase.is_deleted == False,
            CareCase.status.in_(["NEW", "IN-PROGRESS", "NEEDS LEADER"]),
        )
    )).scalar() or 0

    # ── Volunteer Hours (MTD) ──
    volunteer_hours = (await db.execute(
        select(func.coalesce(func.sum(VolunteerHoursLog.hours_served), 0)).where(
            VolunteerHoursLog.church_id == church_id,
            VolunteerHoursLog.date >= first_of_month.date(),
        )
    )).scalar() or 0

    # ── Prayer Requests ──
    active_prayers = (await db.execute(
        select(func.count(PrayerRequest.id)).where(
            PrayerRequest.church_id == church_id,
            PrayerRequest.is_answered == False,
            PrayerRequest.is_deleted == False,
        )
    )).scalar() or 0

    return {
        "members": {"total": total_members, "trend": new_members_this_month, "label": "new this month"},
        "giving": {"total": float(giving_mtd), "trend": giving_trend, "label": "vs last month"},
        "attendance": {"total": attendance_30d, "trend": attendance_trend, "label": "vs prev 30d"},
        "groups": {"total": total_groups, "trend": 0, "label": "active"},
        "care_cases": {"total": open_care_cases, "trend": 0, "label": "open"},
        "volunteer_hours": {"total": float(volunteer_hours), "trend": 0, "label": "this month"},
        "prayers": {"total": active_prayers, "trend": 0, "label": "active"},
    }


# ── Chart Data ──

@router.get("/giving-chart", response_model=List[ChartPoint])
async def get_giving_chart(
    months: int = Query(12, ge=1, le=24),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Monthly giving totals for the line chart."""
    church_id = current_user.church_id
    cutoff = date.today() - timedelta(days=months * 30)

    is_postgres = db.bind.dialect.name == "postgresql"
    month_expr = func.to_char(Donation.date, 'YYYY-MM') if is_postgres else func.strftime('%Y-%m', Donation.date)

    result = await db.execute(
        select(
            month_expr.label("month"),
            func.sum(Donation.amount).label("total"),
        )
        .where(
            Donation.church_id == church_id,
            Donation.date >= cutoff,
            Donation.status == "completed",
        )
        .group_by(month_expr)
        .order_by(month_expr)
    )

    return [ChartPoint(date=row.month, value=float(row.total or 0)) for row in result.all()]


@router.get("/attendance-chart", response_model=List[ChartPoint])
async def get_attendance_chart(
    weeks: int = Query(12, ge=1, le=52),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Weekly attendance totals for the bar chart."""
    church_id = current_user.church_id
    cutoff = date.today() - timedelta(weeks=weeks)

    is_postgres = db.bind.dialect.name == "postgresql"
    week_expr = func.to_char(AttendanceRecord.date, 'IYYY-IW') if is_postgres else func.strftime('%Y-%W', AttendanceRecord.date)

    result = await db.execute(
        select(
            week_expr.label("week"),
            func.count(AttendanceRecord.id).label("count"),
        )
        .where(
            AttendanceRecord.church_id == church_id,
            AttendanceRecord.date >= cutoff,
        )
        .group_by(week_expr)
        .order_by(week_expr)
    )

    return [ChartPoint(date=row.week, value=float(row.count or 0)) for row in result.all()]


@router.get("/member-growth", response_model=List[ChartPoint])
async def get_member_growth(
    months: int = Query(12, ge=1, le=24),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Monthly new member counts for the growth chart."""
    church_id = current_user.church_id
    cutoff = date.today() - timedelta(days=months * 30)

    is_postgres = db.bind.dialect.name == "postgresql"
    month_expr = func.to_char(Member.created_at, 'YYYY-MM') if is_postgres else func.strftime('%Y-%m', Member.created_at)

    result = await db.execute(
        select(
            month_expr.label("month"),
            func.count(Member.id).label("count"),
        )
        .where(
            Member.church_id == church_id,
            Member.created_at >= cutoff,
        )
        .group_by(month_expr)
        .order_by(month_expr)
    )

    return [ChartPoint(date=row.month, value=float(row.count or 0)) for row in result.all()]


# ── Activity Feed ──

@router.get("/recent-activity", response_model=List[ActivityItem])
async def get_recent_activity(
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get recent member activity from the activity log."""
    church_id = current_user.church_id

    result = await db.execute(
        select(MemberActivityLog)
        .where(MemberActivityLog.church_id == church_id)
        .order_by(desc(MemberActivityLog.occurred_at))
        .limit(limit)
    )
    logs = result.scalars().all()

    return [
        ActivityItem(
            id=log.id,
            description=log.description,
            activity_type=log.activity_type,
            occurred_at=log.occurred_at.isoformat() if log.occurred_at else "",
        )
        for log in logs
    ]


# ── Upcoming Events ──

@router.get("/upcoming-events", response_model=List[EventPreview])
async def get_upcoming_events(
    limit: int = Query(5, ge=1, le=20),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the next upcoming events."""
    church_id = current_user.church_id
    now = datetime.now(timezone.utc)

    result = await db.execute(
        select(Event)
        .where(
            Event.church_id == church_id,
            Event.start_datetime >= now,
            Event.is_cancelled == False,
        )
        .order_by(Event.start_datetime)
        .limit(limit)
    )
    events = result.scalars().all()

    return [
        EventPreview(
            id=e.id,
            title=e.title,
            date=e.start_datetime.isoformat() if e.start_datetime else None,
            location=e.location,
        )
        for e in events
    ]


# ── Care Summary ──

@router.get("/care-summary", response_model=List[CareSummaryItem])
async def get_care_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get care case counts grouped by status."""
    church_id = current_user.church_id

    result = await db.execute(
        select(
            CareCase.status,
            func.count(CareCase.id).label("count"),
        )
        .where(CareCase.church_id == church_id, CareCase.is_deleted == False)
        .group_by(CareCase.status)
    )

    return [CareSummaryItem(status=row.status, count=row.count) for row in result.all()]
