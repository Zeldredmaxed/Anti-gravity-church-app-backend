"""Clips router — cross-church video platform with trending."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case
from datetime import datetime, timezone, timedelta

from app.database import get_db
from app.models.clip import Clip, ClipLike, ClipComment, ClipView
from app.models.user import User
from app.models.church import Church
from app.models.alert import create_alert
from app.schemas.clip import (
    ClipCreate, ClipUpdate, ClipResponse,
    ClipCommentCreate, ClipCommentResponse, ClipViewRecord,
)
from app.utils.security import get_current_user
from app.utils.mentions import process_mentions

router = APIRouter(prefix="/clips", tags=["Clips (Cross-Church)"])


def _clip_response(s, author_name=None, church_name=None, is_amened=False):
    return ClipResponse(
        id=s.id, author_id=s.author_id, author_name=author_name,
        church_id=s.church_id, church_name=church_name,
        title=s.title, description=s.description, video_url=s.video_url,
        thumbnail_url=s.thumbnail_url, duration_seconds=s.duration_seconds,
        category=s.category, moderation_status=s.moderation_status,
        view_count=s.view_count, like_count=s.like_count,
        comment_count=s.comment_count, share_count=s.share_count,
        is_featured=s.is_featured, tags=s.tags or [],
        is_liked_by_me=is_amened, created_at=s.created_at)


@router.get("", response_model=list[ClipResponse])
async def get_clips_feed(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    category: str = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)):
    """Get clips feed — cross-church, all approved clips."""
    query = select(Clip).where(
        Clip.is_deleted == False,
        Clip.moderation_status == "approved")
    if category:
        query = query.where(Clip.category == category)
    query = query.order_by(Clip.is_featured.desc(), Clip.created_at.desc())
    query = query.offset(offset).limit(limit)

    clips = (await db.execute(query)).scalars().all()
    return [await _enrich(db, s, current_user) for s in clips]


@router.get("/trending", response_model=list[ClipResponse])
async def get_trending(
    limit: int = Query(20, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)):
    """Trending clips based on weighted engagement in the last 7 days.
    Score = (views * 1) + (likes * 3) + (comments * 5) + (completion_rate * 10)
    """
    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)

    # Get recent clips with their engagement
    query = select(Clip).where(
        Clip.is_deleted == False,
        Clip.moderation_status == "approved",
        Clip.created_at >= seven_days_ago,
    )
    clips = (await db.execute(query)).scalars().all()

    # Calculate trending score
    scored = []
    for s in clips:
        # Completion rate from views
        completion_count = (await db.execute(
            select(func.count()).where(
                ClipView.clip_id == s.id, ClipView.completed == True)
        )).scalar() or 0
        total_views = max(s.view_count, 1)
        completion_rate = completion_count / total_views

        score = (
            (s.view_count or 0) * 1
            + (s.like_count or 0) * 3
            + (s.comment_count or 0) * 5
            + completion_rate * 10
        )
        scored.append((s, score))

    scored.sort(key=lambda x: x[1], reverse=True)
    top = [s for s, _ in scored[:limit]]
    return [await _enrich(db, s, current_user) for s in top]


@router.get("/my-church", response_model=list[ClipResponse])
async def get_my_church_clips(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)):
    """Get clips from my church only."""
    query = select(Clip).where(
        Clip.church_id == current_user.church_id,
        Clip.is_deleted == False,
        Clip.moderation_status == "approved")
    query = query.order_by(Clip.created_at.desc()).offset(offset).limit(limit)
    clips = (await db.execute(query)).scalars().all()
    return [await _enrich(db, s, current_user) for s in clips]


@router.post("", response_model=ClipResponse, status_code=201)
async def create_clip(
    data: ClipCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)):
    """Upload a new clip."""
    clip = Clip(
        author_id=current_user.id,
        church_id=current_user.church_id,
        title=data.title,
        description=data.description,
        video_url=data.video_url,
        thumbnail_url=data.thumbnail_url,
        duration_seconds=data.duration_seconds,
        category=data.category,
        tags=data.tags or [],
    )
    db.add(clip)
    await db.flush()
    await db.refresh(clip)
    await process_mentions(db, clip.description, current_user.id, "clip", clip.id)
    await db.commit()
    return _clip_response(clip, current_user.full_name)


@router.get("/{clip_id}", response_model=ClipResponse)
async def get_clip(
    clip_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)):
    s = (await db.execute(select(Clip).where(
        Clip.id == clip_id, Clip.is_deleted == False))).scalar_one_or_none()
    if not s:
        raise HTTPException(status_code=404, detail="Clip not found")
    return await _enrich(db, s, current_user)


@router.post("/{clip_id}/amen", status_code=201)
async def amen_clip(
    clip_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)):
    s = (await db.execute(select(Clip).where(Clip.id == clip_id))).scalar_one_or_none()
    if not s:
        raise HTTPException(status_code=404, detail="Clip not found")
    existing = (await db.execute(select(ClipLike).where(
        ClipLike.clip_id == clip_id, ClipLike.user_id == current_user.id
    ))).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Already amened")
    db.add(ClipLike(clip_id=clip_id, user_id=current_user.id))
    s.like_count = (s.like_count or 0) + 1
    db.add(s)

    # Notify author
    if s.author_id != current_user.id:
        await create_alert(db, s.author_id, "like",
            f"{current_user.full_name} amened your glory clip",
            data={"link_type": "clip", "link_id": clip_id})

    await db.flush()
    return {"message": "Amened", "like_count": s.like_count}


@router.delete("/{clip_id}/amen", status_code=200)
async def unamen_clip(
    clip_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)):
    existing = (await db.execute(select(ClipLike).where(
        ClipLike.clip_id == clip_id, ClipLike.user_id == current_user.id
    ))).scalar_one_or_none()
    if not existing:
        raise HTTPException(status_code=400, detail="Not amened")
    await db.delete(existing)
    s = (await db.execute(select(Clip).where(Clip.id == clip_id))).scalar_one_or_none()
    if s:
        s.like_count = max((s.like_count or 0) - 1, 0)
        db.add(s)
    return {"message": "Unamened", "like_count": s.like_count if s else 0}


@router.post("/{clip_id}/comments", response_model=ClipCommentResponse, status_code=201)
async def add_comment(
    clip_id: int, data: ClipCommentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)):
    s = (await db.execute(select(Clip).where(Clip.id == clip_id))).scalar_one_or_none()
    if not s:
        raise HTTPException(status_code=404, detail="Clip not found")
    comment = ClipComment(
        clip_id=clip_id, author_id=current_user.id,
        content=data.content, parent_id=data.parent_id)
    db.add(comment)
    s.comment_count = (s.comment_count or 0) + 1
    db.add(s)

    if s.author_id != current_user.id:
        await create_alert(db, s.author_id, "comment",
            f"{current_user.full_name} commented on your glory clip",
            body=data.content[:100],
            data={"link_type": "clip", "link_id": clip_id})

    await db.flush()
    await db.refresh(comment)
    
    await process_mentions(db, comment.content, current_user.id, "clip_comment", comment.id)
    
    return ClipCommentResponse(
        id=comment.id, clip_id=comment.clip_id, author_id=comment.author_id,
        author_name=current_user.full_name, content=comment.content,
        parent_id=comment.parent_id, created_at=comment.created_at)


@router.get("/{clip_id}/comments", response_model=list[ClipCommentResponse])
async def get_comments(
    clip_id: int,
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)):
    comments = (await db.execute(
        select(ClipComment).where(
            ClipComment.clip_id == clip_id,
            ClipComment.parent_id.is_(None),
            ClipComment.is_deleted == False)
        .order_by(ClipComment.created_at.desc()).limit(limit)
    )).scalars().all()

    items = []
    for c in comments:
        author = (await db.execute(select(User).where(User.id == c.author_id))).scalar_one_or_none()
        replies_rows = (await db.execute(
            select(ClipComment).where(ClipComment.parent_id == c.id, ClipComment.is_deleted == False)
            .order_by(ClipComment.created_at)
        )).scalars().all()
        replies = []
        for r in replies_rows:
            ra = (await db.execute(select(User).where(User.id == r.author_id))).scalar_one_or_none()
            replies.append(ClipCommentResponse(
                id=r.id, clip_id=r.clip_id, author_id=r.author_id,
                author_name=ra.full_name if ra else None, content=r.content,
                parent_id=r.parent_id, created_at=r.created_at))
        items.append(ClipCommentResponse(
            id=c.id, clip_id=c.clip_id, author_id=c.author_id,
            author_name=author.full_name if author else None, content=c.content,
            parent_id=c.parent_id, created_at=c.created_at, replies=replies))
    return items


@router.post("/{clip_id}/view")
async def record_view(
    clip_id: int, data: ClipViewRecord,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)):
    """Record a view (for trending algorithm)."""
    s = (await db.execute(select(Clip).where(Clip.id == clip_id))).scalar_one_or_none()
    if not s:
        raise HTTPException(status_code=404, detail="Clip not found")
    view = ClipView(
        clip_id=clip_id, user_id=current_user.id,
        watched_seconds=data.watched_seconds, completed=data.completed)
    db.add(view)
    s.view_count = (s.view_count or 0) + 1
    db.add(s)
    await db.flush()
    return {"message": "View recorded", "view_count": s.view_count}


@router.delete("/{clip_id}", status_code=204)
async def delete_clip(
    clip_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)):
    """Soft-delete a clip (only author or admin can delete)."""
    s = (await db.execute(select(Clip).where(
        Clip.id == clip_id, Clip.church_id == current_user.church_id
    ))).scalar_one_or_none()
    if not s:
        raise HTTPException(status_code=404, detail="Clip not found")
    if s.author_id != current_user.id and current_user.role not in ("admin", "pastor"):
        raise HTTPException(status_code=403, detail="Cannot delete this clip")
    s.is_deleted = True
    db.add(s)


@router.post("/{clip_id}/share", status_code=200)
async def share_clip(
    clip_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)):
    """Share a clip."""
    s = (await db.execute(select(Clip).where(Clip.id == clip_id))).scalar_one_or_none()
    if not s:
        raise HTTPException(status_code=404, detail="Clip not found")
    
    s.share_count = (s.share_count or 0) + 1
    db.add(s)
    await db.flush()
    
    share_url = f"https://app.church.com/s/{clip_id}"
    return {"message": "Clip shared", "share_count": s.share_count, "share_url": share_url}


async def _enrich(db, s, current_user):
    """Enrich a Clip with author/church names and like status."""
    author = (await db.execute(select(User).where(User.id == s.author_id))).scalar_one_or_none()
    church = (await db.execute(select(Church).where(Church.id == s.church_id))).scalar_one_or_none()
    is_amened = (await db.execute(select(ClipLike).where(
        ClipLike.clip_id == s.id, ClipLike.user_id == current_user.id
    ))).scalar_one_or_none() is not None
    return _clip_response(s,
        author.full_name if author else None,
        church.name if church else None,
        is_amened)
