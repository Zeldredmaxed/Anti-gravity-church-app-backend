"""Facility room management and booking with double-booking prevention."""

from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from pydantic import BaseModel, ConfigDict

from app.database import get_db
from app.models.facility import FacilityRoom, RoomBooking, BookingStatus
from app.models.user import User
from app.utils.security import get_current_user

router = APIRouter(prefix="/facilities", tags=["Facilities"])


# ── Schemas ──

class RoomCreate(BaseModel):
    name: str
    capacity: Optional[int] = None
    amenities: Optional[list] = None
    description: Optional[str] = None


class RoomResponse(BaseModel):
    id: int
    name: str
    capacity: Optional[int] = None
    amenities: Optional[list] = None
    description: Optional[str] = None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class BookingCreate(BaseModel):
    event_id: Optional[int] = None
    title: Optional[str] = None
    start_datetime: datetime
    end_datetime: datetime
    notes: Optional[str] = None


class BookingResponse(BaseModel):
    id: int
    room_id: int
    event_id: Optional[int] = None
    booked_by: int
    title: Optional[str] = None
    start_datetime: datetime
    end_datetime: datetime
    status: str
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# ── Room CRUD ──

@router.get("/rooms", response_model=List[RoomResponse])
async def list_rooms(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all facility rooms for the church."""
    result = await db.execute(
        select(FacilityRoom).where(
            FacilityRoom.church_id == current_user.church_id,
            FacilityRoom.is_active == True,
        )
    )
    return result.scalars().all()


@router.post("/rooms", response_model=RoomResponse, status_code=201)
async def create_room(
    data: RoomCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new facility room."""
    room = FacilityRoom(
        church_id=current_user.church_id,
        name=data.name,
        capacity=data.capacity,
        amenities=data.amenities,
        description=data.description,
    )
    db.add(room)
    await db.flush()
    await db.refresh(room)
    return room


@router.put("/rooms/{room_id}", response_model=RoomResponse)
async def update_room(
    room_id: int,
    data: RoomCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a facility room."""
    room = (await db.execute(
        select(FacilityRoom).where(FacilityRoom.id == room_id, FacilityRoom.church_id == current_user.church_id)
    )).scalar_one_or_none()

    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    room.name = data.name
    room.capacity = data.capacity
    room.amenities = data.amenities
    room.description = data.description
    db.add(room)
    await db.flush()
    await db.refresh(room)
    return room


@router.delete("/rooms/{room_id}", status_code=204)
async def delete_room(
    room_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Soft-delete a facility room."""
    room = (await db.execute(
        select(FacilityRoom).where(FacilityRoom.id == room_id, FacilityRoom.church_id == current_user.church_id)
    )).scalar_one_or_none()

    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    room.is_active = False
    db.add(room)
    await db.flush()


# ── Booking ──

@router.post("/rooms/{room_id}/book", response_model=BookingResponse, status_code=201)
async def book_room(
    room_id: int,
    data: BookingCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Book a room with double-booking conflict detection."""
    if data.end_datetime <= data.start_datetime:
        raise HTTPException(status_code=400, detail="End time must be after start time")

    # Check for overlapping bookings
    conflicts = (await db.execute(
        select(RoomBooking).where(
            RoomBooking.room_id == room_id,
            RoomBooking.status != BookingStatus.CANCELLED.value,
            # Overlap: existing.start < new.end AND existing.end > new.start
            RoomBooking.start_datetime < data.end_datetime,
            RoomBooking.end_datetime > data.start_datetime,
        )
    )).scalars().all()

    if conflicts:
        raise HTTPException(
            status_code=409,
            detail=f"Room is already booked during this time ({len(conflicts)} conflicting booking(s))",
        )

    booking = RoomBooking(
        church_id=current_user.church_id,
        room_id=room_id,
        event_id=data.event_id,
        booked_by=current_user.id,
        title=data.title,
        start_datetime=data.start_datetime,
        end_datetime=data.end_datetime,
        notes=data.notes,
    )
    db.add(booking)
    await db.flush()
    await db.refresh(booking)
    return booking


@router.get("/rooms/{room_id}/bookings", response_model=List[BookingResponse])
async def get_room_bookings(
    room_id: int,
    start_date: Optional[str] = Query(None, description="Filter from date (YYYY-MM-DD)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all bookings for a room."""
    query = select(RoomBooking).where(
        RoomBooking.room_id == room_id,
        RoomBooking.church_id == current_user.church_id,
        RoomBooking.status != BookingStatus.CANCELLED.value,
    ).order_by(RoomBooking.start_datetime)

    if start_date:
        from datetime import datetime as dt
        filter_date = dt.fromisoformat(start_date)
        query = query.where(RoomBooking.start_datetime >= filter_date)

    result = await db.execute(query)
    return result.scalars().all()


@router.delete("/bookings/{booking_id}", status_code=204)
async def cancel_booking(
    booking_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Cancel a room booking."""
    booking = (await db.execute(
        select(RoomBooking).where(RoomBooking.id == booking_id, RoomBooking.church_id == current_user.church_id)
    )).scalar_one_or_none()

    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    booking.status = BookingStatus.CANCELLED.value
    db.add(booking)
    await db.flush()
