"""Feed system models: posts, likes, comments."""

import enum
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Text,
    ForeignKey, JSON, UniqueConstraint
)
from sqlalchemy.orm import relationship
from app.database import Base


class PostType(str, enum.Enum):
    TEXT = "text"
    PHOTO = "photo"
    VIDEO = "video"
    ANNOUNCEMENT = "announcement"
    TESTIMONY = "testimony"
    PRAYER_REQUEST = "prayer_request"


class PostVisibility(str, enum.Enum):
    PUBLIC = "public"
    MEMBERS_ONLY = "members_only"
    LEADERS_ONLY = "leaders_only"


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    church_id = Column(Integer, ForeignKey("churches.id"), nullable=False, index=True)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    content = Column(Text, nullable=True)
    media_urls = Column(JSON, default=list)  # Array of media URLs
    post_type = Column(String(30), default=PostType.TEXT.value, nullable=False)
    visibility = Column(String(20), default=PostVisibility.MEMBERS_ONLY.value, nullable=False)
    likes_count = Column(Integer, default=0)
    comments_count = Column(Integer, default=0)
    shares_count = Column(Integer, default=0)
    is_pinned = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    author = relationship("User")
    likes = relationship("PostLike", back_populates="post", cascade="all, delete-orphan")
    comments = relationship("PostComment", back_populates="post",
                             lazy="dynamic", cascade="all, delete-orphan")


class PostLike(Base):
    __tablename__ = "post_likes"
    __table_args__ = (
        UniqueConstraint("post_id", "user_id", name="uq_post_like"),
    )

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id", ondelete="CASCADE"),
                      nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    post = relationship("Post", back_populates="likes")
    user = relationship("User")


class PostComment(Base):
    __tablename__ = "post_comments"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id", ondelete="CASCADE"),
                      nullable=False, index=True)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    parent_id = Column(Integer, ForeignKey("post_comments.id"), nullable=True)  # Nested replies
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    post = relationship("Post", back_populates="comments")
    author = relationship("User")
    replies = relationship("PostComment", backref="parent", remote_side=[id])
