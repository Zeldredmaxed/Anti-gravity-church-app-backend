"""Shorts system models — cross-church video platform."""

import enum
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Text,
    ForeignKey, JSON, UniqueConstraint
)
from sqlalchemy.orm import relationship
from app.database import Base


class GloryClipCategory(str, enum.Enum):
    WORSHIP = "worship"
    TESTIMONY = "testimony"
    SERMON_CLIP = "sermon_clip"
    DEVOTIONAL = "devotional"
    COMEDY = "comedy"
    PRAISE = "praise"
    TUTORIAL = "tutorial"
    OTHER = "other"


class ModerationStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class GloryClip(Base):
    __tablename__ = "glory_clips"

    id = Column(Integer, primary_key=True, index=True)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    church_id = Column(Integer, ForeignKey("churches.id"), nullable=False, index=True)  # Attribution, not isolation
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    video_url = Column(String(500), nullable=False)
    thumbnail_url = Column(String(500), nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    category = Column(String(30), default=GloryClipCategory.OTHER.value, nullable=False)
    moderation_status = Column(String(20), default=ModerationStatus.APPROVED.value, nullable=False)
    view_count = Column(Integer, default=0)
    amen_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    share_count = Column(Integer, default=0)
    is_featured = Column(Boolean, default=False)
    tags = Column(JSON, default=list)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    author = relationship("User")
    church = relationship("Church")
    amens = relationship("GloryClipAmen", back_populates="glory_clip", cascade="all, delete-orphan")
    comments = relationship("GloryClipComment", back_populates="glory_clip",
                             lazy="dynamic", cascade="all, delete-orphan")
    views = relationship("GloryClipView", back_populates="glory_clip", cascade="all, delete-orphan")


class GloryClipAmen(Base):
    __tablename__ = "glory_clip_amens"
    __table_args__ = (
        UniqueConstraint("glory_clip_id", "user_id", name="uq_glory_clip_amen"),
    )

    id = Column(Integer, primary_key=True, index=True)
    glory_clip_id = Column(Integer, ForeignKey("glory_clips.id", ondelete="CASCADE"),
                       nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    glory_clip = relationship("GloryClip", back_populates="amens")
    user = relationship("User")


class GloryClipComment(Base):
    __tablename__ = "glory_clip_comments"

    id = Column(Integer, primary_key=True, index=True)
    glory_clip_id = Column(Integer, ForeignKey("glory_clips.id", ondelete="CASCADE"),
                       nullable=False, index=True)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    parent_id = Column(Integer, ForeignKey("glory_clip_comments.id"), nullable=True)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    glory_clip = relationship("GloryClip", back_populates="comments")
    author = relationship("User")
    replies = relationship("GloryClipComment", backref="parent", remote_side=[id])


class GloryClipView(Base):
    __tablename__ = "glory_clip_views"

    id = Column(Integer, primary_key=True, index=True)
    glory_clip_id = Column(Integer, ForeignKey("glory_clips.id", ondelete="CASCADE"),
                       nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    watched_seconds = Column(Integer, default=0)
    completed = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    glory_clip = relationship("GloryClip", back_populates="views")
