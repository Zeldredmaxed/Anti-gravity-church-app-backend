"""Pydantic schemas for attendance tracking."""

from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime


class ServiceCreate(BaseModel):
    name: str
    service_type: str = "sunday_morning"
    day_of_week: Optional[str] = None
    start_time: Optional[str] = None
    campus: Optional[str] = None


class ServiceResponse(BaseModel):
    id: int
    name: str
    service_type: str
    day_of_week: Optional[str] = None
    start_time: Optional[str] = None
    campus: Optional[str] = None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class CheckInRequest(BaseModel):
    member_id: Optional[int] = None
    service_id: int
    date: date
    is_first_time_guest: bool = False
    guest_info: Optional[dict] = None  # name, phone, email for unregistered guests


class CheckOutRequest(BaseModel):
    attendance_record_id: int


class AttendanceResponse(BaseModel):
    id: int
    member_id: Optional[int] = None
    member_name: Optional[str] = None
    service_id: int
    service_name: Optional[str] = None
    date: date
    check_in_time: Optional[datetime] = None
    check_out_time: Optional[datetime] = None
    is_first_time_guest: bool
    guest_info: Optional[dict] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AttendanceSummary(BaseModel):
    date: date
    service_name: str
    total_count: int
    member_count: int
    guest_count: int
    first_time_guest_count: int


class AttendanceTrend(BaseModel):
    period: str  # date or week or month label
    total: int
    members: int
    guests: int


class AbsenteeReport(BaseModel):
    member_id: int
    member_name: str
    last_attended: Optional[date] = None
    weeks_absent: int
    membership_status: str


class GroupAttendanceCreate(BaseModel):
    group_id: int
    member_ids: List[int]
    date: date
