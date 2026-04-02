"""Seek router — user search returning { data: FlockUser[] }."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_, func

from app.database import get_db
from app.models.user import User
from app.models.church import Church
from app.models.social import Follower
from app.utils.security import get_current_user

router = APIRouter(tags=["Seek"])


@router.get("/seek")
@router.get("/search")
async def seek_users(
    q: str = Query(..., min_length=1, description="Search query"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Search for users by name/username. Returns { data: FlockUser[] }."""
    term = f"%{q}%"

    users = (await db.execute(
        select(User).where(
            or_(
                User.full_name.ilike(term),
                User.username.ilike(term),
            )
        ).limit(30)
    )).scalars().all()

    items = []
    for u in users:
        church = None
        if u.church_id:
            church = (await db.execute(select(Church).where(Church.id == u.church_id))).scalar_one_or_none()

        is_following = (await db.execute(
            select(Follower).where(
                Follower.follower_id == current_user.id, Follower.followed_id == u.id
            )
        )).scalar_one_or_none() is not None

        fc = (await db.execute(select(func.count()).where(Follower.followed_id == u.id))).scalar() or 0

        items.append({
            "id": u.id,
            "full_name": u.full_name,
            "username": u.username,
            "avatar_url": getattr(u, "avatar_url", None),
            "church_name": church.name if church else None,
            "is_following": is_following,
            "followers_count": fc,
        })

    return {"data": items}
