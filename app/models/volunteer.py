"""Volunteer ministry scheduling and roles."""

from datetime import datetime, timezone, date
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Date, Text, ForeignKey,
)
from sqlalchemy.orm import relationship
from app.database import Base


class VolunteerRole(Base):
    __tablename__ = "volunteer_roles"

    id = Column(Integer, primary_key=True, index=True)
    church_id = Column(Integer, ForeignKey("churches.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False) # e.g. "Usher", "Choir", "Camera Operator"
    description = Column(Text, nullable=True)
    
    # Relationships
    church = relationship("Church")
    schedules = relationship("VolunteerSchedule", back_populates="role", lazy="dynamic")


class VolunteerSchedule(Base):
    __tablename__ = "volunteer_schedules"

    id = Column(Integer, primary_key=True, index=True)
    church_id = Column(Integer, ForeignKey("churches.id"), nullable=False, index=True)
    role_id = Column(Integer, ForeignKey("volunteer_roles.id"), nullable=False)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False)
    
    # Assignments can be to either a specific event, or a service (Sunday morning etc)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=True)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=True)
    
    # Status of the assignment
    status = Column(String(50), default="pending") # pending, accepted, declined, pending_swap
    
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
