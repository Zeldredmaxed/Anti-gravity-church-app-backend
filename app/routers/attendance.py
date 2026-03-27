"""Attendance tracking router: check-in/out, trends, absentees, guests, Sunday geo-check-in."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import Optional
from datetime import date, datetime, timezone, timedelta
import math

from app.database import get_db
from app.models.attendance import Service, AttendanceRecord, GroupAttendance
from app.models.sunday_checkin import SundayCheckIn
from app.models.church import Church
from app.models.member import Member
from app.models.user import User
from app.schemas.attendance import (
    ServiceCreate, ServiceResponse, CheckInRequest, CheckOutRequest,
    AttendanceResponse, AttendanceSummary, AttendanceTrend,
    AbsenteeReport, GroupAttendanceCreate,
)
from app.utils.security import get_current_user, require_role
from app.dependencies import PaginationParams
from pydantic import BaseModel, Field

router = APIRouter(prefix="/attendance", tags=["Attendance"])


# ── Haversine distance (miles) ────────────────────────────────────
def _haversine_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two lat/lng points in miles."""
    R = 3958.8  # Earth radius in miles
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ── Pydantic schema for Sunday check-in ──────────────────────────
class SundayCheckInRequest(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)


# --- Services ---
@router.get("/services", response_model=list[ServiceResponse])
async def list_services(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return (await db.execute(select(Service).order_by(Service.name))).scalars().all()


@router.post("/services", response_model=ServiceResponse, status_code=201)
async def create_service(data: ServiceCreate,
    current_user: User = Depends(require_role("admin", "pastor")), db: AsyncSession = Depends(get_db)):
    svc = Service(**data.model_dump()); db.add(svc); await db.flush(); await db.refresh(svc)
    return svc


# --- Check-in/out ---
@router.post("/checkin", response_model=AttendanceResponse, status_code=201)
async def check_in(data: CheckInRequest,
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = (await db.execute(select(Service).where(Service.id == data.service_id))).scalar_one_or_none()
    if not svc: raise HTTPException(status_code=404, detail="Service not found")
    record = AttendanceRecord(
        member_id=data.member_id, service_id=data.service_id, date=data.date,
        check_in_time=datetime.now(timezone.utc), checked_in_by=current_user.id,
        is_first_time_guest=data.is_first_time_guest, guest_info=data.guest_info,
    )
    db.add(record); await db.flush(); await db.refresh(record)
    name = None
    if record.member_id:
        m = (await db.execute(select(Member).where(Member.id == record.member_id))).scalar_one_or_none()
        if m: name = f"{m.first_name} {m.last_name}"
    return AttendanceResponse(
        id=record.id, member_id=record.member_id, member_name=name,
        service_id=record.service_id, service_name=svc.name, date=record.date,
        check_in_time=record.check_in_time, check_out_time=record.check_out_time,
        is_first_time_guest=record.is_first_time_guest, guest_info=record.guest_info,
        created_at=record.created_at)


@router.post("/checkout")
async def check_out(data: CheckOutRequest, db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)):
    record = (await db.execute(select(AttendanceRecord).where(
        AttendanceRecord.id == data.attendance_record_id))).scalar_one_or_none()
    if not record: raise HTTPException(status_code=404, detail="Record not found")
    record.check_out_time = datetime.now(timezone.utc)
    db.add(record)
    return {"message": "Checked out", "check_out_time": record.check_out_time.isoformat()}


# --- Queries ---
@router.get("/service/{service_id}", response_model=list[AttendanceResponse])
async def get_service_attendance(service_id: int, attendance_date: date = Query(...),
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    svc = (await db.execute(select(Service).where(Service.id == service_id))).scalar_one_or_none()
    if not svc: raise HTTPException(status_code=404, detail="Service not found")
    records = (await db.execute(select(AttendanceRecord).where(
        AttendanceRecord.service_id == service_id, AttendanceRecord.date == attendance_date)
    )).scalars().all()
    items = []
    for r in records:
        name = None
        if r.member_id:
            m = (await db.execute(select(Member).where(Member.id == r.member_id))).scalar_one_or_none()
            if m: name = f"{m.first_name} {m.last_name}"
        items.append(AttendanceResponse(
            id=r.id, member_id=r.member_id, member_name=name,
            service_id=r.service_id, service_name=svc.name, date=r.date,
            check_in_time=r.check_in_time, check_out_time=r.check_out_time,
            is_first_time_guest=r.is_first_time_guest, guest_info=r.guest_info,
            created_at=r.created_at))
    return items


@router.get("/member/{member_id}", response_model=list[AttendanceResponse])
async def get_member_attendance(member_id: int, db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)):
    records = (await db.execute(select(AttendanceRecord).where(
        AttendanceRecord.member_id == member_id).order_by(AttendanceRecord.date.desc()).limit(50)
    )).scalars().all()
    items = []
    for r in records:
        svc = (await db.execute(select(Service).where(Service.id == r.service_id))).scalar_one_or_none()
        items.append(AttendanceResponse(
            id=r.id, member_id=r.member_id, member_name=None,
            service_id=r.service_id, service_name=svc.name if svc else None,
            date=r.date, check_in_time=r.check_in_time, check_out_time=r.check_out_time,
            is_first_time_guest=r.is_first_time_guest, guest_info=r.guest_info,
            created_at=r.created_at))
    return items


@router.get("/trends", response_model=list[AttendanceTrend])
async def attendance_trends(weeks: int = Query(12, ge=1, le=52),
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    trends = []
    today = date.today()
    for i in range(weeks):
        week_start = today - timedelta(days=today.weekday() + 7 * i)
        week_end = week_start + timedelta(days=6)
        total = (await db.execute(select(func.count()).where(
            AttendanceRecord.date >= week_start, AttendanceRecord.date <= week_end))).scalar() or 0
        members = (await db.execute(select(func.count()).where(
            AttendanceRecord.date >= week_start, AttendanceRecord.date <= week_end,
            AttendanceRecord.member_id.isnot(None)))).scalar() or 0
        guests = total - members
        trends.append(AttendanceTrend(
            period=f"{week_start.isoformat()} to {week_end.isoformat()}",
            total=total, members=members, guests=guests))
    trends.reverse()
    return trends


@router.get("/absentees", response_model=list[AbsenteeReport])
async def get_absentees(weeks: int = Query(3, ge=1, le=12),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "pastor", "staff"))):
    cutoff = date.today() - timedelta(weeks=weeks)
    members = (await db.execute(select(Member).where(
        Member.is_deleted == False, Member.membership_status.in_(["active", "member"])))).scalars().all()
    absentees = []
    for m in members:
        last = (await db.execute(select(func.max(AttendanceRecord.date)).where(
            AttendanceRecord.member_id == m.id))).scalar()
        if last is None or last < cutoff:
            weeks_absent = (date.today() - last).days // 7 if last else 999
            absentees.append(AbsenteeReport(
                member_id=m.id, member_name=f"{m.first_name} {m.last_name}",
                last_attended=last, weeks_absent=weeks_absent,
                membership_status=m.membership_status))
    absentees.sort(key=lambda x: x.weeks_absent, reverse=True)
    return absentees


@router.get("/first-time-guests", response_model=list[AttendanceResponse])
async def first_time_guests(days: int = Query(30, ge=1, le=90),
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    cutoff = date.today() - timedelta(days=days)
    records = (await db.execute(select(AttendanceRecord).where(
        AttendanceRecord.is_first_time_guest == True, AttendanceRecord.date >= cutoff)
        .order_by(AttendanceRecord.date.desc()))).scalars().all()
    return [AttendanceResponse(
        id=r.id, member_id=r.member_id, member_name=None,
        service_id=r.service_id, service_name=None, date=r.date,
        check_in_time=r.check_in_time, check_out_time=r.check_out_time,
        is_first_time_guest=True, guest_info=r.guest_info, created_at=r.created_at
    ) for r in records]


# --- Group Attendance ---
@router.post("/group/check-in", status_code=201)
async def record_group_attendance(data: GroupAttendanceCreate,
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    recorded = 0
    # verify group exists
    from app.models.group import Group
    g = (await db.execute(select(Group).where(Group.id == data.group_id, Group.church_id == current_user.church_id))).scalar_one_or_none()
    if not g:
        raise HTTPException(status_code=404, detail="Group not found")
        
    # Prevent duplicate records
    for mid in data.member_ids:
        existing = (await db.execute(select(GroupAttendance).where(
            GroupAttendance.group_id == data.group_id,
            GroupAttendance.member_id == mid,
            GroupAttendance.date == data.date
        ))).scalar_one_or_none()
        if not existing:
            ga = GroupAttendance(group_id=data.group_id, member_id=mid,
                                church_id=current_user.church_id,
                                date=data.date, recorded_by=current_user.id)
            db.add(ga); recorded += 1
    await db.commit()
    return {"recorded": recorded, "group_id": data.group_id, "date": data.date.isoformat()}


@router.get("/group/{group_id}/metrics")
async def get_group_metrics(group_id: int, 
    current_user: User = Depends(require_role("admin", "pastor", "ministry_leader")),
    db: AsyncSession = Depends(get_db)):
    
    # 1. Total unique attendees across all time
    unique_attendees = (await db.execute(
        select(func.count(func.distinct(GroupAttendance.member_id)))
        .where(GroupAttendance.group_id == group_id)
    )).scalar() or 0
    
    # 2. Average attendance per session (last 12 sessions)
    sessions = (await db.execute(
        select(func.count(GroupAttendance.id))
        .where(GroupAttendance.group_id == group_id)
        .group_by(GroupAttendance.date)
        .order_by(GroupAttendance.date.desc())
        .limit(12)
    )).scalars().all()
    avg_attendance = sum(sessions) / len(sessions) if sessions else 0
    
    return {
        "group_id": group_id,
        "metrics": {
            "total_unique_attendees": unique_attendees,
            "average_session_attendance": round(avg_attendance, 1),
            "total_sessions_recorded": len(sessions)
        }
    }



# ═══════════════════════════════════════════════════════════════════
# GEO-BASED SUNDAY ATTENDANCE
# ═══════════════════════════════════════════════════════════════════

MAX_CHECKIN_DISTANCE_MILES = 0.5  # Half mile radius


@router.post("/sunday-checkin", status_code=201)
async def sunday_checkin(
    data: SundayCheckInRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Geo-verify Sunday church attendance.

    The frontend should call this on Sundays around 12:15 PM.
    The backend checks if the user is within 0.5 miles of their church.
    """
    if not current_user.church_id:
        raise HTTPException(status_code=400, detail="You must belong to a church to check in")

    church = (await db.execute(
        select(Church).where(Church.id == current_user.church_id)
    )).scalar_one_or_none()
    if not church:
        raise HTTPException(status_code=404, detail="Church not found")
    if church.latitude is None or church.longitude is None:
        raise HTTPException(status_code=400, detail="Church location has not been set by the pastor")

    # Calculate distance
    distance = _haversine_miles(data.latitude, data.longitude, church.latitude, church.longitude)
    if distance > MAX_CHECKIN_DISTANCE_MILES:
        raise HTTPException(
            status_code=400,
            detail=f"You are {distance:.2f} miles from church. Must be within {MAX_CHECKIN_DISTANCE_MILES} miles to check in."
        )

    today = date.today()

    # Prevent duplicate check-in for same day
    existing = (await db.execute(select(SundayCheckIn).where(
        SundayCheckIn.user_id == current_user.id,
        SundayCheckIn.check_in_date == today,
    ))).scalar_one_or_none()
    if existing:
        return {"data": {"message": "Already checked in today", "distance_miles": round(distance, 3)}}

    checkin = SundayCheckIn(
        user_id=current_user.id,
        church_id=current_user.church_id,
        check_in_date=today,
        latitude=data.latitude,
        longitude=data.longitude,
        distance_miles=round(distance, 4),
        year=today.year,
    )
    db.add(checkin)
    await db.flush()

    # Get updated year count
    year_count = (await db.execute(select(func.count()).where(
        SundayCheckIn.user_id == current_user.id,
        SundayCheckIn.year == today.year,
    ))).scalar() or 0

    return {"data": {
        "message": "Church attendance recorded!",
        "distance_miles": round(distance, 3),
        "sundays_this_year": year_count,
    }}


@router.get("/my-sundays")
async def my_sundays(
    year: int = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return the authenticated user's Sunday attendance history and year stats."""
    target_year = year or date.today().year

    # This year's check-ins
    checkins = (await db.execute(
        select(SundayCheckIn)
        .where(SundayCheckIn.user_id == current_user.id, SundayCheckIn.year == target_year)
        .order_by(SundayCheckIn.check_in_date.desc())
    )).scalars().all()

    # Last year's total for comparison
    last_year_count = (await db.execute(select(func.count()).where(
        SundayCheckIn.user_id == current_user.id,
        SundayCheckIn.year == target_year - 1,
    ))).scalar() or 0

    # All-time best year
    best_year_row = (await db.execute(
        select(SundayCheckIn.year, func.count().label("cnt"))
        .where(SundayCheckIn.user_id == current_user.id)
        .group_by(SundayCheckIn.year)
        .order_by(func.count().desc())
        .limit(1)
    )).first()

    return {"data": {
        "year": target_year,
        "sundays_attended": len(checkins),
        "last_year_total": last_year_count,
        "best_year": best_year_row[0] if best_year_row else None,
        "best_year_count": best_year_row[1] if best_year_row else 0,
        "on_track_to_beat_last_year": len(checkins) > last_year_count,
        "dates": [c.check_in_date.isoformat() for c in checkins],
    }}


@router.get("/sunday-stats/{user_id}")
async def sunday_stats_for_user(
    user_id: int,
    year: int = Query(None),
    current_user: User = Depends(require_role("admin", "pastor")),
    db: AsyncSession = Depends(get_db),
):
    """Pastor view — see any member's Sunday attendance stats."""
    target_year = year or date.today().year

    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    count = (await db.execute(select(func.count()).where(
        SundayCheckIn.user_id == user_id,
        SundayCheckIn.year == target_year,
    ))).scalar() or 0

    last_year_count = (await db.execute(select(func.count()).where(
        SundayCheckIn.user_id == user_id,
        SundayCheckIn.year == target_year - 1,
    ))).scalar() or 0

    dates = (await db.execute(
        select(SundayCheckIn.check_in_date)
        .where(SundayCheckIn.user_id == user_id, SundayCheckIn.year == target_year)
        .order_by(SundayCheckIn.check_in_date.desc())
    )).scalars().all()

    return {"data": {
        "user_id": user_id,
        "user_name": user.full_name,
        "year": target_year,
        "sundays_attended": count,
        "last_year_total": last_year_count,
        "on_track": count > last_year_count,
        "dates": [d.isoformat() for d in dates],
    }}
