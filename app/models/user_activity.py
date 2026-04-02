"""User Activity and Tracking models."""

import enum
from datetime import datetime, timezone, timedelta
from sqlalchemy import (
    Column, Integer, String, DateTime, Text, ForeignKey, JSON, Enum
)
from sqlalchemy.orm import relationship
from app.database import Base


class InteractionType(str, enum.Enum):
    LIKE = "like"
    COMMENT = "comment"
    SHARE = "share"

class ContentType(str, enum.Enum):
    POST = "post"
    CLIP = "clip"
    STORY = "story"


class UserInteraction(Base):
    __tablename__ = "user_interactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("members.id", ondelete="CASCADE"), nullable=False, index=True)
    
    type = Column(Enum(InteractionType), nullable=False, index=True)
    target_type = Column(Enum(ContentType), nullable=False)
    target_id = Column(String(255), nullable=False, index=True)
    
    target_title = Column(String(255), nullable=True)
    target_thumbnail = Column(String(500), nullable=True)
    content = Column(Text, nullable=True)  # For comments or share notes

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("Member", foreign_keys=[user_id])


class UserContentView(Base):
    __tablename__ = "user_content_views"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("members.id", ondelete="CASCADE"), nullable=False, index=True)
    
    content_type = Column(Enum(ContentType), nullable=False)
    content_id = Column(String(255), nullable=False, index=True)
    
    title = Column(String(255), nullable=True)
    thumbnail_url = Column(String(500), nullable=True)
    author_name = Column(String(255), nullable=True)
    
    viewed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    user = relationship("Member", foreign_keys=[user_id])


class RecentlyDeleted(Base):
    __tablename__ = "recently_deleted"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("members.id", ondelete="CASCADE"), nullable=False, index=True)
    
    content_type = Column(Enum(ContentType), nullable=False)
    title = Column(String(255), nullable=True)
    thumbnail_url = Column(String(500), nullable=True)
    original_data = Column(JSON, nullable=False)  # The fully serialized object to restore
    
    deleted_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc) + timedelta(days=30), index=True)

    user = relationship("Member", foreign_keys=[user_id])
