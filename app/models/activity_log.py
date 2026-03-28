"""Member activity timeline — records major events on a member's profile."""

import enum
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, DateTime, Text, ForeignKey, JSON,
)
from sqlalchemy.orm import relationship
from app.database import Base


class ActivityType(str, enum.Enum):
    BAPTISM = "baptism"
    JOINED_GROUP = "joined_group"
    LEFT_GROUP = "left_group"
    DONATION = "donation"
    ATTENDANCE = "attendance"
    MILESTONE = "milestone"
    MEMBERSHIP_CHANGE = "membership_change"
    VOLUNTEER_STARTED = "volunteer_started"
    CARE_CASE_OPENED = "care_case_opened"
    CUSTOM = "custom"


class MemberActivityLog(Base):
    """Chronological activity timeline for each member profile."""
    __tablename__ = "member_activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    church_id = Column(Integer, ForeignKey("churches.id"), nullable=False, index=True)
    member_id = Column(Integer, ForeignKey("members.id", ondelete="CASCADE"), nullable=False, index=True)

    activity_type = Column(String(50), nullable=False)  # From ActivityType enum
    description = Column(Text, nullable=False)           # "Baptized on 2026-03-15"
    metadata_json = Column(JSON, nullable=True)           # Extra context: {group_name: "Youth", ...}

    occurred_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    logged_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    member = relationship("Member", back_populates="activity_logs")
    logger = relationship("User", foreign_keys=[logged_by])
