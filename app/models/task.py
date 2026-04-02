"""Ministry Task tracking model with care case linkage."""

import enum
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, DateTime, Text, ForeignKey,
)
from sqlalchemy.orm import relationship
from app.database import Base


class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELED = "canceled"


class TaskType(str, enum.Enum):
    FOLLOW_UP = "follow_up"
    PASTORAL_CARE = "pastoral_care"
    ADMIN = "admin"
    DISCIPLESHIP = "discipleship"
    OTHER = "other"


class ActionType(str, enum.Enum):
    SEND_SMS = "send_sms"
    SEND_EMAIL = "send_email"
    LOG_CALL = "log_call"
    HOME_VISIT = "home_visit"
    OTHER = "other"


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    church_id = Column(Integer, ForeignKey("churches.id"), nullable=False, index=True)
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    assigned_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    related_member_id = Column(Integer, ForeignKey("members.id", ondelete="SET NULL"), nullable=True, index=True)

    # ── Care Case Linkage (NEW) ──
    care_case_id = Column(Integer, ForeignKey("care_cases.id", ondelete="SET NULL"), nullable=True, index=True)

    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    task_type = Column(String(50), default=TaskType.FOLLOW_UP.value, nullable=False)
    status = Column(String(50), default=TaskStatus.PENDING.value, nullable=False)

    # ── Action Type (NEW) — what kind of action this task represents ──
    action_type = Column(String(50), default=ActionType.OTHER.value, nullable=True)

    due_date = Column(DateTime(timezone=True), nullable=True, index=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    church = relationship("Church")
    assignee = relationship("User", foreign_keys=[assigned_to])
    creator = relationship("User", foreign_keys=[assigned_by])
    member = relationship("Member")
    care_case = relationship("CareCase")
