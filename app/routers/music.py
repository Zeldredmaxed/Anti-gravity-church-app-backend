"""Gospel Music Platform router — radio player, artist uploads, donations, skip premium."""

import random
from datetime import datetime, timezone, timedelta
from decimal import Decimal, ROUND_HALF_UP

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.database import get_db
from app.models.user import User
from app.models.music import Song, ArtistProfile, MusicDonation, SkipSubscription
from app.schemas.music import (
    SongCreate, SongResponse,
    ArtistRegister, ArtistProfileResponse,
    MusicDonationCreate, MusicDonationResponse,
    SkipPremiumStatus,
)
from app.utils.security import get_current_user
from app.services.email_service import send_song_download_email

router = APIRouter(prefix="/music", tags=["Gospel Music"])

PLATFORM_FEE_RATE = Decimal("0.30")
ARTIST_SHARE_RATE = Decimal("0.70")
SKIP_MONTHLY_PRICE = Decimal("3.99")
ALLOWED_DONATION_AMOUNTS = [Decimal("2.99"), Decimal("5.00"), Decimal("25.00")]


# ── Helpers ─────────────────────────────────────────────────────────

def _song_resp(song: Song, artist_name: str = "") -> dict:
    return {
        "id": song.id,
        "artist_id": song.artist_id,
        "artist_name": artist_name,
        "title": song.title,
        "genre": song.genre,
        "audio_url": song.audio_url,
        "cover_url": song.cover_url,
        "duration_seconds": song.duration_seconds,
        "play_count": song.play_count,
        "donation_count": song.donation_count,
        "created_at": song.created_at,
    }


async def _get_artist_name(db: AsyncSession, artist_id: int) -> str:
    artist = (await db.execute(
        select(ArtistProfile).where(ArtistProfile.id == artist_id)
    )).scalar_one_or_none()
    return artist.artist_name if artist else "Unknown Artist"


# ── Radio Queue ─────────────────────────────────────────────────────

@router.get("/radio")
async def get_radio_queue(
    limit: int = Query(20, ge=1, le=50),
    _=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return a shuffled queue of approved songs for radio playback."""
    result = await db.execute(
        select(Song).where(Song.is_approved == True, Song.is_active == True)
    )
    songs = list(result.scalars().all())
    random.shuffle(songs)
    queue = songs[:limit]

    data = []
    for s in queue:
        name = await _get_artist_name(db, s.artist_id)
        data.append(_song_resp(s, name))

    return {"data": data}


# ── Song CRUD ───────────────────────────────────────────────────────

@router.get("/songs")
async def list_songs(
    genre: str | None = None,
    q: str | None = None,
    limit: int = Query(20, ge=1, le=50),
    offset: int = 0,
    _=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Browse or search songs."""
    query = select(Song).where(Song.is_approved == True, Song.is_active == True)
    if genre:
        query = query.where(Song.genre == genre)
    if q:
        query = query.where(Song.title.ilike(f"%{q}%"))
    query = query.order_by(desc(Song.created_at)).offset(offset).limit(limit)

    songs = (await db.execute(query)).scalars().all()
    data = []
    for s in songs:
        name = await _get_artist_name(db, s.artist_id)
        data.append(_song_resp(s, name))

    return {"data": data}


@router.get("/songs/{song_id}")
async def get_song(
    song_id: int,
    _=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    song = (await db.execute(select(Song).where(Song.id == song_id))).scalar_one_or_none()
    if not song:
        raise HTTPException(status_code=404, detail="Song not found")
    name = await _get_artist_name(db, song.artist_id)
    return {"data": _song_resp(song, name)}


@router.post("/songs", status_code=201)
async def upload_song(
    data: SongCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Artist uploads a new song. Must be a registered artist."""
    artist = (await db.execute(
        select(ArtistProfile).where(ArtistProfile.user_id == current_user.id)
    )).scalar_one_or_none()
    if not artist:
        raise HTTPException(status_code=403, detail="You must register as an artist first")

    song = Song(
        artist_id=artist.id,
        title=data.title,
        genre=data.genre,
        audio_url=data.audio_url,
        cover_url=data.cover_url,
        duration_seconds=data.duration_seconds,
    )
    db.add(song)
    await db.flush()
    await db.refresh(song)
    return {"data": _song_resp(song, artist.artist_name)}


@router.post("/songs/{song_id}/play")
async def record_play(
    song_id: int,
    _=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Increment play count when a song finishes playing."""
    song = (await db.execute(select(Song).where(Song.id == song_id))).scalar_one_or_none()
    if not song:
        raise HTTPException(status_code=404, detail="Song not found")
    song.play_count = (song.play_count or 0) + 1
    db.add(song)
    return {"data": {"play_count": song.play_count}}


# ── Artist Profiles ─────────────────────────────────────────────────

@router.post("/artist/register", status_code=201)
async def register_artist(
    data: ArtistRegister,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    existing = (await db.execute(
        select(ArtistProfile).where(ArtistProfile.user_id == current_user.id)
    )).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="You are already registered as an artist")

    artist = ArtistProfile(
        user_id=current_user.id,
        artist_name=data.artist_name,
        bio=data.bio,
        payout_email=data.payout_email or current_user.email,
    )
    db.add(artist)
    await db.flush()
    await db.refresh(artist)
    return {"data": {
        "id": artist.id,
        "user_id": artist.user_id,
        "artist_name": artist.artist_name,
        "bio": artist.bio,
        "payout_email": artist.payout_email,
        "total_earnings": 0,
        "is_verified": artist.is_verified,
        "song_count": 0,
        "created_at": artist.created_at,
    }}


@router.get("/artist/me")
async def get_my_artist_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the current user's artist profile."""
    artist = (await db.execute(
        select(ArtistProfile).where(ArtistProfile.user_id == current_user.id)
    )).scalar_one_or_none()
    if not artist:
        return {"data": None}

    song_count = (await db.execute(
        select(func.count()).select_from(Song).where(Song.artist_id == artist.id)
    )).scalar() or 0

    return {"data": {
        "id": artist.id,
        "user_id": artist.user_id,
        "artist_name": artist.artist_name,
        "bio": artist.bio,
        "cover_image_url": artist.cover_image_url,
        "payout_email": artist.payout_email,
        "total_earnings": float(artist.total_earnings or 0),
        "is_verified": artist.is_verified,
        "song_count": song_count,
        "created_at": artist.created_at,
    }}


@router.get("/artist/{artist_id}")
async def get_artist(
    artist_id: int,
    _=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    artist = (await db.execute(
        select(ArtistProfile).where(ArtistProfile.id == artist_id)
    )).scalar_one_or_none()
    if not artist:
        raise HTTPException(status_code=404, detail="Artist not found")

    songs = (await db.execute(
        select(Song).where(Song.artist_id == artist.id, Song.is_active == True)
        .order_by(desc(Song.created_at))
    )).scalars().all()

    song_count = len(songs)

    return {"data": {
        "id": artist.id,
        "user_id": artist.user_id,
        "artist_name": artist.artist_name,
        "bio": artist.bio,
        "cover_image_url": artist.cover_image_url,
        "total_earnings": float(artist.total_earnings or 0),
        "is_verified": artist.is_verified,
        "song_count": song_count,
        "created_at": artist.created_at,
        "songs": [_song_resp(s, artist.artist_name) for s in songs],
    }}


# ── Donations (70/30 Split) ────────────────────────────────────────

@router.post("/donate", status_code=201)
async def donate_to_artist(
    data: MusicDonationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Donate to an artist for a song. Platform takes 30%, artist gets 70%.
    Sends the song download link via email to the donor.
    """
    amount = data.amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if amount not in ALLOWED_DONATION_AMOUNTS:
        raise HTTPException(
            status_code=400,
            detail=f"Donation must be one of: ${', $'.join(str(a) for a in ALLOWED_DONATION_AMOUNTS)}"
        )

    song = (await db.execute(select(Song).where(Song.id == data.song_id))).scalar_one_or_none()
    if not song:
        raise HTTPException(status_code=404, detail="Song not found")

    artist = (await db.execute(
        select(ArtistProfile).where(ArtistProfile.id == song.artist_id)
    )).scalar_one_or_none()
    if not artist:
        raise HTTPException(status_code=404, detail="Artist not found")

    platform_fee = (amount * PLATFORM_FEE_RATE).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    artist_share = amount - platform_fee

    donation = MusicDonation(
        donor_id=current_user.id,
        song_id=song.id,
        artist_id=artist.id,
        amount=amount,
        platform_fee=platform_fee,
        artist_share=artist_share,
        donor_email=current_user.email,
    )
    db.add(donation)

    # Update artist earnings
    artist.total_earnings = (artist.total_earnings or Decimal("0")) + artist_share
    db.add(artist)

    # Update song donation count
    song.donation_count = (song.donation_count or 0) + 1
    db.add(song)

    await db.flush()
    await db.refresh(donation)

    # Send download email (non-blocking — if SMTP isn't configured it just skips)
    email_sent = send_song_download_email(
        to_email=current_user.email,
        song_title=song.title,
        artist_name=artist.artist_name,
        download_url=song.audio_url,
        amount=float(amount),
    )
    if email_sent:
        donation.download_email_sent = True
        db.add(donation)

    return {"data": {
        "id": donation.id,
        "song_id": song.id,
        "song_title": song.title,
        "artist_name": artist.artist_name,
        "amount": float(amount),
        "platform_fee": float(platform_fee),
        "artist_share": float(artist_share),
        "download_email_sent": donation.download_email_sent,
        "created_at": donation.created_at,
    }}


@router.get("/donations/me")
async def my_donations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List the current user's donation / purchase history."""
    result = await db.execute(
        select(MusicDonation).where(MusicDonation.donor_id == current_user.id)
        .order_by(desc(MusicDonation.created_at))
    )
    donations = result.scalars().all()

    data = []
    for d in donations:
        song = (await db.execute(select(Song).where(Song.id == d.song_id))).scalar_one_or_none()
        artist = (await db.execute(
            select(ArtistProfile).where(ArtistProfile.id == d.artist_id)
        )).scalar_one_or_none()
        data.append({
            "id": d.id,
            "song_id": d.song_id,
            "song_title": song.title if song else "Unknown",
            "artist_name": artist.artist_name if artist else "Unknown",
            "audio_url": song.audio_url if song else None,
            "amount": float(d.amount),
            "platform_fee": float(d.platform_fee),
            "artist_share": float(d.artist_share),
            "download_email_sent": d.download_email_sent,
            "created_at": d.created_at,
        })

    return {"data": data}


# ── Skip Premium ($3.99/mo) ─────────────────────────────────────────

@router.get("/skip-premium/status")
async def skip_premium_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Check if the user has an active skip premium subscription."""
    now = datetime.now(timezone.utc)
    sub = (await db.execute(
        select(SkipSubscription).where(
            SkipSubscription.user_id == current_user.id,
            SkipSubscription.status == "active",
            SkipSubscription.expires_at > now,
        )
    )).scalar_one_or_none()

    return {"data": {
        "is_active": sub is not None,
        "expires_at": sub.expires_at.isoformat() if sub else None,
        "amount": float(SKIP_MONTHLY_PRICE),
    }}


@router.post("/skip-premium", status_code=201)
async def subscribe_skip_premium(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Subscribe to skip premium ($3.99/mo).
    In production, this would create a Stripe subscription.
    For now, records the subscription directly.
    """
    now = datetime.now(timezone.utc)

    # Check if already active
    existing = (await db.execute(
        select(SkipSubscription).where(
            SkipSubscription.user_id == current_user.id,
            SkipSubscription.status == "active",
            SkipSubscription.expires_at > now,
        )
    )).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="You already have an active skip premium subscription")

    sub = SkipSubscription(
        user_id=current_user.id,
        status="active",
        amount=SKIP_MONTHLY_PRICE,
        started_at=now,
        expires_at=now + timedelta(days=30),
    )
    db.add(sub)
    await db.flush()
    await db.refresh(sub)

    return {"data": {
        "is_active": True,
        "expires_at": sub.expires_at.isoformat(),
        "amount": float(SKIP_MONTHLY_PRICE),
        "message": "Skip Premium activated! You can now skip songs for 30 days.",
    }}
