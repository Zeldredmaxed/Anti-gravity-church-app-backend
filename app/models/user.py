"""User and audit trail models."""

import enum
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Enum, Text, ForeignKey, JSON
)
from sqlalchemy.orm import relationship
from app.database import Base


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    PASTOR = "pastor"
    STAFF = "staff"
    MINISTRY_LEADER = "ministry_leader"
    FINANCE_TEAM = "finance_team"
    VOLUNTEER = "volunteer"
    MEMBER = "member"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    church_id = Column(Integer, ForeignKey("churches.id"), nullable=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    date_of_birth = Column(DateTime(timezone=True), nullable=True)
    stripe_customer_id = Column(String(255), nullable=True)
    testimony_summary = Column(Text, nullable=True)
    is_anointed = Column(Boolean, default=False)
    website = Column(String(255), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    role = Column(String(20), default=UserRole.MEMBER.value, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=True)

    # ── 2FA ──
    totp_secret = Column(String(255), nullable=True)  # Encrypted TOTP secret
    is_2fa_enabled = Column(Boolean, default=False)

    # ── Preferences ──
    language_preference = Column(String(10), default="en")
    notification_prefs = Column(JSON, default=lambda: {"email": True, "sms": False, "push": True})
    phone_number = Column(String(20), nullable=True)  # For SMS delivery

    # ── Tracking ──
    last_login_at = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    church = relationship("Church", back_populates="users")
    audit_logs = relationship("AuditLog", back_populates="user", lazy="dynamic")
    member_notes = relationship("MemberNote", back_populates="author", lazy="dynamic")
    sessions = relationship("UserSession", back_populates="user", lazy="dynamic", cascade="all, delete-orphan")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    church_id = Column(Integer, ForeignKey("churches.id"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(50), nullable=False)
    resource = Column(String(100), nullable=False)
    resource_id = Column(String(50), nullable=True)
    details = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    # Relationships
    user = relationship("User", back_populates="audit_logs")


class UserSession(Base):
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    session_token = Column(String(500), unique=True, index=True, nullable=False)
    device_info = Column(String(255), nullable=True) # e.g. "iPhone 13 - iOS Safari"
    ip_address = Column(String(45), nullable=True)
    location = Column(String(255), nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    last_active_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime(timezone=True), nullable=False)

    user = relationship("User", back_populates="sessions")
