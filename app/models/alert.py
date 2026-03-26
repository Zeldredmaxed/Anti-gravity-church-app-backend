"""Notification model and helper utility."""

import enum
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Text,
    ForeignKey, JSON
)
from sqlalchemy.orm import relationship
from app.database import Base


class AlertType(str, enum.Enum):
    MESSAGE = "message"
    AMEN = "amen"
    COMMENT = "comment"
    EVENT = "event"
    PRAYER = "prayer"
    ANNOUNCEMENT = "announcement"
    RSVP = "rsvp"
    SYSTEM = "system"


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    church_id = Column(Integer, ForeignKey("churches.id"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    type = Column(String(30), nullable=False)
    title = Column(String(255), nullable=False)
    body = Column(Text, nullable=True)
    data = Column(JSON, default=dict)  # {link_type: "post", link_id: 42} for deep linking
    is_read = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    # Relationships
    user = relationship("User")


async def create_alert(
    db,
    user_id: int,
    type: str,
    title: str,
    body: str = None,
    data: dict = None,
    church_id: int = None,
):
    """Utility to create an alert from any router."""
    alert = Alert(
        church_id=church_id,
        user_id=user_id,
        type=type,
        title=title,
        body=body,
        data=data or {},
    )
    db.add(alert)
    return alert
