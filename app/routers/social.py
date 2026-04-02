"""Social router — flock (follow), meditations (saved), reports, with frontend-aligned paths."""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from typing import List

from app.database import get_db
from app.models.user import User
from app.models.social import Follower, Bookmark, Report, ReportStatus
from app.models.church import Church
from app.models.feed import Post
from app.schemas.social import (
    FollowerResponse, FollowerListResponse, BookmarkCreate, BookmarkResponse,
    ReportCreate, ReportResponse
)
from app.utils.security import get_current_user

router = APIRouter(tags=["Social"])


# ══════════════════════════════════════════════════════════════════
# FLOCK (Follow) System & Social User Profile
# ══════════════════════════════════════════════════════════════════

@router.get("/social/user/{user_id}")
async def get_user_profile(user_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Fetch social profile data for a specific user."""
    target_user = await db.get(User, user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
        
    church_name = None
    if target_user.church_id:
        church = await db.get(Church, target_user.church_id)
        if church:
            church_name = church.name

    is_following = False
    if current_user.id != user_id:
        existing = (await db.execute(
            select(Follower).where(Follower.follower_id == current_user.id, Follower.followed_id == user_id)
        )).scalar_one_or_none()
        if existing:
            is_following = True
            
    followers_count = (await db.execute(
        select(func.count()).where(Follower.followed_id == user_id)
    )).scalar() or 0
    
    following_count = (await db.execute(
        select(func.count()).where(Follower.follower_id == user_id)
    )).scalar() or 0
    
    post_count = (await db.execute(
        select(func.count()).where(Post.author_id == user_id, Post.is_deleted == False)
    )).scalar() or 0
    
    return {"data": {
        "id": str(target_user.id),
        "full_name": target_user.full_name,
        "username": getattr(target_user, "username", ""),
        "avatar_url": getattr(target_user, "avatar_url", None),
        "church_name": church_name,
        "bio": getattr(target_user, "testimony_summary", ""),
        "role": target_user.role,
        "is_following": is_following,
        "followers_count": followers_count,
        "following_count": following_count,
        "post_count": post_count,
        "created_at": target_user.created_at.isoformat() if target_user.created_at else None
    }}


@router.post("/social/flock/{user_id}", status_code=201)
async def follow_user(user_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Follow/join a user's flock. Toggle: if already following, unfollow."""
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="Cannot follow yourself")

    target = await db.get(User, user_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    existing = (await db.execute(
        select(Follower).where(Follower.follower_id == current_user.id, Follower.followed_id == user_id)
    )).scalar_one_or_none()

    if existing:
        # Toggle: unfollow
        await db.delete(existing)
        await db.commit()
        return {"data": {"following": False}}

    db.add(Follower(follower_id=current_user.id, followed_id=user_id))
    await db.commit()
    return {"data": {"following": True}}


@router.delete("/social/flock/{user_id}", status_code=204)
async def unfollow_user(user_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = (await db.execute(
        select(Follower).where(Follower.follower_id == current_user.id, Follower.followed_id == user_id)
    )).scalar_one_or_none()
    if not result:
        raise HTTPException(status_code=404, detail="Not following this user")
    await db.delete(result)
    await db.commit()


@router.get("/social/flock/stats")
async def flock_stats(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Get current user's follower/following counts."""
    followers_count = (await db.execute(
        select(func.count()).where(Follower.followed_id == current_user.id)
    )).scalar() or 0
    following_count = (await db.execute(
        select(func.count()).where(Follower.follower_id == current_user.id)
    )).scalar() or 0
    return {"data": {"followers_count": followers_count, "following_count": following_count}}


@router.get("/social/flock/suggestions")
async def flock_suggestions(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Suggest users to follow — same church, not yet followed."""
    already_following = (await db.execute(
        select(Follower.followed_id).where(Follower.follower_id == current_user.id)
    )).scalars().all()

    exclude_ids = set(already_following) | {current_user.id}

    query = select(User).where(User.id.notin_(exclude_ids))
    if current_user.church_id:
        query = query.where(User.church_id == current_user.church_id)
    query = query.limit(20)

    users = (await db.execute(query)).scalars().all()

    items = []
    for u in users:
        church = None
        if u.church_id:
            church = (await db.execute(select(Church).where(Church.id == u.church_id))).scalar_one_or_none()
        fc = (await db.execute(select(func.count()).where(Follower.followed_id == u.id))).scalar() or 0
        items.append({
            "id": u.id,
            "full_name": u.full_name,
            "username": u.username,
            "avatar_url": getattr(u, "avatar_url", None),
            "church_name": church.name if church else None,
            "is_following": False,
            "followers_count": fc,
        })
    return {"data": items}


@router.get("/social/flock/{user_id}/followers")
async def get_followers(user_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(
        select(Follower, User).join(User, Follower.follower_id == User.id).where(Follower.followed_id == user_id)
    )
    items = []
    for member, user in result.all():
        is_following = (await db.execute(
            select(Follower).where(Follower.follower_id == current_user.id, Follower.followed_id == user.id)
        )).scalar_one_or_none() is not None
        items.append({
            "id": user.id, "full_name": user.full_name, "username": user.username,
            "avatar_url": getattr(user, "avatar_url", None), "is_following": is_following,
        })
    return {"data": items}


@router.get("/social/flock/{user_id}/following")
async def get_following(user_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(
        select(Follower, User).join(User, Follower.followed_id == User.id).where(Follower.follower_id == user_id)
    )
    items = []
    for member, user in result.all():
        is_following = (await db.execute(
            select(Follower).where(Follower.follower_id == current_user.id, Follower.followed_id == user.id)
        )).scalar_one_or_none() is not None
        items.append({
            "id": user.id, "full_name": user.full_name, "username": user.username,
            "avatar_url": getattr(user, "avatar_url", None), "is_following": is_following,
        })
    return {"data": items}


# ══════════════════════════════════════════════════════════════════
# SAVED ITEMS (Bookmarks) — /saved/* aliases
# ══════════════════════════════════════════════════════════════════

@router.post("/saved", status_code=201)
async def save_item(save_data: BookmarkCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    existing = (await db.execute(
        select(Bookmark).where(
            Bookmark.user_id == current_user.id,
            Bookmark.entity_type == save_data.entity_type,
            Bookmark.entity_id == save_data.entity_id,
        )
    )).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Already saved")

    m = Bookmark(user_id=current_user.id, entity_type=save_data.entity_type, entity_id=save_data.entity_id)
    db.add(m)
    await db.commit()
    await db.refresh(m)
    return {"data": {"id": m.id, "item_id": m.entity_id, "item_type": m.entity_type}}


@router.delete("/saved/{item_id}")
async def unsave_item(item_id: int, type: str = Query("post"), db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = (await db.execute(
        select(Bookmark).where(
            Bookmark.user_id == current_user.id,
            Bookmark.entity_type == type,
            Bookmark.entity_id == item_id,
        )
    )).scalar_one_or_none()
    if not result:
        raise HTTPException(status_code=404, detail="Saved item not found")
    await db.delete(result)
    await db.commit()
    return {"message": "Unsaved"}


@router.get("/saved")
async def get_saved(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = (await db.execute(
        select(Bookmark).where(Bookmark.user_id == current_user.id).order_by(Bookmark.created_at.desc())
    )).scalars().all()
    items = [{"id": m.id, "item_id": m.entity_id, "item_type": m.entity_type,
              "created_at": m.created_at.isoformat() if m.created_at else None} for m in result]
    return {"data": items}


# ══════════════════════════════════════════════════════════════════
# REPORTS
# ══════════════════════════════════════════════════════════════════

@router.post("/reports", status_code=201)
async def report_content(report_data: ReportCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    new_report = Report(
        reporter_id=current_user.id,
        entity_type=report_data.entity_type,
        entity_id=report_data.entity_id,
        reason=report_data.reason,
        status=ReportStatus.PENDING.value,
    )
    db.add(new_report)
    await db.commit()
    await db.refresh(new_report)
    return {"data": {"id": new_report.id, "status": "pending"}}
