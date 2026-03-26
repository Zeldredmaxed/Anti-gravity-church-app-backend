"""Group and small group models."""

import enum
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Date, Text,
    ForeignKey
)
from sqlalchemy.orm import relationship
from app.database import Base


class GroupType(str, enum.Enum):
    SMALL_GROUP = "small_group"
    SUNDAY_SCHOOL = "sunday_school"
    MINISTRY_TEAM = "ministry_team"
    BIBLE_STUDY = "bible_study"
    PRAYER_GROUP = "prayer_group"
    YOUTH_GROUP = "youth_group"
    MENS_GROUP = "mens_group"
    WOMENS_GROUP = "womens_group"
    OTHER = "other"


class GroupRole(str, enum.Enum):
    LEADER = "leader"
    CO_LEADER = "co_leader"
    MEMBER = "member"


class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, index=True)
    church_id = Column(Integer, ForeignKey("churches.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    group_type = Column(String(30), default=GroupType.SMALL_GROUP.value, nullable=False)
    leader_id = Column(Integer, ForeignKey("members.id"), nullable=True)
    meeting_day = Column(String(15), nullable=True)
    meeting_time = Column(String(10), nullable=True)
    meeting_location = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    max_capacity = Column(Integer, nullable=True)
    campus = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    memberships = relationship("GroupMembership", back_populates="group", lazy="selectin")
    attendance_records = relationship("GroupAttendance", back_populates="group", lazy="dynamic")


class GroupMembership(Base):
    __tablename__ = "group_memberships"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False, index=True)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False, index=True)
    role = Column(String(20), default=GroupRole.MEMBER.value, nullable=False)
    joined_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    group = relationship("Group", back_populates="memberships")
    member = relationship("Member", back_populates="group_memberships")
