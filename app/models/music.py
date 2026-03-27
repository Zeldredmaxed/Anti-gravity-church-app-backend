"""Music platform models: Song, ArtistProfile, MusicDonation, SkipSubscription."""

from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Text, ForeignKey,
    Numeric, Index
)
from sqlalchemy.orm import relationship
from app.database import Base


class ArtistProfile(Base):
    """Extended profile for users who register as artists."""
    __tablename__ = "artist_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    artist_name = Column(String(255), nullable=False)
    bio = Column(Text, nullable=True)
    cover_image_url = Column(String(500), nullable=True)
    payout_email = Column(String(255), nullable=True)
    total_earnings = Column(Numeric(12, 2), default=Decimal("0.00"))
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User", backref="artist_profile")
    songs = relationship("Song", back_populates="artist", lazy="dynamic")


class Song(Base):
    """A song uploaded by an artist."""
    __tablename__ = "songs"

    id = Column(Integer, primary_key=True, index=True)
    artist_id = Column(Integer, ForeignKey("artist_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    genre = Column(String(100), nullable=True, default="gospel")
    audio_url = Column(String(500), nullable=False)
    cover_url = Column(String(500), nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    play_count = Column(Integer, default=0)
    donation_count = Column(Integer, default=0)
    is_approved = Column(Boolean, default=True)  # Auto-approve for now
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    artist = relationship("ArtistProfile", back_populates="songs")


class MusicDonation(Base):
    """Records a listener donation to an artist for a specific song."""
    __tablename__ = "music_donations"

    id = Column(Integer, primary_key=True, index=True)
    donor_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    song_id = Column(Integer, ForeignKey("songs.id", ondelete="SET NULL"), nullable=True, index=True)
    artist_id = Column(Integer, ForeignKey("artist_profiles.id", ondelete="SET NULL"), nullable=True, index=True)
    amount = Column(Numeric(10, 2), nullable=False)
    platform_fee = Column(Numeric(10, 2), nullable=False)   # 30%
    artist_share = Column(Numeric(10, 2), nullable=False)    # 70%
    donor_email = Column(String(255), nullable=True)
    download_email_sent = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class SkipSubscription(Base):
    """$3.99/mo skip premium subscription."""
    __tablename__ = "skip_subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(20), default="active")  # active, cancelled, expired
    amount = Column(Numeric(10, 2), default=Decimal("3.99"))
    started_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
