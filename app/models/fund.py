"""Fund accounting, budget, and expense models."""

import enum
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Date, Numeric, Text,
    ForeignKey
)
from sqlalchemy.orm import relationship
from app.database import Base


class FundType(str, enum.Enum):
    GENERAL = "general"
    MISSIONS = "missions"
    BUILDING = "building"
    YOUTH = "youth"
    BENEVOLENCE = "benevolence"
    MEDIA = "media"
    EDUCATION = "education"
    OTHER = "other"


class Fund(Base):
    __tablename__ = "funds"

    id = Column(Integer, primary_key=True, index=True)
    church_id = Column(Integer, ForeignKey("churches.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    fund_type = Column(String(30), default=FundType.GENERAL.value, nullable=False)
    is_restricted = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    target_amount = Column(Numeric(12, 2), nullable=True)
    current_balance = Column(Numeric(12, 2), default=0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    donations = relationship("Donation", back_populates="fund", lazy="dynamic")
    budgets = relationship("Budget", back_populates="fund", lazy="selectin")
    expenses = relationship("Expense", back_populates="fund", lazy="dynamic")
    pledges = relationship("Pledge", back_populates="fund", lazy="dynamic")


class Budget(Base):
    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True, index=True)
    church_id = Column(Integer, ForeignKey("churches.id"), nullable=False, index=True)
    fund_id = Column(Integer, ForeignKey("funds.id"), nullable=False, index=True)
    fiscal_year = Column(Integer, nullable=False)
    budgeted_amount = Column(Numeric(12, 2), nullable=False)
    period = Column(String(20), default="annual")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    fund = relationship("Fund", back_populates="budgets")


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    church_id = Column(Integer, ForeignKey("churches.id"), nullable=False, index=True)
    fund_id = Column(Integer, ForeignKey("funds.id"), nullable=False, index=True)
    amount = Column(Numeric(12, 2), nullable=False)
    description = Column(String(500), nullable=False)
    vendor = Column(String(255), nullable=True)
    category = Column(String(100), nullable=True)
    date = Column(Date, nullable=False)
    check_number = Column(String(50), nullable=True)
    receipt_url = Column(String(500), nullable=True)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    fund = relationship("Fund", back_populates="expenses")
