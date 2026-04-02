"""Volunteer management — roles, schedules, applications, hours, retention metrics."""

from datetime import datetime, date, timedelta, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, distinct
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import joinedload

from app.database import get_db
from app.models.user import User
from app.models.member import Member
from app.models.volunteer import (
    VolunteerRole, VolunteerSchedule, VolunteerAvailability,
    VolunteerApplication, VolunteerHoursLog, ApplicationStatus,
)
from app.utils.security import get_current_user

router = APIRouter(prefix="/volunteers", tags=["Volunteers"])


# ── Schemas ──

class VolunteerRoleResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    teams: Optional[str] = None
    capacity_needed: Optional[int] = None
    is_active: bool = True

    model_config = ConfigDict(from_attributes=True)


class VolunteerRoleCreate(BaseModel):
    name: str
    description: Optional[str] = None
    teams: Optional[str] = None
    capacity_needed: Optional[int] = None


class VolunteerScheduleResponse(BaseModel):
    id: int
    role_id: int
    event_id: Optional[int] = None
    member_id: int
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: str

    model_config = ConfigDict(from_attributes=True)


class VolunteerListItem(BaseModel):
    id: str
    name: str
    avatar: str
    role: Optional[str] = None
    available: bool = True
    team: Optional[str] = None
    contact: Optional[str] = None


class ApplicationCreate(BaseModel):
    role_id: int
    message: Optional[str] = None


class ApplicationResponse(BaseModel):
    id: int
    member_id: int
    role_id: int
    status: str
    message: Optional[str] = None
    applied_at: datetime
    reviewed_by: Optional[int] = None
    reviewed_at: Optional[datetime] = None
    review_notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ApplicationReview(BaseModel):
    status: str  # "approved" or "rejected"
    review_notes: Optional[str] = None


class HoursLogCreate(BaseModel):
    member_id: int
    role_id: Optional[int] = None
    event_id: Optional[int] = None
    hours_served: float
    date: date
    notes: Optional[str] = None


class HoursLogResponse(BaseModel):
    id: int
    member_id: int
    role_id: Optional[int] = None
    hours_served: float
    date: date
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# ── Roles ──

@router.get("/roles", response_model=List[VolunteerRoleResponse])
async def get_volunteer_roles(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all volunteer roles for the church."""
    result = await db.execute(
        select(VolunteerRole).where(
            VolunteerRole.church_id == current_user.church_id,
            VolunteerRole.is_active == True,
        )
    )
    return result.scalars().all()


@router.post("/roles", response_model=VolunteerRoleResponse, status_code=201)
async def create_volunteer_role(
    data: VolunteerRoleCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new volunteer role."""
    role = VolunteerRole(
        church_id=current_user.church_id,
        name=data.name,
        description=data.description,
        teams=data.teams,
        capacity_needed=data.capacity_needed,
    )
    db.add(role)
    await db.commit()
    await db.refresh(role)
    return role


# ── Schedules ──

@router.get("/schedules", response_model=List[VolunteerScheduleResponse])
async def get_volunteer_schedules(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get upcoming volunteer schedules."""
    result = await db.execute(
        select(VolunteerSchedule).where(VolunteerSchedule.church_id == current_user.church_id)
    )
    return result.scalars().all()


# ── Volunteer List ──

@router.get("/list", response_model=List[VolunteerListItem])
async def get_volunteer_list(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a list of members who are active volunteers."""
    result = await db.execute(
        select(VolunteerSchedule)
        .options(joinedload(VolunteerSchedule.member), joinedload(VolunteerSchedule.role))
        .where(VolunteerSchedule.church_id == current_user.church_id)
    )
    schedules = result.scalars().unique().all()

    volunteers_map = {}
    for s in schedules:
        m = s.member
        if not m:
            continue
        if str(m.id) not in volunteers_map:
            volunteers_map[str(m.id)] = VolunteerListItem(
                id=str(m.id),
                name=f"{m.first_name} {m.last_name}".strip(),
                avatar=m.avatar_url or m.photo_url or f"https://ui-avatars.com/api/?name={m.first_name}+{m.last_name}&background=random",
                role=s.role.name if s.role else None,
                available=True,
                team=s.role.teams if s.role and s.role.teams else "General",
                contact=m.email or m.phone or "N/A",
            )

    return list(volunteers_map.values())


# ── Applications ──

@router.post("/apply", response_model=ApplicationResponse, status_code=201)
async def apply_to_volunteer(
    data: ApplicationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit a volunteer application for a specific role."""
    # Find member linked to user
    member_id = current_user.member_id
    if not member_id:
        raise HTTPException(status_code=400, detail="No member profile linked to this user account")

    app = VolunteerApplication(
        church_id=current_user.church_id,
        member_id=member_id,
        role_id=data.role_id,
        message=data.message,
    )
    db.add(app)
    await db.commit()
    await db.refresh(app)
    return app


@router.get("/applications", response_model=List[ApplicationResponse])
async def list_applications(
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List volunteer applications (optionally filtered by status)."""
    query = select(VolunteerApplication).where(
        VolunteerApplication.church_id == current_user.church_id
    )
    if status_filter:
        query = query.where(VolunteerApplication.status == status_filter)
    query = query.order_by(VolunteerApplication.applied_at.desc())

    result = await db.execute(query)
    return result.scalars().all()


@router.put("/applications/{app_id}", response_model=ApplicationResponse)
async def review_application(
    app_id: int,
    data: ApplicationReview,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Approve or reject a volunteer application."""
    application = (await db.execute(
        select(VolunteerApplication).where(
            VolunteerApplication.id == app_id,
            VolunteerApplication.church_id == current_user.church_id,
        )
    )).scalar_one_or_none()

    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    application.status = data.status
    application.reviewed_by = current_user.id
    application.reviewed_at = datetime.now(timezone.utc)
    application.review_notes = data.review_notes
    db.add(application)
    await db.commit()
    await db.refresh(application)
    return application


# ── Hours Logging ──

@router.post("/hours", response_model=HoursLogResponse, status_code=201)
async def log_volunteer_hours(
    data: HoursLogCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Log volunteer hours served."""
    log = VolunteerHoursLog(
        church_id=current_user.church_id,
        member_id=data.member_id,
        role_id=data.role_id,
        event_id=data.event_id,
        hours_served=data.hours_served,
        date=data.date,
        notes=data.notes,
        logged_by=current_user.id,
    )
    db.add(log)
    await db.commit()
    await db.refresh(log)
    return log


@router.get("/hours", response_model=List[HoursLogResponse])
async def get_volunteer_hours(
    member_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get volunteer hours logs, optionally filtered by member."""
    query = select(VolunteerHoursLog).where(
        VolunteerHoursLog.church_id == current_user.church_id
    ).order_by(VolunteerHoursLog.date.desc())

    if member_id:
        query = query.where(VolunteerHoursLog.member_id == member_id)

    result = await db.execute(query)
    return result.scalars().all()


# ── Metrics & Retention ──

@router.get("/metrics")
async def get_volunteer_metrics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get aggregated volunteer metrics."""
    church_id = current_user.church_id
    now = datetime.now(timezone.utc)
    first_of_month = now.replace(day=1)
    thirty_days_ago = now - timedelta(days=30)

    # Active volunteers (distinct members with confirmed schedules)
    active_volunteers = (await db.execute(
        select(func.count(distinct(VolunteerSchedule.member_id))).where(
            VolunteerSchedule.church_id == church_id,
            VolunteerSchedule.status == "confirmed",
        )
    )).scalar() or 0

    # Total roles
    total_roles = (await db.execute(
        select(func.count(VolunteerRole.id)).where(
            VolunteerRole.church_id == church_id, VolunteerRole.is_active == True
        )
    )).scalar() or 0

    # Total hours served (MTD)
    hours_mtd = (await db.execute(
        select(func.coalesce(func.sum(VolunteerHoursLog.hours_served), 0)).where(
            VolunteerHoursLog.church_id == church_id,
            VolunteerHoursLog.date >= first_of_month.date(),
        )
    )).scalar() or 0

    # Pending applications
    pending_apps = (await db.execute(
        select(func.count(VolunteerApplication.id)).where(
            VolunteerApplication.church_id == church_id,
            VolunteerApplication.status == ApplicationStatus.PENDING.value,
        )
    )).scalar() or 0

    return {
        "active_volunteers": active_volunteers,
        "total_roles": total_roles,
        "hours_served": float(hours_mtd),
        "pending_applications": pending_apps,
    }


@router.get("/retention")
async def get_volunteer_retention(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Calculate volunteer retention rate over the last 90 days."""
    church_id = current_user.church_id
    now = date.today()
    ninety_days_ago = now - timedelta(days=90)
    one_eighty_days_ago = now - timedelta(days=180)

    # Volunteers active in last 90 days
    recent = (await db.execute(
        select(func.count(distinct(VolunteerHoursLog.member_id))).where(
            VolunteerHoursLog.church_id == church_id,
            VolunteerHoursLog.date >= ninety_days_ago,
        )
    )).scalar() or 0

    # Volunteers active 90-180 days ago
    previous = (await db.execute(
        select(func.count(distinct(VolunteerHoursLog.member_id))).where(
            VolunteerHoursLog.church_id == church_id,
            VolunteerHoursLog.date >= one_eighty_days_ago,
            VolunteerHoursLog.date < ninety_days_ago,
        )
    )).scalar() or 0

    retention_rate = (recent / previous * 100) if previous > 0 else 100.0

    return {
        "retention_rate": round(retention_rate, 1),
        "active_last_90d": recent,
        "active_prev_90d": previous,
    }
