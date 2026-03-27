"""Child checking and family security models."""

from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Text, ForeignKey,
)
from sqlalchemy.orm import relationship
from app.database import Base


class CheckinSession(Base):
    __tablename__ = "checkin_sessions"

    id = Column(Integer, primary_key=True, index=True)
    church_id = Column(Integer, ForeignKey("churches.id"), nullable=False, index=True)
    child_id = Column(Integer, ForeignKey("members.id"), nullable=False, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=True) # Optional link to a specific event/service
    service_id = Column(Integer, ForeignKey("services.id"), nullable=True) # Optional link to service
    
    # Security
    parent_matching_id = Column(String(50), nullable=False, index=True) # Security code on tags
    
    # Times
    checkin_time = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    checkout_time = Column(DateTime(timezone=True), nullable=True)
    
    # Specifics for this session
    room_assignment = Column(String(100), nullable=True)
    alerts = Column(Text, nullable=True) # Copied from member profile or entered at checkin
    checked_in_by = Column(Integer, ForeignKey("users.id"), nullable=True) # Staff/volunteer who processed it
    checked_out_by = Column(Integer, ForeignKey("users.id"), nullable=True) # Staff/volunteer who processed it
    
    # Relationships
    church = relationship("Church")
    child = relationship("Member", foreign_keys=[child_id])
    checked_in_by_user = relationship("User", foreign_keys=[checked_in_by])
    checked_out_by_user = relationship("User", foreign_keys=[checked_out_by])
    event = relationship("Event")
    service = relationship("Service")
