from typing import List, Optional, Any
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.utils.security import get_current_user
from app.models.user import User
from app.models.user_activity import UserInteraction, UserContentView, RecentlyDeleted, InteractionType, ContentType
from app.models.settings import ArchivedContent
from app.models.feed import PostComment
from app.models.clip import ClipComment
from pydantic import BaseModel
import json

router = APIRouter(prefix="/activity", tags=["User Activity"])

class InteractionResponse(BaseModel):
    id: int
    type: str
    target_type: str
    target_id: str
    target_title: Optional[str]
    target_thumbnail: Optional[str]
    content: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class ContentViewResponse(BaseModel):
    id: int
    content_type: str
    content_id: str
    title: Optional[str]
    thumbnail_url: Optional[str]
    author_name: Optional[str]
    viewed_at: datetime

    class Config:
        from_attributes = True

class RecentlyDeletedResponse(BaseModel):
    id: int
    content_type: str
    title: Optional[str]
    thumbnail_url: Optional[str]
    deleted_at: datetime
    expires_at: datetime
    
    class Config:
        from_attributes = True

class CommentResponse(BaseModel):
    id: int
    content: str
    created_at: datetime
    comment_type: str
    item_id: str

@router.get("/interactions", response_model=List[InteractionResponse])
async def get_interactions(
    type: Optional[InteractionType] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not current_user.member_id:
        raise HTTPException(status_code=400, detail="User is not a member.")
        
    query = select(UserInteraction).where(UserInteraction.user_id == current_user.member_id)
    if type:
        query = query.where(UserInteraction.type == type)
        
    query = query.order_by(UserInteraction.created_at.desc()).limit(50)
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/comments", response_model=List[CommentResponse])
async def get_user_comments(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not current_user.member_id:
        raise HTTPException(status_code=400, detail="User is not a member.")
        
    post_comments_res = await db.execute(select(PostComment).where(PostComment.author_id == current_user.member_id))
    post_comments = post_comments_res.scalars().all()
    
    clip_comments_res = await db.execute(select(ClipComment).where(ClipComment.author_id == current_user.member_id))
    clip_comments = clip_comments_res.scalars().all()
    
    results = []
    for pc in post_comments:
        results.append({
            "id": pc.id,
            "content": pc.content,
            "created_at": pc.created_at,
            "comment_type": "post",
            "item_id": str(pc.post_id)
        })
    for cc in clip_comments:
        results.append({
            "id": cc.id,
            "content": cc.content,
            "created_at": cc.created_at,
            "comment_type": "clip",
            "item_id": str(cc.clip_id)
        })
        
    results.sort(key=lambda x: x["created_at"], reverse=True)
    return results

@router.delete("/comments/{comment_id}")
async def delete_user_comment(
    comment_id: int,
    comment_type: str = Query(..., description="Either 'post' or 'clip'"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not current_user.member_id:
        raise HTTPException(status_code=400, detail="User is not a member.")
        
    if comment_type == "post":
        res = await db.execute(select(PostComment).where(PostComment.id == comment_id, PostComment.author_id == current_user.member_id))
        comment = res.scalar_one_or_none()
    elif comment_type == "clip":
        res = await db.execute(select(ClipComment).where(ClipComment.id == comment_id, ClipComment.author_id == current_user.member_id))
        comment = res.scalar_one_or_none()
    else:
        raise HTTPException(status_code=400, detail="Invalid comment type. Use 'post' or 'clip'.")
        
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found.")
        
    await db.delete(comment)
    await db.commit()
    return {"message": "Comment deleted successfully."}

@router.get("/viewed", response_model=List[ContentViewResponse])
async def get_viewed_content(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not current_user.member_id:
        raise HTTPException(status_code=400, detail="User is not a member.")
        
    query = select(UserContentView).where(UserContentView.user_id == current_user.member_id).order_by(UserContentView.viewed_at.desc()).limit(50)
    res = await db.execute(query)
    return res.scalars().all()

@router.get("/recently-deleted", response_model=List[RecentlyDeletedResponse])
async def get_recently_deleted(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not current_user.member_id:
        raise HTTPException(status_code=400, detail="User is not a member.")
        
    query = select(RecentlyDeleted).where(
        RecentlyDeleted.user_id == current_user.member_id,
        RecentlyDeleted.expires_at > datetime.now(timezone.utc)
    ).order_by(RecentlyDeleted.deleted_at.desc())
    
    res = await db.execute(query)
    return res.scalars().all()

@router.post("/recently-deleted/{item_id}/restore")
async def restore_recently_deleted(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not current_user.member_id:
        raise HTTPException(status_code=400, detail="User is not a member.")
        
    res = await db.execute(select(RecentlyDeleted).where(
        RecentlyDeleted.id == item_id,
        RecentlyDeleted.user_id == current_user.member_id
    ))
    item = res.scalar_one_or_none()
    
    if not item:
        raise HTTPException(status_code=404, detail="Item not found or already expired.")
        
    data = item.original_data
    await db.delete(item)
    await db.commit()
    
    return {"message": "Content restored. (Re-insertion must be handled by proper service)", "data": data}

@router.delete("/recently-deleted/{item_id}")
async def permanently_delete_item(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not current_user.member_id:
        raise HTTPException(status_code=400, detail="User is not a member.")
        
    res = await db.execute(select(RecentlyDeleted).where(
        RecentlyDeleted.id == item_id,
        RecentlyDeleted.user_id == current_user.member_id
    ))
    item = res.scalar_one_or_none()
    
    if not item:
        raise HTTPException(status_code=404, detail="Item not found.")
        
    await db.delete(item)
    await db.commit()
    return {"message": "Item permanently deleted."}

@router.get("/archive/{content_type}")
async def get_archived_content(
    content_type: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not current_user.member_id:
        raise HTTPException(status_code=400, detail="User is not a member.")
        
    query = select(ArchivedContent).where(
        ArchivedContent.user_id == current_user.member_id,
        ArchivedContent.content_type == content_type
    ).order_by(ArchivedContent.archived_at.desc())
    
    res = await db.execute(query)
    return res.scalars().all()
