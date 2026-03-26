"""Attendance tracking router: check-in/out, trends, absentees, guests."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import Optional
from datetime import date, datetime, timezone, timedelta

from app.database import get_db
from app.models.attendance import Service, AttendanceRecord, GroupAttendance
from app.models.member import Member
from app.models.user import User
from app.schemas.attendance import (
    ServiceCreate, ServiceResponse, CheckInRequest, CheckOutRequest,
    AttendanceResponse, AttendanceSummary, AttendanceTrend,
    AbsenteeReport, GroupAttendanceCreate,
)
from app.utils.security import get_current_user, require_role
from app.dependencies import PaginationParams

router = APIRouter(prefix="/attendance", tags=["Attendance"])


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
@router.post("/groups", status_code=201)
async def record_group_attendance(data: GroupAttendanceCreate,
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    recorded = 0
    for mid in data.member_ids:
        ga = GroupAttendance(group_id=data.group_id, member_id=mid,
                             date=data.date, recorded_by=current_user.id)
        db.add(ga); recorded += 1
    await db.flush()
    return {"recorded": recorded, "group_id": data.group_id, "date": data.date.isoformat()}
