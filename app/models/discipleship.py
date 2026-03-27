"""Discipleship tracking models."""

import enum
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Text, ForeignKey, UniqueConstraint
)
from sqlalchemy.orm import relationship
from app.database import Base


class ProgressStatus(str, enum.Enum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DROPPED = "dropped"


class DiscipleshipStep(Base):
    __tablename__ = "discipleship_steps"

    id = Column(Integer, primary_key=True, index=True)
    church_id = Column(Integer, ForeignKey("churches.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    order_index = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    progress_records = relationship("MemberDiscipleshipProgress", back_populates="step", cascade="all, delete-orphan")


class MemberDiscipleshipProgress(Base):
    __tablename__ = "member_discipleship_progress"
    __table_args__ = (
        UniqueConstraint("member_id", "step_id", name="uq_member_step"),
    )

    id = Column(Integer, primary_key=True, index=True)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False, index=True)
    step_id = Column(Integer, ForeignKey("discipleship_steps.id"), nullable=False, index=True)
    status = Column(String(30), default=ProgressStatus.PLANNED.value, nullable=False)
    notes = Column(Text, nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    member = relationship("Member")
    step = relationship("DiscipleshipStep", back_populates="progress_records")
