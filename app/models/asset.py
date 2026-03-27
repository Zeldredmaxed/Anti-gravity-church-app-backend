"""Inventory management models for church assets."""

from datetime import datetime, timezone, date
from sqlalchemy import (
    Column, Integer, String, DateTime, Date, Numeric, Text, ForeignKey,
)
from sqlalchemy.orm import relationship
from app.database import Base


class Asset(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, index=True)
    church_id = Column(Integer, ForeignKey("churches.id"), nullable=False, index=True)
    
    name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=True) # e.g. "Cameras", "Instruments", "Vehicles"
    serial_number = Column(String(255), nullable=True, unique=True)
    
    # Financial details
    purchase_date = Column(Date, nullable=True)
    purchase_price = Column(Numeric(10, 2), nullable=True)
    
    # Status
    status = Column(String(50), default="available") # available, in_repair, checked_out, retired
    
    # Check-out management
    assigned_to_id = Column(Integer, ForeignKey("users.id"), nullable=True) # The staff/volunteer who holds it
    
    # Audit trail
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    notes = Column(Text, nullable=True)
    
    # Relationships
    church = relationship("Church")
    assigned_to = relationship("User")
