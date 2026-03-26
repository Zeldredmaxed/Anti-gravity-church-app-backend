"""GloryClips router — cross-church video platform with trending."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case
from datetime import datetime, timezone, timedelta

from app.database import get_db
from app.models.glory_clip import GloryClip, GloryClipAmen, GloryClipComment, GloryClipView
from app.models.user import User
from app.models.church import Church
from app.models.alert import create_alert
from app.schemas.glory_clip import (
    GloryClipCreate, GloryClipUpdate, GloryClipResponse,
    GloryClipCommentCreate, GloryClipCommentResponse, GloryClipViewRecord,
)
from app.utils.security import get_current_user
from app.utils.mentions import process_mentions

router = APIRouter(prefix="/glory_clips", tags=["GloryClips (Cross-Church)"])


def _glory_clip_response(s, author_name=None, church_name=None, is_amened=False):
    return GloryClipResponse(
        id=s.id, author_id=s.author_id, author_name=author_name,
        church_id=s.church_id, church_name=church_name,
        title=s.title, description=s.description, video_url=s.video_url,
        thumbnail_url=s.thumbnail_url, duration_seconds=s.duration_seconds,
        category=s.category, moderation_status=s.moderation_status,
        view_count=s.view_count, amen_count=s.amen_count,
        comment_count=s.comment_count, share_count=s.share_count,
        is_featured=s.is_featured, tags=s.tags or [],
        is_amened_by_me=is_amened, created_at=s.created_at)


@router.get("", response_model=list[GloryClipResponse])
async def get_glory_clips_feed(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    category: str = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)):
    """Get glory_clips feed — cross-church, all approved glory_clips."""
    query = select(GloryClip).where(
        GloryClip.is_deleted == False,
        GloryClip.moderation_status == "approved")
    if category:
        query = query.where(GloryClip.category == category)
    query = query.order_by(GloryClip.is_featured.desc(), GloryClip.created_at.desc())
    query = query.offset(offset).limit(limit)

    glory_clips = (await db.execute(query)).scalars().all()
    return [await _enrich(db, s, current_user) for s in glory_clips]


@router.get("/trending", response_model=list[GloryClipResponse])
async def get_trending(
    limit: int = Query(20, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)):
    """Trending glory_clips based on weighted engagement in the last 7 days.
    Score = (views * 1) + (likes * 3) + (comments * 5) + (completion_rate * 10)
    """
    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)

    # Get recent glory_clips with their engagement
    query = select(GloryClip).where(
        GloryClip.is_deleted == False,
        GloryClip.moderation_status == "approved",
        GloryClip.created_at >= seven_days_ago,
    )
    glory_clips = (await db.execute(query)).scalars().all()

    # Calculate trending score
    scored = []
    for s in glory_clips:
        # Completion rate from views
        completion_count = (await db.execute(
            select(func.count()).where(
                GloryClipView.glory_clip_id == s.id, GloryClipView.completed == True)
        )).scalar() or 0
        total_views = max(s.view_count, 1)
        completion_rate = completion_count / total_views

        score = (
            (s.view_count or 0) * 1
            + (s.amen_count or 0) * 3
            + (s.comment_count or 0) * 5
            + completion_rate * 10
        )
        scored.append((s, score))

    scored.sort(key=lambda x: x[1], reverse=True)
    top = [s for s, _ in scored[:limit]]
    return [await _enrich(db, s, current_user) for s in top]


@router.get("/my-church", response_model=list[GloryClipResponse])
async def get_my_church_glory_clips(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)):
    """Get glory_clips from my church only."""
    query = select(GloryClip).where(
        GloryClip.church_id == current_user.church_id,
        GloryClip.is_deleted == False,
        GloryClip.moderation_status == "approved")
    query = query.order_by(GloryClip.created_at.desc()).offset(offset).limit(limit)
    glory_clips = (await db.execute(query)).scalars().all()
    return [await _enrich(db, s, current_user) for s in glory_clips]


@router.post("", response_model=GloryClipResponse, status_code=201)
async def create_glory_clip(
    data: GloryClipCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)):
    """Upload a new glory_clip."""
    glory_clip = GloryClip(
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
    db.add(glory_clip)
    await db.flush()
    await db.refresh(glory_clip)
    await process_mentions(db, glory_clip.description, current_user.id, "glory_clip", glory_clip.id)
    return _glory_clip_response(glory_clip, current_user.full_name)


@router.get("/{glory_clip_id}", response_model=GloryClipResponse)
async def get_glory_clip(
    glory_clip_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)):
    s = (await db.execute(select(GloryClip).where(
        GloryClip.id == glory_clip_id, GloryClip.is_deleted == False))).scalar_one_or_none()
    if not s:
        raise HTTPException(status_code=404, detail="GloryClip not found")
    return await _enrich(db, s, current_user)


@router.post("/{glory_clip_id}/amen", status_code=201)
async def amen_glory_clip(
    glory_clip_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)):
    s = (await db.execute(select(GloryClip).where(GloryClip.id == glory_clip_id))).scalar_one_or_none()
    if not s:
        raise HTTPException(status_code=404, detail="GloryClip not found")
    existing = (await db.execute(select(GloryClipAmen).where(
        GloryClipAmen.glory_clip_id == glory_clip_id, GloryClipAmen.user_id == current_user.id
    ))).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Already amened")
    db.add(GloryClipAmen(glory_clip_id=glory_clip_id, user_id=current_user.id))
    s.amen_count = (s.amen_count or 0) + 1
    db.add(s)

    # Notify author
    if s.author_id != current_user.id:
        await create_alert(db, s.author_id, "like",
            f"{current_user.full_name} amened your glory clip",
            data={"link_type": "glory_clip", "link_id": glory_clip_id})

    await db.flush()
    return {"message": "Amened", "amen_count": s.amen_count}


@router.delete("/{glory_clip_id}/amen", status_code=200)
async def unamen_glory_clip(
    glory_clip_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)):
    existing = (await db.execute(select(GloryClipAmen).where(
        GloryClipAmen.glory_clip_id == glory_clip_id, GloryClipAmen.user_id == current_user.id
    ))).scalar_one_or_none()
    if not existing:
        raise HTTPException(status_code=400, detail="Not amened")
    await db.delete(existing)
    s = (await db.execute(select(GloryClip).where(GloryClip.id == glory_clip_id))).scalar_one_or_none()
    if s:
        s.amen_count = max((s.amen_count or 0) - 1, 0)
        db.add(s)
    return {"message": "Unamened", "amen_count": s.amen_count if s else 0}


@router.post("/{glory_clip_id}/comments", response_model=GloryClipCommentResponse, status_code=201)
async def add_comment(
    glory_clip_id: int, data: GloryClipCommentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)):
    s = (await db.execute(select(GloryClip).where(GloryClip.id == glory_clip_id))).scalar_one_or_none()
    if not s:
        raise HTTPException(status_code=404, detail="GloryClip not found")
    comment = GloryClipComment(
        glory_clip_id=glory_clip_id, author_id=current_user.id,
        content=data.content, parent_id=data.parent_id)
    db.add(comment)
    s.comment_count = (s.comment_count or 0) + 1
    db.add(s)

    if s.author_id != current_user.id:
        await create_alert(db, s.author_id, "comment",
            f"{current_user.full_name} commented on your glory clip",
            body=data.content[:100],
            data={"link_type": "glory_clip", "link_id": glory_clip_id})

    await db.flush()
    await db.refresh(comment)
    
    await process_mentions(db, comment.content, current_user.id, "glory_clip_comment", comment.id)
    
    return GloryClipCommentResponse(
        id=comment.id, glory_clip_id=comment.glory_clip_id, author_id=comment.author_id,
        author_name=current_user.full_name, content=comment.content,
        parent_id=comment.parent_id, created_at=comment.created_at)


@router.get("/{glory_clip_id}/comments", response_model=list[GloryClipCommentResponse])
async def get_comments(
    glory_clip_id: int,
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)):
    comments = (await db.execute(
        select(GloryClipComment).where(
            GloryClipComment.glory_clip_id == glory_clip_id,
            GloryClipComment.parent_id.is_(None),
            GloryClipComment.is_deleted == False)
        .order_by(GloryClipComment.created_at.desc()).limit(limit)
    )).scalars().all()

    items = []
    for c in comments:
        author = (await db.execute(select(User).where(User.id == c.author_id))).scalar_one_or_none()
        replies_rows = (await db.execute(
            select(GloryClipComment).where(GloryClipComment.parent_id == c.id, GloryClipComment.is_deleted == False)
            .order_by(GloryClipComment.created_at)
        )).scalars().all()
        replies = []
        for r in replies_rows:
            ra = (await db.execute(select(User).where(User.id == r.author_id))).scalar_one_or_none()
            replies.append(GloryClipCommentResponse(
                id=r.id, glory_clip_id=r.glory_clip_id, author_id=r.author_id,
                author_name=ra.full_name if ra else None, content=r.content,
                parent_id=r.parent_id, created_at=r.created_at))
        items.append(GloryClipCommentResponse(
            id=c.id, glory_clip_id=c.glory_clip_id, author_id=c.author_id,
            author_name=author.full_name if author else None, content=c.content,
            parent_id=c.parent_id, created_at=c.created_at, replies=replies))
    return items


@router.post("/{glory_clip_id}/view")
async def record_view(
    glory_clip_id: int, data: GloryClipViewRecord,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)):
    """Record a view (for trending algorithm)."""
    s = (await db.execute(select(GloryClip).where(GloryClip.id == glory_clip_id))).scalar_one_or_none()
    if not s:
        raise HTTPException(status_code=404, detail="GloryClip not found")
    view = GloryClipView(
        glory_clip_id=glory_clip_id, user_id=current_user.id,
        watched_seconds=data.watched_seconds, completed=data.completed)
    db.add(view)
    s.view_count = (s.view_count or 0) + 1
    db.add(s)
    await db.flush()
    return {"message": "View recorded", "view_count": s.view_count}


@router.delete("/{glory_clip_id}", status_code=204)
async def delete_glory_clip(
    glory_clip_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)):
    """Soft-delete a glory_clip (only author or admin can delete)."""
    s = (await db.execute(select(GloryClip).where(
        GloryClip.id == glory_clip_id, GloryClip.church_id == current_user.church_id
    ))).scalar_one_or_none()
    if not s:
        raise HTTPException(status_code=404, detail="GloryClip not found")
    if s.author_id != current_user.id and current_user.role not in ("admin", "pastor"):
        raise HTTPException(status_code=403, detail="Cannot delete this glory_clip")
    s.is_deleted = True
    db.add(s)


@router.post("/{glory_clip_id}/share", status_code=200)
async def share_glory_clip(
    glory_clip_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)):
    """Share a glory_clip."""
    s = (await db.execute(select(GloryClip).where(GloryClip.id == glory_clip_id))).scalar_one_or_none()
    if not s:
        raise HTTPException(status_code=404, detail="GloryClip not found")
    
    s.share_count = (s.share_count or 0) + 1
    db.add(s)
    await db.flush()
    
    share_url = f"https://app.church.com/s/{glory_clip_id}"
    return {"message": "GloryClip shared", "share_count": s.share_count, "share_url": share_url}


async def _enrich(db, s, current_user):
    """Enrich a GloryClip with author/church names and like status."""
    author = (await db.execute(select(User).where(User.id == s.author_id))).scalar_one_or_none()
    church = (await db.execute(select(Church).where(Church.id == s.church_id))).scalar_one_or_none()
    is_amened = (await db.execute(select(GloryClipAmen).where(
        GloryClipAmen.glory_clip_id == s.id, GloryClipAmen.user_id == current_user.id
    ))).scalar_one_or_none() is not None
    return _glory_clip_response(s,
        author.full_name if author else None,
        church.name if church else None,
        is_amened)
