"""Prayer request router — prayer wall, pray counter, respond."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models.prayer import PrayerRequest, PrayerResponseEntry
from app.models.user import User
from app.models.alert import create_alert
from app.schemas.prayer import (
    PrayerRequestCreate, PrayerRequestUpdate, PrayerRequestResponse,
    PrayerResponseCreate, PrayerResponseSchema, PrayerAnsweredRequest,
)
from app.utils.security import get_current_user, require_role

router = APIRouter(prefix="/prayers", tags=["Prayer Requests"])


def _prayer_response(p, author_name=None, responses=None, is_prayed_by_me=False, author_avatar=None):
    return PrayerRequestResponse(
        id=p.id, church_id=p.church_id,
        author_id=None if p.is_anonymous else p.author_id,
        author_name=None if p.is_anonymous else author_name,
        author_avatar=None if p.is_anonymous else author_avatar,
        title=p.title, description=p.description, category=p.category,
        is_anonymous=p.is_anonymous, is_urgent=p.is_urgent,
        is_answered=p.is_answered, answered_testimony=p.answered_testimony,
        prayed_count=p.prayed_count, visibility=p.visibility,
        is_prayed_by_me=is_prayed_by_me,
        created_at=p.created_at, responses=responses or [])


@router.get("", response_model=list[PrayerRequestResponse])
async def prayer_wall(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    category: str = Query(None),
    include_answered: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)):
    """Get prayer wall for my church."""
    query = select(PrayerRequest).where(
        PrayerRequest.church_id == current_user.church_id,
        PrayerRequest.is_deleted == False)

    if not include_answered:
        query = query.where(PrayerRequest.is_answered == False)
    if category:
        query = query.where(PrayerRequest.category == category)

    # Visibility filter
    if current_user.role not in ("admin", "pastor"):
        query = query.where(PrayerRequest.visibility.in_(["public", "church_only"]))

    # Urgent first, then by date
    query = query.order_by(PrayerRequest.is_urgent.desc(), PrayerRequest.created_at.desc())
    query = query.offset(offset).limit(limit)

    prayers = (await db.execute(query)).scalars().all()
    
    prayer_ids = [p.id for p in prayers]
    my_prayers = set()
    if prayer_ids:
        prayed_rows = (await db.execute(
            select(PrayerResponseEntry.prayer_request_id).where(
                PrayerResponseEntry.prayer_request_id.in_(prayer_ids),
                PrayerResponseEntry.responder_id == current_user.id,
                PrayerResponseEntry.is_prayed == True
            )
        )).scalars().all()
        my_prayers = set(prayed_rows)
        
    items = []
    for p in prayers:
        author = (await db.execute(select(User).where(User.id == p.author_id))).scalar_one_or_none()
        items.append(_prayer_response(
            p, 
            author.full_name if author else None, 
            is_prayed_by_me=(p.id in my_prayers), 
            author_avatar=getattr(author, "avatar_url", None) if author else None
        ))
    return items


@router.post("", response_model=PrayerRequestResponse, status_code=201)
async def submit_prayer(
    data: PrayerRequestCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)):
    prayer = PrayerRequest(
        church_id=current_user.church_id,
        author_id=current_user.id,
        **data.model_dump(),
    )
    db.add(prayer)
    await db.flush()
    await db.refresh(prayer)
    return _prayer_response(prayer,
        None if data.is_anonymous else current_user.full_name,
        is_prayed_by_me=False,
        author_avatar=None if data.is_anonymous else getattr(current_user, "avatar_url", None))


@router.get("/{prayer_id}", response_model=PrayerRequestResponse)
async def get_prayer(
    prayer_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)):
    p = (await db.execute(select(PrayerRequest).where(
        PrayerRequest.id == prayer_id,
        PrayerRequest.church_id == current_user.church_id,
        PrayerRequest.is_deleted == False
    ))).scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Prayer request not found")

    author = (await db.execute(select(User).where(User.id == p.author_id))).scalar_one_or_none()

    # Get responses
    resp_rows = (await db.execute(
        select(PrayerResponseEntry).where(PrayerResponseEntry.prayer_request_id == prayer_id)
        .order_by(PrayerResponseEntry.created_at)
    )).scalars().all()
    responses = []
    for r in resp_rows:
        responder = (await db.execute(select(User).where(User.id == r.responder_id))).scalar_one_or_none()
        responses.append(PrayerResponseSchema(
            id=r.id, author_id=r.responder_id,
            author_name=responder.full_name if responder else None,
            author_avatar=getattr(responder, "avatar_url", None) if responder else None,
            content=r.content, is_prayed=r.is_prayed,
            created_at=r.created_at))

    is_prayed = (await db.execute(select(PrayerResponseEntry).where(
        PrayerResponseEntry.prayer_request_id == prayer_id,
        PrayerResponseEntry.responder_id == current_user.id,
        PrayerResponseEntry.is_prayed == True
    ))).scalar_one_or_none() is not None

    return _prayer_response(
        p, 
        author.full_name if author else None, 
        responses, 
        is_prayed_by_me=is_prayed,
        author_avatar=getattr(author, "avatar_url", None) if author else None
    )


@router.post("/{prayer_id}/pray")
async def toggle_pray(
    prayer_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)):
    """Toggle 'I prayed for this' — pray if not already, unpray if already prayed."""
    p = (await db.execute(select(PrayerRequest).where(
        PrayerRequest.id == prayer_id, PrayerRequest.is_deleted == False
    ))).scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Prayer request not found")

    # Check if already prayed (just the boolean flag, no content)
    existing = (await db.execute(select(PrayerResponseEntry).where(
        PrayerResponseEntry.prayer_request_id == prayer_id,
        PrayerResponseEntry.responder_id == current_user.id,
        PrayerResponseEntry.content.is_(None),
    ))).scalar_one_or_none()

    if existing:
        # Unpray — remove record, decrement count
        await db.delete(existing)
        p.prayed_count = max((p.prayed_count or 1) - 1, 0)
        db.add(p)
        await db.flush()
        return {"data": {"has_prayed": False, "pray_count": p.prayed_count}}
    else:
        # Pray — create record, increment count
        resp = PrayerResponseEntry(
            prayer_request_id=prayer_id, responder_id=current_user.id,
            is_prayed=True)
        db.add(resp)
        p.prayed_count = (p.prayed_count or 0) + 1
        db.add(p)

        # Notify author
        if p.author_id != current_user.id:
            await create_alert(db, p.author_id, "prayer",
                f"{current_user.full_name} prayed for your request",
                data={"link_type": "prayer", "link_id": prayer_id},
                church_id=p.church_id)

        await db.flush()
        return {"data": {"has_prayed": True, "pray_count": p.prayed_count}}


@router.post("/{prayer_id}/respond", response_model=PrayerResponseSchema, status_code=201)
async def respond_to_prayer(
    prayer_id: int, data: PrayerResponseCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)):
    """Add an encouragement message to a prayer request."""
    p = (await db.execute(select(PrayerRequest).where(
        PrayerRequest.id == prayer_id, PrayerRequest.is_deleted == False
    ))).scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Prayer request not found")

    resp = PrayerResponseEntry(
        prayer_request_id=prayer_id, responder_id=current_user.id,
        content=data.content, is_prayed=data.is_prayed)
    db.add(resp)
    if data.is_prayed:
        p.prayed_count = (p.prayed_count or 0) + 1
        db.add(p)

    if p.author_id != current_user.id:
        await create_alert(db, p.author_id, "prayer",
            f"{current_user.full_name} responded to your prayer request",
            body=data.content[:100] if data.content else None,
            data={"link_type": "prayer", "link_id": prayer_id},
            church_id=p.church_id)

    await db.flush()
    await db.refresh(resp)
    return PrayerResponseSchema(
        id=resp.id, author_id=resp.responder_id,
        author_name=current_user.full_name,
        author_avatar=getattr(current_user, "avatar_url", None),
        content=resp.content, is_prayed=resp.is_prayed,
        created_at=resp.created_at)


@router.put("/{prayer_id}/answered")
async def mark_answered(
    prayer_id: int, data: PrayerAnsweredRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)):
    """Mark as answered (author only)."""
    p = (await db.execute(select(PrayerRequest).where(
        PrayerRequest.id == prayer_id
    ))).scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Prayer request not found")
    if p.author_id != current_user.id and current_user.role not in ("admin", "pastor"):
        raise HTTPException(status_code=403, detail="Only the author can mark as answered")
    p.is_answered = True
    p.answered_testimony = data.testimony
    db.add(p)
    return {"message": "Marked as answered", "testimony": data.testimony}


@router.delete("/{prayer_id}", status_code=204)
async def delete_prayer(
    prayer_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)):
    p = (await db.execute(select(PrayerRequest).where(
        PrayerRequest.id == prayer_id, PrayerRequest.church_id == current_user.church_id
    ))).scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Prayer request not found")
    if p.author_id != current_user.id and current_user.role not in ("admin", "pastor"):
        raise HTTPException(status_code=403, detail="Cannot delete this prayer request")
    p.is_deleted = True
    db.add(p)
