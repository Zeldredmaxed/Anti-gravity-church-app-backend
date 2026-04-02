"""Geo-based check-in model."""

from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, Float, Date, DateTime, ForeignKey, UniqueConstraint
)
from app.database import Base


class CheckIn(Base):
    """Records a geo-verified church attendance."""
    __tablename__ = "checkins"
    __table_args__ = (
        UniqueConstraint("user_id", "check_in_date", name="uq_checkin"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    church_id = Column(Integer, ForeignKey("churches.id"), nullable=False, index=True)
    check_in_date = Column(Date, nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    distance_miles = Column(Float, nullable=False)
    year = Column(Integer, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
