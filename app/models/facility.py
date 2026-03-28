"""Facility room and booking models for preventing double-booking."""

import enum
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, ForeignKey, JSON, Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from app.database import Base


class BookingStatus(str, enum.Enum):
    CONFIRMED = "confirmed"
    TENTATIVE = "tentative"
    CANCELLED = "cancelled"


class FacilityRoom(Base):
    """Church rooms/spaces available for booking."""
    __tablename__ = "facility_rooms"

    id = Column(Integer, primary_key=True, index=True)
    church_id = Column(Integer, ForeignKey("churches.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)              # "Sanctuary", "Youth Room", "Fellowship Hall"
    capacity = Column(Integer, nullable=True)
    amenities = Column(JSON, nullable=True)                  # ["projector", "piano", "whiteboard"]
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    church = relationship("Church")
    bookings = relationship("RoomBooking", back_populates="room", lazy="dynamic")


class RoomBooking(Base):
    """Room reservation linked to events — prevents double-booking."""
    __tablename__ = "room_bookings"

    id = Column(Integer, primary_key=True, index=True)
    church_id = Column(Integer, ForeignKey("churches.id"), nullable=False, index=True)
    room_id = Column(Integer, ForeignKey("facility_rooms.id", ondelete="CASCADE"), nullable=False, index=True)
    event_id = Column(Integer, ForeignKey("events.id", ondelete="SET NULL"), nullable=True, index=True)
    booked_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    title = Column(String(255), nullable=True)  # Booking title (if not linked to event)
    start_datetime = Column(DateTime(timezone=True), nullable=False, index=True)
    end_datetime = Column(DateTime(timezone=True), nullable=False)

    status = Column(String(20), default=BookingStatus.CONFIRMED.value, nullable=False)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    church = relationship("Church")
    room = relationship("FacilityRoom", back_populates="bookings")
    event = relationship("Event")
    booker = relationship("User")
