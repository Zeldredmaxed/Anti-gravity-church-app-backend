"""Saved Items router — sync bookmarks across devices."""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional, List

from app.database import get_db
from app.models.user import User
from app.models.saved import SavedItem
from app.utils.security import get_current_user

router = APIRouter(prefix="/saved", tags=["Saved Items"])


class SavedItemCreate(BaseModel):
    content_type: str  # post, clip, sermon, prayer, event, song
    content_id: str
    title: Optional[str] = None
    thumbnail_url: Optional[str] = None
    subtitle: Optional[str] = None


class SavedItemResponse(BaseModel):
    id: int
    content_type: str
    content_id: str
    title: Optional[str] = None
    thumbnail_url: Optional[str] = None
    subtitle: Optional[str] = None
    saved_at: datetime

    class Config:
        from_attributes = True


@router.get("", response_model=List[SavedItemResponse])
async def list_saved_items(
    content_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all saved/bookmarked items for the current user."""
    query = select(SavedItem).where(SavedItem.user_id == current_user.id)
    if content_type:
        query = query.where(SavedItem.content_type == content_type)
    query = query.order_by(SavedItem.saved_at.desc())

    result = await db.execute(query)
    return result.scalars().all()


@router.post("", status_code=201)
async def save_item(
    data: SavedItemCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Save/bookmark an item. Duplicate saves are idempotent."""
    # Check if already saved
    existing = (await db.execute(
        select(SavedItem).where(
            SavedItem.user_id == current_user.id,
            SavedItem.content_type == data.content_type,
            SavedItem.content_id == data.content_id,
        )
    )).scalar_one_or_none()

    if existing:
        return {
            "id": existing.id,
            "content_type": existing.content_type,
            "content_id": existing.content_id,
            "message": "Already saved",
        }

    item = SavedItem(
        user_id=current_user.id,
        content_type=data.content_type,
        content_id=data.content_id,
        title=data.title,
        thumbnail_url=data.thumbnail_url,
        subtitle=data.subtitle,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)

    return {
        "id": item.id,
        "content_type": item.content_type,
        "content_id": item.content_id,
        "saved_at": item.saved_at.isoformat(),
        "message": "Item saved",
    }


@router.delete("/{item_id}")
async def unsave_item(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove a saved/bookmarked item."""
    item = (await db.execute(
        select(SavedItem).where(
            SavedItem.id == item_id,
            SavedItem.user_id == current_user.id,
        )
    )).scalar_one_or_none()

    if not item:
        raise HTTPException(status_code=404, detail="Saved item not found")

    await db.delete(item)
    await db.commit()
    return {"message": "Item removed from saved"}
