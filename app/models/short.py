"""Shorts system models — cross-church video platform."""

import enum
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Text,
    ForeignKey, JSON, UniqueConstraint
)
from sqlalchemy.orm import relationship
from app.database import Base


class ShortCategory(str, enum.Enum):
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


class Short(Base):
    __tablename__ = "shorts"

    id = Column(Integer, primary_key=True, index=True)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    church_id = Column(Integer, ForeignKey("churches.id"), nullable=False, index=True)  # Attribution, not isolation
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    video_url = Column(String(500), nullable=False)
    thumbnail_url = Column(String(500), nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    category = Column(String(30), default=ShortCategory.OTHER.value, nullable=False)
    moderation_status = Column(String(20), default=ModerationStatus.APPROVED.value, nullable=False)
    view_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    share_count = Column(Integer, default=0)
    is_featured = Column(Boolean, default=False)
    tags = Column(JSON, default=list)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    author = relationship("User")
    church = relationship("Church")
    likes = relationship("ShortLike", back_populates="short", cascade="all, delete-orphan")
    comments = relationship("ShortComment", back_populates="short",
                             lazy="dynamic", cascade="all, delete-orphan")
    views = relationship("ShortView", back_populates="short", cascade="all, delete-orphan")


class ShortLike(Base):
    __tablename__ = "short_likes"
    __table_args__ = (
        UniqueConstraint("short_id", "user_id", name="uq_short_like"),
    )

    id = Column(Integer, primary_key=True, index=True)
    short_id = Column(Integer, ForeignKey("shorts.id", ondelete="CASCADE"),
                       nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    short = relationship("Short", back_populates="likes")
    user = relationship("User")


class ShortComment(Base):
    __tablename__ = "short_comments"

    id = Column(Integer, primary_key=True, index=True)
    short_id = Column(Integer, ForeignKey("shorts.id", ondelete="CASCADE"),
                       nullable=False, index=True)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    parent_id = Column(Integer, ForeignKey("short_comments.id"), nullable=True)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    short = relationship("Short", back_populates="comments")
    author = relationship("User")
    replies = relationship("ShortComment", backref="parent", remote_side=[id])


class ShortView(Base):
    __tablename__ = "short_views"

    id = Column(Integer, primary_key=True, index=True)
    short_id = Column(Integer, ForeignKey("shorts.id", ondelete="CASCADE"),
                       nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    watched_seconds = Column(Integer, default=0)
    completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    short = relationship("Short", back_populates="views")
