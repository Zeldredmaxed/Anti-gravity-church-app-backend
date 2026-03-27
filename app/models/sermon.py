"""Sermon & media library models — recordings, Bible studies, live streams."""

from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Text, Date,
    ForeignKey, JSON
)
from sqlalchemy.orm import relationship
from app.database import Base


class Sermon(Base):
    __tablename__ = "sermons"

    id = Column(Integer, primary_key=True, index=True)
    church_id = Column(Integer, ForeignKey("churches.id"), nullable=False, index=True)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    speaker = Column(String(150), nullable=True)
    series_name = Column(String(200), nullable=True)
    scripture_reference = Column(String(200), nullable=True)

    # Video source
    video_url = Column(String(500), nullable=True)
    video_type = Column(String(30), default="upload")       # upload, youtube, zoom, vimeo, facebook
    youtube_video_id = Column(String(50), nullable=True, index=True)
    thumbnail_url = Column(String(500), nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    transcript = Column(Text, nullable=True)

    # Live
    is_live = Column(Boolean, default=False, index=True)
    live_started_at = Column(DateTime(timezone=True), nullable=True)

    # Engagement
    view_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)

    # Organization
    recorded_date = Column(Date, nullable=True)
    tags = Column(JSON, default=list)
    is_published = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    church = relationship("Church")
    uploader = relationship("User")
    notes = relationship("SermonNote", back_populates="sermon", cascade="all, delete-orphan")


class SermonNote(Base):
    __tablename__ = "sermon_notes"

    id = Column(Integer, primary_key=True, index=True)
    sermon_id = Column(Integer, ForeignKey("sermons.id", ondelete="CASCADE"),
                       nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    church_id = Column(Integer, ForeignKey("churches.id"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    timestamp_marker = Column(Integer, nullable=True)       # seconds into sermon

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    sermon = relationship("Sermon", back_populates="notes")
    user = relationship("User")
