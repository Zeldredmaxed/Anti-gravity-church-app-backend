"""Family/household models with relationship tracking."""

import enum
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey
)
from sqlalchemy.orm import relationship
from app.database import Base


class RelationshipType(str, enum.Enum):
    HEAD = "head"
    SPOUSE = "spouse"
    CHILD = "child"
    PARENT = "parent"
    SIBLING = "sibling"
    OTHER = "other"


class Family(Base):
    __tablename__ = "families"

    id = Column(Integer, primary_key=True, index=True)
    church_id = Column(Integer, ForeignKey("churches.id"), nullable=False, index=True)
    family_name = Column(String(255), nullable=False, index=True)
    address = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(50), nullable=True)
    zip_code = Column(String(10), nullable=True)
    phone = Column(String(20), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    members = relationship("Member", back_populates="family", lazy="selectin")
    relationships = relationship("FamilyRelationship", back_populates="family", lazy="selectin")


class FamilyRelationship(Base):
    __tablename__ = "family_relationships"

    id = Column(Integer, primary_key=True, index=True)
    family_id = Column(Integer, ForeignKey("families.id"), nullable=False, index=True)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False, index=True)
    relationship_type = Column(
        String(20), default=RelationshipType.OTHER.value, nullable=False
    )

    # Relationships
    family = relationship("Family", back_populates="relationships")
    member = relationship("Member")
