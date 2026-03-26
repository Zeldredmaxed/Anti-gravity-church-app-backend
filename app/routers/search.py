from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_

from app.database import get_db
from app.models.user import User
from app.models.church import Church
from app.models.short import Short
from app.utils.security import get_current_user

router = APIRouter(tags=["Search"])


@router.get("/search")
async def global_search(
    q: str = Query(..., min_length=2, description="Search query"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Unified global search for finding people, churches, and shorts.
    """
    search_term = f"%{q}%"
    
    # 1. Search Users
    users_result = await db.execute(
        select(User.id, User.username, User.full_name, User.avatar_url)
        .where(
            or_(
                User.username.ilike(search_term),
                User.full_name.ilike(search_term)
            )
        )
        .limit(10)
    )
    users = [{"type": "user", **row._mapping} for row in users_result.all()]

    # 2. Search Churches
    churches_result = await db.execute(
        select(Church.id, Church.name, Church.slug)
        .where(Church.name.ilike(search_term))
        .limit(10)
    )
    churches = [{"type": "church", **row._mapping} for row in churches_result.all()]
    
    # 3. Search Shorts (caption search)
    shorts_result = await db.execute(
        select(Short.id, Short.caption, Short.video_url, Short.author_id)
        .where(Short.caption.ilike(search_term))
        .limit(10)
    )
    shorts = [{"type": "short", **row._mapping} for row in shorts_result.all()]
    
    return {
        "query": q,
        "results": {
            "users": users,
            "churches": churches,
            "shorts": shorts
        }
    }
