"""Care model for tracking care/hospital/prayer cases with follow-up notes."""

import enum
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Text, ForeignKey, DateTime, Boolean
)
from sqlalchemy.orm import relationship
from app.database import Base


class CasePriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class CaseStatus(str, enum.Enum):
    NEW = "NEW"
    IN_PROGRESS = "IN-PROGRESS"
    NEEDS_LEADER = "NEEDS LEADER"
    COMPLETED = "COMPLETED"
    CLOSED = "CLOSED"


class CareCase(Base):
    __tablename__ = "care_cases"

    id = Column(Integer, primary_key=True, index=True)
    church_id = Column(Integer, ForeignKey("churches.id", ondelete="CASCADE"), nullable=False, index=True)

    requester_name = Column(String(255), nullable=False)
    requester_avatar = Column(String(500), nullable=True)

    # Link to actual member profile
    member_id = Column(Integer, ForeignKey("members.id", ondelete="SET NULL"), nullable=True, index=True)

    # "Prayer" or "Care" etc.
    care_type = Column(String(50), nullable=False)

    # "Hospital Visit", "Healing", "Meals", "Financial"
    sub_type = Column(String(100), nullable=True)

    summary = Column(Text, nullable=False)

    assigned_leader_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Priority
    priority = Column(String(20), default=CasePriority.MEDIUM.value, nullable=False)

    status = Column(String(50), default=CaseStatus.NEW.value, nullable=False)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    is_deleted = Column(Boolean, default=False)

    # Relationships
    assigned_leader = relationship("User", foreign_keys=[assigned_leader_id])
    church = relationship("Church")
    member = relationship("Member")
    notes = relationship("CareNote", back_populates="care_case", cascade="all, delete-orphan", lazy="selectin")


class CareNote(Base):
    """Follow-up notes on a care case — tracks every interaction."""
    __tablename__ = "care_notes"

    id = Column(Integer, primary_key=True, index=True)
    care_case_id = Column(Integer, ForeignKey("care_cases.id", ondelete="CASCADE"), nullable=False, index=True)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    action_taken = Column(String(100), nullable=True)  # e.g. "Phone Call", "Home Visit", "SMS Sent"
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    care_case = relationship("CareCase", back_populates="notes")
    author = relationship("User")
