"""Donation and pledge tracking models."""

import enum
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Date, Numeric, Text,
    ForeignKey
)
from sqlalchemy.orm import relationship
from app.database import Base


class DonationType(str, enum.Enum):
    TITHE = "tithe"
    OFFERING = "offering"
    SPECIAL_GIFT = "special_gift"
    BENEVOLENCE = "benevolence"
    MISSIONS = "missions"
    BUILDING = "building"
    OTHER = "other"


class PaymentMethod(str, enum.Enum):
    CASH = "cash"
    CHECK = "check"
    ONLINE = "online"
    TEXT = "text"
    BANK_TRANSFER = "bank_transfer"
    DEBIT_CARD = "debit_card"
    CREDIT_CARD = "credit_card"
    OTHER = "other"


class PledgeStatus(str, enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Donation(Base):
    __tablename__ = "donations"

    id = Column(Integer, primary_key=True, index=True)
    church_id = Column(Integer, ForeignKey("churches.id"), nullable=False, index=True)
    donor_id = Column(Integer, ForeignKey("members.id"), nullable=True, index=True)
    fund_id = Column(Integer, ForeignKey("funds.id"), nullable=False, index=True)
    amount = Column(Numeric(12, 2), nullable=False)
    donation_type = Column(String(30), default=DonationType.OFFERING.value, nullable=False)
    payment_method = Column(String(30), default=PaymentMethod.CASH.value, nullable=False)
    check_number = Column(String(50), nullable=True)
    transaction_id = Column(String(255), nullable=True)
    date = Column(Date, nullable=False, index=True)
    is_recurring = Column(Boolean, default=False)
    recurring_frequency = Column(String(20), nullable=True)
    is_anonymous = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)
    recorded_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    donor = relationship("Member", back_populates="donations")
    fund = relationship("Fund", back_populates="donations")


class Pledge(Base):
    __tablename__ = "pledges"

    id = Column(Integer, primary_key=True, index=True)
    church_id = Column(Integer, ForeignKey("churches.id"), nullable=False, index=True)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False, index=True)
    fund_id = Column(Integer, ForeignKey("funds.id"), nullable=False, index=True)
    campaign_name = Column(String(255), nullable=True)
    pledged_amount = Column(Numeric(12, 2), nullable=False)
    fulfilled_amount = Column(Numeric(12, 2), default=0)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    status = Column(String(20), default=PledgeStatus.ACTIVE.value, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    member = relationship("Member", back_populates="pledges")
    fund = relationship("Fund", back_populates="pledges")
