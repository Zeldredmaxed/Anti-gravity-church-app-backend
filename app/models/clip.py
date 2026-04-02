"""Clips (short video) models — cross-church video platform."""

import enum
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Text,
    ForeignKey, JSON, UniqueConstraint
)
from sqlalchemy.orm import relationship
from app.database import Base


class ClipCategory(str, enum.Enum):
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


class Clip(Base):
    __tablename__ = "clips"

    id = Column(Integer, primary_key=True, index=True)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    church_id = Column(Integer, ForeignKey("churches.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    video_url = Column(String(500), nullable=False)
    thumbnail_url = Column(String(500), nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    category = Column(String(30), default=ClipCategory.OTHER.value, nullable=False)
    moderation_status = Column(String(20), default=ModerationStatus.APPROVED.value, nullable=False)
    view_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
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
    likes = relationship("ClipLike", back_populates="clip", cascade="all, delete-orphan")
    comments = relationship("ClipComment", back_populates="clip",
                             lazy="dynamic", cascade="all, delete-orphan")
    views = relationship("ClipView", back_populates="clip", cascade="all, delete-orphan")


class ClipLike(Base):
    __tablename__ = "clip_likes"
    __table_args__ = (
        UniqueConstraint("clip_id", "user_id", name="uq_clip_like"),
    )

    id = Column(Integer, primary_key=True, index=True)
    clip_id = Column(Integer, ForeignKey("clips.id", ondelete="CASCADE"),
                     nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    clip = relationship("Clip", back_populates="likes")
    user = relationship("User")


class ClipComment(Base):
    __tablename__ = "clip_comments"

    id = Column(Integer, primary_key=True, index=True)
    clip_id = Column(Integer, ForeignKey("clips.id", ondelete="CASCADE"),
                     nullable=False, index=True)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    parent_id = Column(Integer, ForeignKey("clip_comments.id"), nullable=True)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    clip = relationship("Clip", back_populates="comments")
    author = relationship("User")
    replies = relationship("ClipComment", backref="parent", remote_side=[id])


class ClipView(Base):
    __tablename__ = "clip_views"

    id = Column(Integer, primary_key=True, index=True)
    clip_id = Column(Integer, ForeignKey("clips.id", ondelete="CASCADE"),
                     nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    watched_seconds = Column(Integer, default=0)
    completed = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    clip = relationship("Clip", back_populates="views")
