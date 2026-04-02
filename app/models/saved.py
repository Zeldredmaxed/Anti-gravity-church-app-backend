"""Saved Items model — allows users to bookmark posts, clips, sermons, etc."""

import enum
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
)
from sqlalchemy.orm import relationship
from app.database import Base


class SavedContentType(str, enum.Enum):
    POST = "post"
    CLIP = "clip"
    SERMON = "sermon"
    PRAYER = "prayer"
    EVENT = "event"
    SONG = "song"


class SavedItem(Base):
    __tablename__ = "saved_items"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    content_type = Column(String(30), nullable=False, index=True)  # post, clip, sermon, prayer, event, song
    content_id = Column(String(255), nullable=False, index=True)

    title = Column(String(500), nullable=True)
    thumbnail_url = Column(String(500), nullable=True)
    subtitle = Column(String(500), nullable=True)  # e.g. author name, date

    saved_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("user_id", "content_type", "content_id", name="uq_saved_item"),
    )

    user = relationship("User", foreign_keys=[user_id])
