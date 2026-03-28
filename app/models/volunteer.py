"""Volunteer ministry scheduling, roles, applications, and hours tracking."""

import enum
from datetime import datetime, timezone, date
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Date, Text, ForeignKey, Numeric,
)
from sqlalchemy.orm import relationship
from app.database import Base


class VolunteerRole(Base):
    __tablename__ = "volunteer_roles"

    id = Column(Integer, primary_key=True, index=True)
    church_id = Column(Integer, ForeignKey("churches.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)  # e.g. "Usher", "Choir", "Camera Operator"
    description = Column(Text, nullable=True)
    teams = Column(String(255), nullable=True)  # e.g. "Worship Team", "Media Team"
    capacity_needed = Column(Integer, nullable=True)  # How many volunteers needed
    is_active = Column(Boolean, default=True)

    # Relationships
    church = relationship("Church")
    schedules = relationship("VolunteerSchedule", back_populates="role", lazy="dynamic")
    applications = relationship("VolunteerApplication", back_populates="role", lazy="dynamic")
    hours_logs = relationship("VolunteerHoursLog", back_populates="role", lazy="dynamic")


class VolunteerSchedule(Base):
    __tablename__ = "volunteer_schedules"

    id = Column(Integer, primary_key=True, index=True)
    church_id = Column(Integer, ForeignKey("churches.id"), nullable=False, index=True)
    role_id = Column(Integer, ForeignKey("volunteer_roles.id"), nullable=False)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False)

    # Assignments can be to either a specific event, or a service
    event_id = Column(Integer, ForeignKey("events.id"), nullable=True)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=True)

    # Shift times
    start_time = Column(DateTime(timezone=True), nullable=True)
    end_time = Column(DateTime(timezone=True), nullable=True)

    # Status of the assignment
    status = Column(String(50), default="pending")  # pending, confirmed, declined, pending_swap
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    church = relationship("Church")
    role = relationship("VolunteerRole", back_populates="schedules")
    member = relationship("Member")
    event = relationship("Event")
    service = relationship("Service")


class VolunteerAvailability(Base):
    __tablename__ = "volunteer_availabilities"

    id = Column(Integer, primary_key=True, index=True)
    church_id = Column(Integer, ForeignKey("churches.id"), nullable=False, index=True)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False)

    # Block out dates
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    reason = Column(String(255), nullable=True)

    # Relationships
    church = relationship("Church")
    member = relationship("Member")


class ApplicationStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ON_BREAK = "on_break"


class VolunteerApplication(Base):
    """Track volunteer applications — members apply to serve in specific roles."""
    __tablename__ = "volunteer_applications"

    id = Column(Integer, primary_key=True, index=True)
    church_id = Column(Integer, ForeignKey("churches.id"), nullable=False, index=True)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False, index=True)
    role_id = Column(Integer, ForeignKey("volunteer_roles.id"), nullable=False, index=True)
    status = Column(String(20), default=ApplicationStatus.PENDING.value, nullable=False)
    message = Column(Text, nullable=True)  # Applicant cover message
    applied_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    review_notes = Column(Text, nullable=True)

    # Relationships
    church = relationship("Church")
    member = relationship("Member")
    role = relationship("VolunteerRole", back_populates="applications")
    reviewer = relationship("User", foreign_keys=[reviewed_by])


class VolunteerHoursLog(Base):
    """Log actual hours served by volunteers for tracking & retention metrics."""
    __tablename__ = "volunteer_hours_logs"

    id = Column(Integer, primary_key=True, index=True)
    church_id = Column(Integer, ForeignKey("churches.id"), nullable=False, index=True)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False, index=True)
    role_id = Column(Integer, ForeignKey("volunteer_roles.id"), nullable=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=True)
    hours_served = Column(Numeric(6, 2), nullable=False)
    date = Column(Date, nullable=False, index=True)
    notes = Column(Text, nullable=True)
    logged_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    church = relationship("Church")
    member = relationship("Member")
    role = relationship("VolunteerRole", back_populates="hours_logs")
    event = relationship("Event")
