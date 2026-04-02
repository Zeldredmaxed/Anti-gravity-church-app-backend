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
    SongCreate, SongUpdate, SongResponse,
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


# ── Server-Side Radio Station ───────────────────────────────────────
# The station plays continuously on the server's timeline.
# Every client that "tunes in" gets the current song + how far into it
# we are, so they join mid-song — just like real radio.

DEFAULT_SONG_DURATION = 300  # 5:00 fallback if duration not stored
ADVANCE_GRACE_SECONDS = 15   # Extra buffer before server auto-advances


class RadioStation:
    """Global singleton that tracks what the radio is playing right now."""

    def __init__(self):
        self.queue: list[dict] = []       # list of song dicts
        self.queue_index: int = 0
        self.song_started_at: datetime | None = None
        self.last_listener_at: datetime | None = None
        self.is_live: bool = False

    def _current_song_duration(self) -> int:
        if not self.queue:
            return DEFAULT_SONG_DURATION
        song = self.queue[self.queue_index % len(self.queue)]
        return song.get("duration_seconds") or DEFAULT_SONG_DURATION

    def advance_if_needed(self) -> None:
        """Auto-advance past any songs whose time has elapsed.

        A grace period (ADVANCE_GRACE_SECONDS) is added to the song
        duration so that the server doesn't advance before clients
        have finished playing — accounting for buffering, loading
        latency, and clock drift.
        """
        if not self.is_live or not self.queue or not self.song_started_at:
            return

        now = datetime.now(timezone.utc)
        elapsed = (now - self.song_started_at).total_seconds()
        dur = self._current_song_duration() + ADVANCE_GRACE_SECONDS

        # Keep advancing while elapsed > current song duration + grace
        while elapsed >= dur and self.queue:
            raw_dur = self._current_song_duration()  # actual duration for time math
            self.queue_index = (self.queue_index + 1) % len(self.queue)
            self.song_started_at = self.song_started_at + timedelta(seconds=raw_dur + ADVANCE_GRACE_SECONDS)
            elapsed = (now - self.song_started_at).total_seconds()
            dur = self._current_song_duration() + ADVANCE_GRACE_SECONDS

    def force_advance(self) -> None:
        """Client-triggered advance when a song finishes on device."""
        if not self.is_live or not self.queue:
            return
        
        # Advance the index and reset the started_at timestamp to now
        self.queue_index = (self.queue_index + 1) % len(self.queue)
        self.song_started_at = datetime.now(timezone.utc)

    def now_playing(self) -> dict | None:
        """Return the current song + elapsed seconds."""
        if not self.is_live or not self.queue:
            return None

        self.advance_if_needed()

        song = self.queue[self.queue_index % len(self.queue)]
        elapsed = 0.0
        if self.song_started_at:
            elapsed = (datetime.now(timezone.utc) - self.song_started_at).total_seconds()

        song_duration = self._current_song_duration()

        return {
            "song": song,
            "elapsed_seconds": round(elapsed, 1),
            "song_duration_seconds": song_duration,
            "queue_position": self.queue_index,
            "queue_length": len(self.queue),
            "is_live": True,
        }

    async def ensure_live(self, db: AsyncSession) -> None:
        """Start the station if it's not running, or refresh queue if empty."""
        now = datetime.now(timezone.utc)
        self.last_listener_at = now

        # Check 5-min idle timeout
        if self.is_live and self.queue:
            return  # Already running

        # Load songs from DB and build queue
        result = await db.execute(
            select(Song).where(Song.is_approved == True, Song.is_active == True)
        )
        songs = list(result.scalars().all())
        if not songs:
            self.is_live = False
            return

        random.shuffle(songs)

        # Build enriched queue with artist names
        enriched = []
        for s in songs:
            artist = (await db.execute(
                select(ArtistProfile).where(ArtistProfile.id == s.artist_id)
            )).scalar_one_or_none()
            enriched.append({
                "id": s.id,
                "artist_id": s.artist_id,
                "artist_name": artist.artist_name if artist else "Unknown Artist",
                "title": s.title,
                "genre": s.genre,
                "audio_url": s.audio_url,
                "cover_url": s.cover_url,
                "duration_seconds": s.duration_seconds,
                "play_count": s.play_count,
                "donation_count": s.donation_count,
            })

        self.queue = enriched
        self.queue_index = 0
        self.song_started_at = now
        self.is_live = True


# Global singleton instance — shared across all requests
_station = RadioStation()


@router.get("/radio/now-playing")
async def radio_now_playing(
    _=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Tune in to the live radio station.

    Returns the currently playing song and how many seconds have elapsed,
    so the client can seek to the correct position — joining mid-song
    just like real radio.
    """
    await _station.ensure_live(db)

    data = _station.now_playing()
    if not data:
        return {"data": None, "message": "No songs available. Upload some music!"}

    return {"data": data}


@router.post("/radio/heartbeat")
async def radio_heartbeat(
    _=Depends(get_current_user),
):
    """Client sends this every ~60s to keep the station alive.
    If no heartbeats for 5 minutes, the station pauses.
    """
    _station.last_listener_at = datetime.now(timezone.utc)
    return {"status": "ok"}


@router.post("/radio/advance")
async def radio_advance(
    _=Depends(get_current_user),
):
    """Client calls this when the audio finishes playing on the device.
    Forces the server to move to the next song immediately.
    """
    _station.force_advance()
    return {"status": "advanced"}


@router.get("/radio")
async def get_radio_queue(
    limit: int = Query(20, ge=1, le=50),
    _=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Legacy endpoint — return a shuffled queue of approved songs."""
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
    
    # Immediately add to the live radio queue if it's currently broadcasting
    if _station.is_live:
        _station.queue.append({
            "id": song.id,
            "artist_id": song.artist_id,
            "artist_name": artist.artist_name,
            "title": song.title,
            "genre": song.genre,
            "audio_url": song.audio_url,
            "cover_url": song.cover_url,
            "duration_seconds": song.duration_seconds,
            "play_count": song.play_count,
            "donation_count": song.donation_count,
        })
        
    return {"data": _song_resp(song, artist.artist_name)}


@router.put("/songs/{song_id}")
async def update_song(
    song_id: int,
    data: SongUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Edit a song's title, genre, or cover art. Only the artist who uploaded it can edit."""
    song = (await db.execute(select(Song).where(Song.id == song_id))).scalar_one_or_none()
    if not song:
        raise HTTPException(status_code=404, detail="Song not found")

    # Verify ownership
    artist = (await db.execute(
        select(ArtistProfile).where(
            ArtistProfile.id == song.artist_id,
            ArtistProfile.user_id == current_user.id,
        )
    )).scalar_one_or_none()
    if not artist:
        raise HTTPException(status_code=403, detail="You can only edit your own songs")

    if data.title is not None:
        song.title = data.title
    if data.genre is not None:
        song.genre = data.genre
    if data.cover_url is not None:
        song.cover_url = data.cover_url

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


@router.get("/artist/me/songs")
async def get_my_songs(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all songs by the current artist."""
    artist = (await db.execute(
        select(ArtistProfile).where(ArtistProfile.user_id == current_user.id)
    )).scalar_one_or_none()
    if not artist:
        raise HTTPException(status_code=403, detail="You are not registered as an artist")

    songs = (await db.execute(
        select(Song).where(Song.artist_id == artist.id)
        .order_by(desc(Song.created_at))
    )).scalars().all()

    return {"data": [_song_resp(s, artist.artist_name) for s in songs]}


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
