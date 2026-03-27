"""System automation triggers and follow-up engines."""

from datetime import datetime, timezone
import enum
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, JSON, ForeignKey,
)
from sqlalchemy.orm import relationship
from app.database import Base


class TriggerType(str, enum.Enum):
    FIRST_TIME_VISITOR = "first_time_visitor"
    MISSED_3_SUNDAYS = "missed_3_sundays"
    MISSED_1_SUNDAY = "missed_1_sunday"
    NEW_DONOR = "new_donor"
    BIRTHDAY = "birthday"
    JOINED_GROUP = "joined_group"
    SALVATION = "salvation"
    BAPTISM_SCHEDULED = "baptism_scheduled"


class ActionType(str, enum.Enum):
    SEND_EMAIL = "send_email"
    SEND_SMS = "send_sms"
    SEND_PUSH = "send_push"
    ADD_TASK = "add_task"
    ALERT_LEADER = "alert_leader"
    ADD_TO_GROUP = "add_to_group"


class AutomationRule(Base):
    """Configures 'If This Then That' rules for church administration."""
    __tablename__ = "automation_rules"

    id = Column(Integer, primary_key=True, index=True)
    church_id = Column(Integer, ForeignKey("churches.id"), nullable=False, index=True)
    
    name = Column(String(255), nullable=False)
    description = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)
    
    # If This...
    trigger_type = Column(String(100), nullable=False) # e.g. "missed_3_sundays"
    trigger_config = Column(JSON, nullable=True) # Further refinements to trigger
    
    # Then That...
    action_type = Column(String(100), nullable=False) # e.g. "send_sms", "alert_leader"
    action_payload = Column(JSON, nullable=True) # Template for message or task details
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    church = relationship("Church")
