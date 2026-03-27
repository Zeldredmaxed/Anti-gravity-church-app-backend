"""Pydantic schemas for the music platform."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal


# ── Artist ──────────────────────────────────────────────────────────
class ArtistRegister(BaseModel):
    artist_name: str = Field(..., min_length=1, max_length=255)
    bio: Optional[str] = None
    payout_email: Optional[str] = None

class ArtistProfileResponse(BaseModel):
    id: int
    user_id: int
    artist_name: str
    bio: Optional[str] = None
    cover_image_url: Optional[str] = None
    payout_email: Optional[str] = None
    total_earnings: float = 0
    is_verified: bool = False
    song_count: int = 0
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ── Song ────────────────────────────────────────────────────────────
class SongCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    genre: Optional[str] = "gospel"
    audio_url: str
    cover_url: str  # Required — must upload cover art
    duration_seconds: Optional[int] = None

class SongResponse(BaseModel):
    id: int
    artist_id: int
    artist_name: str = ""
    title: str
    genre: Optional[str] = "gospel"
    audio_url: str
    cover_url: Optional[str] = None
    duration_seconds: Optional[int] = None
    play_count: int = 0
    donation_count: int = 0
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ── Donation ────────────────────────────────────────────────────────
class MusicDonationCreate(BaseModel):
    song_id: int
    amount: Decimal = Field(..., ge=Decimal("2.99"))

class MusicDonationResponse(BaseModel):
    id: int
    song_id: Optional[int] = None
    song_title: str = ""
    artist_name: str = ""
    amount: float
    platform_fee: float
    artist_share: float
    download_email_sent: bool = False
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ── Skip Premium ────────────────────────────────────────────────────
class SkipPremiumStatus(BaseModel):
    is_active: bool = False
    expires_at: Optional[datetime] = None
    amount: float = 3.99
