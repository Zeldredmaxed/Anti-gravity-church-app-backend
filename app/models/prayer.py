"""Prayer request models."""

import enum
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Text,
    ForeignKey
)
from sqlalchemy.orm import relationship
from app.database import Base


class PrayerCategory(str, enum.Enum):
    HEALING = "healing"
    FAMILY = "family"
    FINANCIAL = "financial"
    SPIRITUAL_GROWTH = "spiritual_growth"
    RELATIONSHIP = "relationship"
    EMPLOYMENT = "employment"
    PRAISE_REPORT = "praise_report"
    OTHER = "other"


class PrayerVisibility(str, enum.Enum):
    PUBLIC = "public"
    CHURCH_ONLY = "church_only"
    LEADERS_ONLY = "leaders_only"


class PrayerRequest(Base):
    __tablename__ = "prayer_requests"

    id = Column(Integer, primary_key=True, index=True)
    church_id = Column(Integer, ForeignKey("churches.id"), nullable=False, index=True)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(30), default=PrayerCategory.OTHER.value, nullable=False)
    is_anonymous = Column(Boolean, default=False)
    is_urgent = Column(Boolean, default=False)
    is_answered = Column(Boolean, default=False)
    answered_testimony = Column(Text, nullable=True)
    prayed_count = Column(Integer, default=0)
    visibility = Column(String(20), default=PrayerVisibility.CHURCH_ONLY.value, nullable=False)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    author = relationship("User")
    responses = relationship("PrayerResponseEntry", back_populates="prayer_request",
                              cascade="all, delete-orphan")


class PrayerResponseEntry(Base):
    __tablename__ = "prayer_responses"

    id = Column(Integer, primary_key=True, index=True)
    prayer_request_id = Column(Integer, ForeignKey("prayer_requests.id", ondelete="CASCADE"),
                                nullable=False, index=True)
    responder_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    content = Column(Text, nullable=True)  # Encouragement message (optional)
    is_prayed = Column(Boolean, default=True)  # "I prayed for this"
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    prayer_request = relationship("PrayerRequest", back_populates="responses")
    responder = relationship("User")
