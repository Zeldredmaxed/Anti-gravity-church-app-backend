"""Service Scripture model — pastor's verse for the congregation."""

from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Text, Date,
    ForeignKey
)
from sqlalchemy.orm import relationship
from app.database import Base


class ServiceScripture(Base):
    __tablename__ = "service_scriptures"

    id = Column(Integer, primary_key=True, index=True)
    church_id = Column(Integer, ForeignKey("churches.id"), nullable=False, index=True)
    set_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    title = Column(String(255), nullable=True)              # e.g., "Sunday Morning Service"
    book = Column(String(50), nullable=False)               # e.g., "John"
    chapter = Column(Integer, nullable=False)               # e.g., 3
    verse_start = Column(Integer, nullable=False)           # e.g., 16
    verse_end = Column(Integer, nullable=True)              # e.g., 17 (null = single verse)
    pastor_notes = Column(Text, nullable=True)              # pastor's commentary

    is_active = Column(Boolean, default=True, index=True)   # only one active per church
    service_date = Column(Date, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    church = relationship("Church")
    set_by = relationship("User")
