"""Social media interaction models: follows, mentions, saves, and reports."""

from datetime import datetime, timezone
import enum
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base


class ReportStatus(str, enum.Enum):
    PENDING = "pending"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class FlockMember(Base):
    __tablename__ = "flock_members"
    __table_args__ = (
        UniqueConstraint("follower_id", "followed_id", name="uq_user_flock"),
    )

    id = Column(Integer, primary_key=True, index=True)
    follower_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    followed_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class Meditation(Base):
    __tablename__ = "meditations"
    __table_args__ = (
        UniqueConstraint("user_id", "entity_type", "entity_id", name="uq_user_meditations"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False, index=True)  # "post" or "glory_clip"
    entity_id = Column(Integer, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class Mention(Base):
    __tablename__ = "mentions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)  # Who was mentioned
    author_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True) # Who did the mentioning
    entity_type = Column(String(50), nullable=False, index=True)  # "post", "short", "comment"
    entity_id = Column(Integer, nullable=False, index=True)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User", foreign_keys=[user_id])
    author = relationship("User", foreign_keys=[author_id])


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    reporter_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    entity_type = Column(String(50), nullable=False, index=True)  # "post", "short", "user", "comment"
    entity_id = Column(Integer, nullable=False, index=True)
    reason = Column(Text, nullable=False)
    status = Column(String(20), default=ReportStatus.PENDING.value, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    reporter = relationship("User")
