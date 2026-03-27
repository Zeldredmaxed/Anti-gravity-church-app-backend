"""Member profile model with full CRM fields."""

import enum
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Date, Enum, Text,
    ForeignKey, JSON
)
from sqlalchemy.orm import relationship
from app.database import Base


class MembershipStatus(str, enum.Enum):
    VISITOR = "visitor"
    PROSPECT = "prospect"
    MEMBER = "member"
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEACON = "deacon"
    ELDER = "elder"


class BaptismType(str, enum.Enum):
    IMMERSION = "immersion"
    SPRINKLING = "sprinkling"
    POURING = "pouring"


class HealthStatus(str, enum.Enum):
    AT_RISK = "at_risk"
    INCONSISTENT = "inconsistent"
    ENGAGED = "engaged"
    NEW = "new"


class NoteType(str, enum.Enum):
    GENERAL = "general"
    PRAYER_REQUEST = "prayer_request"
    COUNSELING = "counseling"
    PASTORAL_VISIT = "pastoral_visit"
    HOSPITAL_VISIT = "hospital_visit"
    EVANGELISM = "evangelism"


class Member(Base):
    __tablename__ = "members"

    id = Column(Integer, primary_key=True, index=True)
    church_id = Column(Integer, ForeignKey("churches.id"), nullable=False, index=True)
    campus_id = Column(Integer, ForeignKey("campuses.id"), nullable=True, index=True)

    # Personal Info
    first_name = Column(String(100), nullable=False, index=True)
    last_name = Column(String(100), nullable=False, index=True)
    email = Column(String(255), nullable=True, index=True)
    phone = Column(String(20), nullable=True)
    secondary_phone = Column(String(20), nullable=True)

    # Address
    address = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(50), nullable=True)
    zip_code = Column(String(10), nullable=True)

    # Demographics
    date_of_birth = Column(Date, nullable=True)
    gender = Column(String(20), nullable=True)
    marital_status = Column(String(20), nullable=True)
    photo_url = Column(String(500), nullable=True)

    # Church Info
    membership_status = Column(
        String(20), default=MembershipStatus.VISITOR.value, nullable=False
    )
    join_date = Column(Date, nullable=True)

    # Baptism Tracking
    baptism_date = Column(Date, nullable=True)
    baptism_location = Column(String(255), nullable=True)
    baptism_type = Column(String(20), nullable=True)
    baptism_pastor = Column(String(255), nullable=True)

    # Spiritual Milestones
    salvation_status = Column(String(50), nullable=True)
    salvation_date = Column(Date, nullable=True)
    completed_membership_class = Column(Boolean, default=False)
    membership_class_date = Column(Date, nullable=True)
    spiritual_gifts = Column(JSON, nullable=True)
    
    # Health Metrics
    health_score = Column(Integer, nullable=True)  # 0-100 score
    health_status = Column(String(20), nullable=True) # e.g. from HealthStatus enum

    # Background Check
    background_check_status = Column(String(50), nullable=True)
    background_check_date = Column(Date, nullable=True)

    # Custom & Meta
    custom_fields = Column(JSON, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    emergency_contact_name = Column(String(255), nullable=True)
    emergency_contact_phone = Column(String(20), nullable=True)

    # Family
    family_id = Column(Integer, ForeignKey("families.id"), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    is_deleted = Column(Boolean, default=False)

    # Relationships
    church = relationship("Church", back_populates="members")
    family = relationship("Family", back_populates="members")
    notes = relationship("MemberNote", back_populates="member", lazy="dynamic")
    campus = relationship("Campus", back_populates="members")
    donations = relationship("Donation", back_populates="donor", lazy="dynamic")
    attendance_records = relationship("AttendanceRecord", back_populates="member", lazy="dynamic")
    pledges = relationship("Pledge", back_populates="member", lazy="dynamic")
    group_memberships = relationship("GroupMembership", back_populates="member", lazy="dynamic")


class MemberNote(Base):
    __tablename__ = "member_notes"

    id = Column(Integer, primary_key=True, index=True)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False, index=True)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    note_type = Column(String(30), default=NoteType.GENERAL.value, nullable=False)
    content = Column(Text, nullable=False)
    is_confidential = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    member = relationship("Member", back_populates="notes")
    author = relationship("User", back_populates="member_notes")
