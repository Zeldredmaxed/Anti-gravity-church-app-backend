"""Events & RSVP router."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timezone

from app.database import get_db
from app.models.event import Event, EventRSVP
from app.models.user import User
from app.models.alert import create_alert
from app.schemas.event import (
    EventCreate, EventUpdate, EventResponse,
    RSVPCreate, RSVPResponse,
)
from app.utils.security import get_current_user, require_role

router = APIRouter(prefix="/events", tags=["Events & RSVP"])


@router.get("", response_model=list[EventResponse])
async def list_events(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    include_past: bool = Query(False),
    event_type: str = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)):
    """Get upcoming events for my church."""
    query = select(Event).where(
        Event.church_id == current_user.church_id,
        Event.is_published == True,
        Event.is_cancelled == False)
    if not include_past:
        query = query.where(Event.start_datetime >= datetime.now(timezone.utc))
    if event_type:
        query = query.where(Event.event_type == event_type)
    query = query.order_by(Event.start_datetime).offset(offset).limit(limit)

    events = (await db.execute(query)).scalars().all()
    items = []
    for e in events:
        my_rsvp = (await db.execute(select(EventRSVP).where(
            EventRSVP.event_id == e.id, EventRSVP.user_id == current_user.id
        ))).scalar_one_or_none()
        items.append(EventResponse(
            id=e.id, church_id=e.church_id, title=e.title,
            description=e.description, event_type=e.event_type,
            location=e.location, start_datetime=e.start_datetime,
            end_datetime=e.end_datetime, is_recurring=e.is_recurring,
            recurrence_rule=e.recurrence_rule, max_capacity=e.max_capacity,
            rsvp_count=e.rsvp_count, registration_required=e.registration_required,
            cover_image_url=e.cover_image_url, is_published=e.is_published,
            is_cancelled=e.is_cancelled, created_by=e.created_by,
            created_at=e.created_at,
            my_rsvp=my_rsvp.status if my_rsvp else None))
    return items


@router.post("", response_model=EventResponse, status_code=201)
async def create_event(
    data: EventCreate,
    current_user: User = Depends(require_role("admin", "pastor", "staff")),
    db: AsyncSession = Depends(get_db)):
    event = Event(
        church_id=current_user.church_id,
        created_by=current_user.id,
        **data.model_dump(),
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return EventResponse(
        id=event.id, church_id=event.church_id, title=event.title,
        description=event.description, event_type=event.event_type,
        location=event.location, start_datetime=event.start_datetime,
        end_datetime=event.end_datetime, is_recurring=event.is_recurring,
        recurrence_rule=event.recurrence_rule, max_capacity=event.max_capacity,
        rsvp_count=0, registration_required=event.registration_required,
        cover_image_url=event.cover_image_url, is_published=event.is_published,
        is_cancelled=event.is_cancelled, created_by=event.created_by,
        created_at=event.created_at)


@router.get("/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)):
    e = (await db.execute(select(Event).where(
        Event.id == event_id, Event.church_id == current_user.church_id
    ))).scalar_one_or_none()
    if not e:
        raise HTTPException(status_code=404, detail="Event not found")
    my_rsvp = (await db.execute(select(EventRSVP).where(
        EventRSVP.event_id == e.id, EventRSVP.user_id == current_user.id
    ))).scalar_one_or_none()
    return EventResponse(
        id=e.id, church_id=e.church_id, title=e.title,
        description=e.description, event_type=e.event_type,
        location=e.location, start_datetime=e.start_datetime,
        end_datetime=e.end_datetime, is_recurring=e.is_recurring,
        recurrence_rule=e.recurrence_rule, max_capacity=e.max_capacity,
        rsvp_count=e.rsvp_count, registration_required=e.registration_required,
        cover_image_url=e.cover_image_url, is_published=e.is_published,
        is_cancelled=e.is_cancelled, created_by=e.created_by,
        created_at=e.created_at,
        my_rsvp=my_rsvp.status if my_rsvp else None)


@router.put("/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: int, data: EventUpdate,
    current_user: User = Depends(require_role("admin", "pastor", "staff")),
    db: AsyncSession = Depends(get_db)):
    e = (await db.execute(select(Event).where(
        Event.id == event_id, Event.church_id == current_user.church_id
    ))).scalar_one_or_none()
    if not e:
        raise HTTPException(status_code=404, detail="Event not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(e, field, value)
    db.add(e)
    await db.commit()
    await db.refresh(e)
    return EventResponse(
        id=e.id, church_id=e.church_id, title=e.title,
        description=e.description, event_type=e.event_type,
        location=e.location, start_datetime=e.start_datetime,
        end_datetime=e.end_datetime, is_recurring=e.is_recurring,
        recurrence_rule=e.recurrence_rule, max_capacity=e.max_capacity,
        rsvp_count=e.rsvp_count, registration_required=e.registration_required,
        cover_image_url=e.cover_image_url, is_published=e.is_published,
        is_cancelled=e.is_cancelled, created_by=e.created_by,
        created_at=e.created_at)


@router.delete("/{event_id}", status_code=204)
async def cancel_event(
    event_id: int,
    current_user: User = Depends(require_role("admin", "pastor")),
    db: AsyncSession = Depends(get_db)):
    e = (await db.execute(select(Event).where(
        Event.id == event_id, Event.church_id == current_user.church_id
    ))).scalar_one_or_none()
    if not e:
        raise HTTPException(status_code=404, detail="Event not found")
    e.is_cancelled = True
    db.add(e)

    # Notify RSVPs
    rsvps = (await db.execute(select(EventRSVP).where(
        EventRSVP.event_id == event_id, EventRSVP.status == "going"
    ))).scalars().all()
    for r in rsvps:
        await create_alert(db, r.user_id, "event",
            f"Event cancelled: {e.title}",
            data={"link_type": "event", "link_id": event_id},
            church_id=e.church_id)


# --- RSVP ---

@router.post("/{event_id}/rsvp", response_model=RSVPResponse, status_code=201)
async def rsvp_event(
    event_id: int, data: RSVPCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)):
    e = (await db.execute(select(Event).where(
        Event.id == event_id, Event.church_id == current_user.church_id
    ))).scalar_one_or_none()
    if not e:
        raise HTTPException(status_code=404, detail="Event not found")
    if e.is_cancelled:
        raise HTTPException(status_code=400, detail="Event is cancelled")
    if e.max_capacity and e.rsvp_count >= e.max_capacity and data.status == "going":
        raise HTTPException(status_code=400, detail="Event is at capacity")

    existing = (await db.execute(select(EventRSVP).where(
        EventRSVP.event_id == event_id, EventRSVP.user_id == current_user.id
    ))).scalar_one_or_none()

    if existing:
        old_status = existing.status
        existing.status = data.status
        existing.guests_count = data.guests_count
        existing.notes = data.notes
        db.add(existing)
        # Adjust count
        if old_status == "going" and data.status != "going":
            e.rsvp_count = max((e.rsvp_count or 0) - 1, 0)
        elif old_status != "going" and data.status == "going":
            e.rsvp_count = (e.rsvp_count or 0) + 1
        db.add(e)
        await db.commit()
        await db.refresh(existing)
        rsvp = existing
    else:
        rsvp = EventRSVP(
            event_id=event_id, user_id=current_user.id,
            status=data.status, guests_count=data.guests_count,
            notes=data.notes)
        db.add(rsvp)
        if data.status == "going":
            e.rsvp_count = (e.rsvp_count or 0) + 1
            db.add(e)

        # Notify event creator
        if e.created_by != current_user.id:
            await create_alert(db, e.created_by, "rsvp",
                f"{current_user.full_name} is {data.status} to {e.title}",
                data={"link_type": "event", "link_id": event_id},
                church_id=e.church_id)

        await db.commit()
        await db.refresh(rsvp)

    return RSVPResponse(
        id=rsvp.id, event_id=rsvp.event_id, user_id=rsvp.user_id,
        user_name=current_user.full_name, status=rsvp.status,
        guests_count=rsvp.guests_count, notes=rsvp.notes,
        created_at=rsvp.created_at)


@router.get("/{event_id}/attendees", response_model=list[RSVPResponse])
async def get_attendees(
    event_id: int,
    status: str = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)):
    query = select(EventRSVP).where(EventRSVP.event_id == event_id)
    if status:
        query = query.where(EventRSVP.status == status)
    query = query.order_by(EventRSVP.created_at)
    rsvps = (await db.execute(query)).scalars().all()

    items = []
    for r in rsvps:
        user = (await db.execute(select(User).where(User.id == r.user_id))).scalar_one_or_none()
        items.append(RSVPResponse(
            id=r.id, event_id=r.event_id, user_id=r.user_id,
            user_name=user.full_name if user else None, status=r.status,
            guests_count=r.guests_count, notes=r.notes,
            created_at=r.created_at))
    return items


# --- Volunteers ---

from app.models.volunteer import VolunteerSchedule
from app.schemas.volunteer import VolunteerScheduleResponse

@router.get("/{event_id}/volunteers", response_model=list[VolunteerScheduleResponse])
async def get_event_volunteers(
    event_id: int,
    current_user: User = Depends(require_role("admin", "pastor", "staff", "ministry_leader")),
    db: AsyncSession = Depends(get_db)):
    
    # Check event exists
    e = (await db.execute(select(Event).where(
        Event.id == event_id, Event.church_id == current_user.church_id
    ))).scalar_one_or_none()
    
    if not e:
        raise HTTPException(status_code=404, detail="Event not found")
        
    query = select(VolunteerSchedule).where(VolunteerSchedule.event_id == event_id)
    schedules = (await db.execute(query)).scalars().all()
    
    return schedules

