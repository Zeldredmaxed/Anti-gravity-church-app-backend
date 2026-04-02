"""Login streak tracking models."""

from datetime import datetime, timezone, date
from sqlalchemy import (
    Column, Integer, Date, DateTime, ForeignKey, UniqueConstraint
)
from app.database import Base


class LoginDay(Base):
    """Records each unique day a user logs in."""
    __tablename__ = "login_days"
    __table_args__ = (
        UniqueConstraint("user_id", "login_date", name="uq_login_day"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    login_date = Column(Date, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class LoginStreak(Base):
    """Aggregated streak stats per user — updated on each login."""
    __tablename__ = "login_streaks"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_login_streak"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    current_streak = Column(Integer, default=1)
    longest_streak = Column(Integer, default=1)
    total_logins = Column(Integer, default=1)
    last_login_date = Column(Date, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))
