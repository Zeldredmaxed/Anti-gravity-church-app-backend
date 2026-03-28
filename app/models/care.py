"""Care model for tracking care/hospital/prayer cases."""

import enum
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Text, ForeignKey, DateTime, Boolean
)
from sqlalchemy.orm import relationship
from app.database import Base


class CareCase(Base):
    __tablename__ = "care_cases"

    id = Column(Integer, primary_key=True, index=True)
    church_id = Column(Integer, ForeignKey("churches.id", ondelete="CASCADE"), nullable=False, index=True)
    
    requester_name = Column(String(255), nullable=False)
    requester_avatar = Column(String(500), nullable=True)
    
    # "Prayer" or "Care" etc.
    care_type = Column(String(50), nullable=False)
    
    # "Hospital Visit", "Healing", "Meals", "Financial"
    sub_type = Column(String(100), nullable=True)
    
    summary = Column(Text, nullable=False)
    
    assigned_leader_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    status = Column(String(50), default="NEW", nullable=False)  # NEW, IN-PROGRESS, NEEDS LEADER, COMPLETED

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    is_deleted = Column(Boolean, default=False)
    
    assigned_leader = relationship("User", foreign_keys=[assigned_leader_id])
    church = relationship("Church")
