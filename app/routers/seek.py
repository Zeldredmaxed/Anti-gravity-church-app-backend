from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_

from app.database import get_db
from app.models.user import User
from app.models.church import Church
from app.models.glory_clip import GloryClip
from app.utils.security import get_current_user

router = APIRouter(tags=["Seek"])


@router.get("/seek")
async def global_seek(
    q: str = Query(..., min_length=2, description="Search query"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Unified global search for finding people, churches, and glory_clips.
    """
    seek_term = f"%{q}%"
    
    # 1. Search Users
    users_result = await db.execute(
        select(User.id, User.username, User.full_name, User.avatar_url)
        .where(
            or_(
                User.username.ilike(seek_term),
                User.full_name.ilike(seek_term)
            )
        )
        .limit(10)
    )
    users = [{"type": "user", **row._mapping} for row in users_result.all()]

    # 2. Search Churches
    churches_result = await db.execute(
        select(Church.id, Church.name, Church.slug)
        .where(Church.name.ilike(seek_term))
        .limit(10)
    )
    churches = [{"type": "church", **row._mapping} for row in churches_result.all()]
    
    # 3. Search GloryClips (caption search)
    glory_clips_result = await db.execute(
        select(GloryClip.id, GloryClip.caption, GloryClip.video_url, GloryClip.author_id)
        .where(GloryClip.caption.ilike(seek_term))
        .limit(10)
    )
    glory_clips = [{"type": "glory_clip", **row._mapping} for row in glory_clips_result.all()]
    
    return {
        "query": q,
        "results": {
            "users": users,
            "churches": churches,
            "glory_clips": glory_clips
        }
    }
