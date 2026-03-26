"""Attendance tracking models for services, groups, and events."""

import enum
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Date, Time,
    ForeignKey, JSON
)
from sqlalchemy.orm import relationship
from app.database import Base


class ServiceType(str, enum.Enum):
    SUNDAY_MORNING = "sunday_morning"
    SUNDAY_EVENING = "sunday_evening"
    WEDNESDAY = "wednesday"
    FRIDAY = "friday"
    SPECIAL = "special"
    REVIVAL = "revival"
    CONFERENCE = "conference"


class Service(Base):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)
    church_id = Column(Integer, ForeignKey("churches.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    service_type = Column(String(30), default=ServiceType.SUNDAY_MORNING.value, nullable=False)
    day_of_week = Column(String(15), nullable=True)
    start_time = Column(String(10), nullable=True)
    campus = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    attendance_records = relationship("AttendanceRecord", back_populates="service", lazy="dynamic")


class AttendanceRecord(Base):
    __tablename__ = "attendance_records"

    id = Column(Integer, primary_key=True, index=True)
    church_id = Column(Integer, ForeignKey("churches.id"), nullable=False, index=True)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=True, index=True)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    check_in_time = Column(DateTime(timezone=True), nullable=True)
    check_out_time = Column(DateTime(timezone=True), nullable=True)
    checked_in_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    is_first_time_guest = Column(Boolean, default=False)
    guest_info = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    member = relationship("Member", back_populates="attendance_records")
    service = relationship("Service", back_populates="attendance_records")


class GroupAttendance(Base):
    __tablename__ = "group_attendance"

    id = Column(Integer, primary_key=True, index=True)
    church_id = Column(Integer, ForeignKey("churches.id"), nullable=False, index=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False, index=True)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    recorded_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    group = relationship("Group", back_populates="attendance_records")
