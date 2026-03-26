"""Shorts router — cross-church video platform with trending."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case
from datetime import datetime, timezone, timedelta

from app.database import get_db
from app.models.short import Short, ShortLike, ShortComment, ShortView
from app.models.user import User
from app.models.church import Church
from app.models.notification import create_notification
from app.schemas.short import (
    ShortCreate, ShortUpdate, ShortResponse,
    ShortCommentCreate, ShortCommentResponse, ShortViewRecord,
)
from app.utils.security import get_current_user

router = APIRouter(prefix="/shorts", tags=["Shorts (Cross-Church)"])


def _short_response(s, author_name=None, church_name=None, is_liked=False):
    return ShortResponse(
        id=s.id, author_id=s.author_id, author_name=author_name,
        church_id=s.church_id, church_name=church_name,
        title=s.title, description=s.description, video_url=s.video_url,
        thumbnail_url=s.thumbnail_url, duration_seconds=s.duration_seconds,
        category=s.category, moderation_status=s.moderation_status,
        view_count=s.view_count, like_count=s.like_count,
        comment_count=s.comment_count, share_count=s.share_count,
        is_featured=s.is_featured, tags=s.tags or [],
        is_liked_by_me=is_liked, created_at=s.created_at)


@router.get("", response_model=list[ShortResponse])
async def get_shorts_feed(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    category: str = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)):
    """Get shorts feed — cross-church, all approved shorts."""
    query = select(Short).where(
        Short.is_deleted == False,
        Short.moderation_status == "approved")
    if category:
        query = query.where(Short.category == category)
    query = query.order_by(Short.is_featured.desc(), Short.created_at.desc())
    query = query.offset(offset).limit(limit)

    shorts = (await db.execute(query)).scalars().all()
    return [await _enrich(db, s, current_user) for s in shorts]


@router.get("/trending", response_model=list[ShortResponse])
async def get_trending(
    limit: int = Query(20, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)):
    """Trending shorts based on weighted engagement in the last 7 days.
    Score = (views * 1) + (likes * 3) + (comments * 5) + (completion_rate * 10)
    """
    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)

    # Get recent shorts with their engagement
    query = select(Short).where(
        Short.is_deleted == False,
        Short.moderation_status == "approved",
        Short.created_at >= seven_days_ago,
    )
    shorts = (await db.execute(query)).scalars().all()

    # Calculate trending score
    scored = []
    for s in shorts:
        # Completion rate from views
        completion_count = (await db.execute(
            select(func.count()).where(
                ShortView.short_id == s.id, ShortView.completed == True)
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


@router.get("/my-church", response_model=list[ShortResponse])
async def get_my_church_shorts(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)):
    """Get shorts from my church only."""
    query = select(Short).where(
        Short.church_id == current_user.church_id,
        Short.is_deleted == False,
        Short.moderation_status == "approved")
    query = query.order_by(Short.created_at.desc()).offset(offset).limit(limit)
    shorts = (await db.execute(query)).scalars().all()
    return [await _enrich(db, s, current_user) for s in shorts]


@router.post("", response_model=ShortResponse, status_code=201)
async def create_short(
    data: ShortCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)):
    """Upload a new short."""
    short = Short(
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
    db.add(short)
    await db.flush()
    await db.refresh(short)
    return _short_response(short, current_user.full_name)


@router.get("/{short_id}", response_model=ShortResponse)
async def get_short(
    short_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)):
    s = (await db.execute(select(Short).where(
        Short.id == short_id, Short.is_deleted == False))).scalar_one_or_none()
    if not s:
        raise HTTPException(status_code=404, detail="Short not found")
    return await _enrich(db, s, current_user)


@router.post("/{short_id}/like", status_code=201)
async def like_short(
    short_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)):
    s = (await db.execute(select(Short).where(Short.id == short_id))).scalar_one_or_none()
    if not s:
        raise HTTPException(status_code=404, detail="Short not found")
    existing = (await db.execute(select(ShortLike).where(
        ShortLike.short_id == short_id, ShortLike.user_id == current_user.id
    ))).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Already liked")
    db.add(ShortLike(short_id=short_id, user_id=current_user.id))
    s.like_count = (s.like_count or 0) + 1
    db.add(s)

    # Notify author
    if s.author_id != current_user.id:
        await create_notification(db, s.author_id, "like",
            f"{current_user.full_name} liked your short",
            data={"link_type": "short", "link_id": short_id})

    await db.flush()
    return {"message": "Liked", "like_count": s.like_count}


@router.delete("/{short_id}/like", status_code=200)
async def unlike_short(
    short_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)):
    existing = (await db.execute(select(ShortLike).where(
        ShortLike.short_id == short_id, ShortLike.user_id == current_user.id
    ))).scalar_one_or_none()
    if not existing:
        raise HTTPException(status_code=400, detail="Not liked")
    await db.delete(existing)
    s = (await db.execute(select(Short).where(Short.id == short_id))).scalar_one_or_none()
    if s:
        s.like_count = max((s.like_count or 0) - 1, 0)
        db.add(s)
    return {"message": "Unliked", "like_count": s.like_count if s else 0}


@router.post("/{short_id}/comments", response_model=ShortCommentResponse, status_code=201)
async def add_comment(
    short_id: int, data: ShortCommentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)):
    s = (await db.execute(select(Short).where(Short.id == short_id))).scalar_one_or_none()
    if not s:
        raise HTTPException(status_code=404, detail="Short not found")
    comment = ShortComment(
        short_id=short_id, author_id=current_user.id,
        content=data.content, parent_id=data.parent_id)
    db.add(comment)
    s.comment_count = (s.comment_count or 0) + 1
    db.add(s)

    if s.author_id != current_user.id:
        await create_notification(db, s.author_id, "comment",
            f"{current_user.full_name} commented on your short",
            body=data.content[:100],
            data={"link_type": "short", "link_id": short_id})

    await db.flush()
    await db.refresh(comment)
    return ShortCommentResponse(
        id=comment.id, short_id=comment.short_id, author_id=comment.author_id,
        author_name=current_user.full_name, content=comment.content,
        parent_id=comment.parent_id, created_at=comment.created_at)


@router.get("/{short_id}/comments", response_model=list[ShortCommentResponse])
async def get_comments(
    short_id: int,
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)):
    comments = (await db.execute(
        select(ShortComment).where(
            ShortComment.short_id == short_id,
            ShortComment.parent_id.is_(None),
            ShortComment.is_deleted == False)
        .order_by(ShortComment.created_at.desc()).limit(limit)
    )).scalars().all()

    items = []
    for c in comments:
        author = (await db.execute(select(User).where(User.id == c.author_id))).scalar_one_or_none()
        replies_rows = (await db.execute(
            select(ShortComment).where(ShortComment.parent_id == c.id, ShortComment.is_deleted == False)
            .order_by(ShortComment.created_at)
        )).scalars().all()
        replies = []
        for r in replies_rows:
            ra = (await db.execute(select(User).where(User.id == r.author_id))).scalar_one_or_none()
            replies.append(ShortCommentResponse(
                id=r.id, short_id=r.short_id, author_id=r.author_id,
                author_name=ra.full_name if ra else None, content=r.content,
                parent_id=r.parent_id, created_at=r.created_at))
        items.append(ShortCommentResponse(
            id=c.id, short_id=c.short_id, author_id=c.author_id,
            author_name=author.full_name if author else None, content=c.content,
            parent_id=c.parent_id, created_at=c.created_at, replies=replies))
    return items


@router.post("/{short_id}/view")
async def record_view(
    short_id: int, data: ShortViewRecord,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)):
    """Record a view (for trending algorithm)."""
    s = (await db.execute(select(Short).where(Short.id == short_id))).scalar_one_or_none()
    if not s:
        raise HTTPException(status_code=404, detail="Short not found")
    view = ShortView(
        short_id=short_id, user_id=current_user.id,
        watched_seconds=data.watched_seconds, completed=data.completed)
    db.add(view)
    s.view_count = (s.view_count or 0) + 1
    db.add(s)
    await db.flush()
    return {"message": "View recorded", "view_count": s.view_count}


async def _enrich(db, s, current_user):
    """Enrich a Short with author/church names and like status."""
    author = (await db.execute(select(User).where(User.id == s.author_id))).scalar_one_or_none()
    church = (await db.execute(select(Church).where(Church.id == s.church_id))).scalar_one_or_none()
    is_liked = (await db.execute(select(ShortLike).where(
        ShortLike.short_id == s.id, ShortLike.user_id == current_user.id
    ))).scalar_one_or_none() is not None
    return _short_response(s,
        author.full_name if author else None,
        church.name if church else None,
        is_liked)
