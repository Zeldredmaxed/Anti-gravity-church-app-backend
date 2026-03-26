"""Church (tenant) model — the multi-tenancy anchor."""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON
from sqlalchemy.orm import relationship
from app.database import Base


class Church(Base):
    __tablename__ = "churches"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    subdomain = Column(String(100), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    logo_url = Column(String(500), nullable=True)
    address = Column(String(500), nullable=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    website = Column(String(255), nullable=True)
    pastor_name = Column(String(255), nullable=True)
    youtube_channel_id = Column(String(50), nullable=True)
    settings = Column(JSON, default=dict)  # Church-specific config
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    users = relationship("User", back_populates="church", lazy="dynamic")
    members = relationship("Member", back_populates="church", lazy="dynamic")


class RegistrationKey(Base):
    __tablename__ = "registration_keys"

    id = Column(Integer, primary_key=True, index=True)
    key_string = Column(String(50), unique=True, index=True, nullable=False)
    is_used = Column(Boolean, default=False, nullable=False)
    church_id = Column(Integer, nullable=True)  # Set when used
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    used_at = Column(DateTime, nullable=True)

