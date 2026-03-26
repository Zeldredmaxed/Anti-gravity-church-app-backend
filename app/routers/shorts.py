"""Shorts router — maps /shorts/* paths to GloryClips logic for frontend compatibility."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models.glory_clip import GloryClip, GloryClipAmen, GloryClipComment, GloryClipView
from app.models.user import User
from app.models.church import Church
from app.schemas.glory_clip import GloryClipCreate, GloryClipCommentCreate
from app.utils.security import get_current_user

router = APIRouter(prefix="/shorts", tags=["Shorts (Glory Clips)"])


def _short_response(s, author_name=None, church_name=None, is_amened=False):
    return {
        "id": s.id,
        "title": s.title,
        "description": s.description,
        "video_url": s.video_url,
        "thumbnail_url": s.thumbnail_url,
        "author_id": s.author_id,
        "author_name": author_name,
        "church_name": church_name,
        "church_id": s.church_id,
        "like_count": s.amen_count or 0,
        "comment_count": s.comment_count or 0,
        "view_count": s.view_count or 0,
        "share_count": s.share_count or 0,
        "is_liked": is_amened,
        "category": s.category,
        "created_at": s.created_at.isoformat() if s.created_at else None,
    }


async def _enrich(db, clip, current_user):
    author = (await db.execute(select(User).where(User.id == clip.author_id))).scalar_one_or_none()
    church = (await db.execute(select(Church).where(Church.id == clip.church_id))).scalar_one_or_none()
    is_amened = (await db.execute(select(GloryClipAmen).where(
        GloryClipAmen.glory_clip_id == clip.id, GloryClipAmen.user_id == current_user.id
    ))).scalar_one_or_none() is not None
    return _short_response(
        clip,
        author.full_name if author else None,
        church.name if church else None,
        is_amened,
    )


# ── GET /shorts/trending ──────────────────────────────────────────
@router.get("/trending")
async def get_trending(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(GloryClip)
        .where(GloryClip.is_deleted == False, GloryClip.moderation_status == "approved")
        .order_by(GloryClip.view_count.desc(), GloryClip.created_at.desc())
        .offset(offset).limit(limit)
    )
    clips = (await db.execute(query)).scalars().all()
    items = [await _enrich(db, c, current_user) for c in clips]
    return {"data": items}


# ── GET /shorts/my-church ─────────────────────────────────────────
@router.get("/my-church")
async def get_my_church_shorts(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(GloryClip)
        .where(
            GloryClip.church_id == current_user.church_id,
            GloryClip.is_deleted == False,
        )
        .order_by(GloryClip.created_at.desc())
        .offset(offset).limit(limit)
    )
    clips = (await db.execute(query)).scalars().all()
    items = [await _enrich(db, c, current_user) for c in clips]
    return {"data": items}


# ── POST /shorts ──────────────────────────────────────────────────
@router.post("", status_code=201)
async def create_short(
    data: GloryClipCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    clip = GloryClip(
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
    return {"data": await _enrich(db, clip, current_user)}


# ── POST /shorts/{id}/like ────────────────────────────────────────
@router.post("/{short_id}/like")
async def like_short(
    short_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    clip = (await db.execute(select(GloryClip).where(GloryClip.id == short_id))).scalar_one_or_none()
    if not clip:
        raise HTTPException(status_code=404, detail="Short not found")

    existing = (await db.execute(select(GloryClipAmen).where(
        GloryClipAmen.glory_clip_id == short_id, GloryClipAmen.user_id == current_user.id
    ))).scalar_one_or_none()

    if existing:
        return {"data": {"liked": True, "like_count": clip.amen_count or 0}}

    db.add(GloryClipAmen(glory_clip_id=short_id, user_id=current_user.id))
    clip.amen_count = (clip.amen_count or 0) + 1
    db.add(clip)
    await db.flush()
    return {"data": {"liked": True, "like_count": clip.amen_count}}


# ── DELETE /shorts/{id}/unlike ────────────────────────────────────
@router.delete("/{short_id}/unlike")
async def unlike_short(
    short_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    existing = (await db.execute(select(GloryClipAmen).where(
        GloryClipAmen.glory_clip_id == short_id, GloryClipAmen.user_id == current_user.id
    ))).scalar_one_or_none()
    if not existing:
        return {"data": {"liked": False}}

    await db.delete(existing)
    clip = (await db.execute(select(GloryClip).where(GloryClip.id == short_id))).scalar_one_or_none()
    if clip:
        clip.amen_count = max((clip.amen_count or 0) - 1, 0)
        db.add(clip)
    await db.flush()
    return {"data": {"liked": False, "like_count": clip.amen_count if clip else 0}}


# ── POST /shorts/{id}/view ────────────────────────────────────────
@router.post("/{short_id}/view")
async def view_short(
    short_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    clip = (await db.execute(select(GloryClip).where(GloryClip.id == short_id))).scalar_one_or_none()
    if not clip:
        raise HTTPException(status_code=404, detail="Short not found")
    clip.view_count = (clip.view_count or 0) + 1
    db.add(clip)
    db.add(GloryClipView(glory_clip_id=short_id, user_id=current_user.id))
    await db.flush()
    return {"data": {"view_count": clip.view_count}}


# ── POST /shorts/{id}/share ──────────────────────────────────────
@router.post("/{short_id}/share")
async def share_short(
    short_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    clip = (await db.execute(select(GloryClip).where(GloryClip.id == short_id))).scalar_one_or_none()
    if not clip:
        raise HTTPException(status_code=404, detail="Short not found")
    clip.share_count = (clip.share_count or 0) + 1
    db.add(clip)
    await db.flush()
    return {"data": {"share_count": clip.share_count}}


# ── DELETE /shorts/{id} ──────────────────────────────────────────
@router.delete("/{short_id}", status_code=204)
async def delete_short(
    short_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    clip = (await db.execute(select(GloryClip).where(GloryClip.id == short_id))).scalar_one_or_none()
    if not clip:
        raise HTTPException(status_code=404, detail="Short not found")
    if clip.author_id != current_user.id and current_user.role not in ("admin", "pastor"):
        raise HTTPException(status_code=403, detail="Cannot delete this short")
    clip.is_deleted = True
    db.add(clip)


# ══════════════════════════════════════════════════════════════════
# COMMENTS ON SHORTS
# ══════════════════════════════════════════════════════════════════

@router.get("/{short_id}/comments")
async def get_short_comments(
    short_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    comments = (await db.execute(
        select(GloryClipComment).where(
            GloryClipComment.glory_clip_id == short_id,
            GloryClipComment.is_deleted == False,
        ).order_by(GloryClipComment.created_at)
    )).scalars().all()

    items = []
    for c in comments:
        author = (await db.execute(select(User).where(User.id == c.author_id))).scalar_one_or_none()
        items.append({
            "id": c.id,
            "author_name": author.full_name if author else None,
            "author_avatar": getattr(author, "avatar_url", None) if author else None,
            "content": c.content,
            "like_count": 0,
            "is_liked": False,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        })
    return {"data": items}


@router.post("/{short_id}/comments", status_code=201)
async def add_short_comment(
    short_id: int,
    data: GloryClipCommentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    clip = (await db.execute(select(GloryClip).where(GloryClip.id == short_id))).scalar_one_or_none()
    if not clip:
        raise HTTPException(status_code=404, detail="Short not found")

    comment = GloryClipComment(
        glory_clip_id=short_id, author_id=current_user.id,
        content=data.content, parent_id=data.parent_id,
    )
    db.add(comment)
    clip.comment_count = (clip.comment_count or 0) + 1
    db.add(clip)
    await db.flush()
    await db.refresh(comment)

    return {"data": {
        "id": comment.id,
        "author_name": current_user.full_name,
        "author_avatar": getattr(current_user, "avatar_url", None),
        "content": comment.content,
        "like_count": 0,
        "is_liked": False,
        "created_at": comment.created_at.isoformat() if comment.created_at else None,
    }}


@router.post("/{short_id}/comments/{comment_id}/like")
async def toggle_short_comment_like(
    short_id: int, comment_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    c = (await db.execute(select(GloryClipComment).where(
        GloryClipComment.id == comment_id, GloryClipComment.glory_clip_id == short_id
    ))).scalar_one_or_none()
    if not c:
        raise HTTPException(status_code=404, detail="Comment not found")
    return {"data": {"liked": True, "like_count": 1}}
