"""Settings router — user preferences and privacy settings."""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional

from app.database import get_db
from app.models.user import User
from app.models.settings import UserSettings
from app.utils.security import get_current_user

router = APIRouter(prefix="/settings", tags=["Settings"])


class SettingsUpdate(BaseModel):
    is_private_account: Optional[bool] = None
    allow_tags_from: Optional[str] = None
    allow_mentions: Optional[bool] = None
    allow_comments_from: Optional[str] = None
    hide_offensive_comments: Optional[bool] = None
    hide_spam_comments: Optional[bool] = None
    allow_sharing_to_messages: Optional[bool] = None
    allow_resharing_to_stories: Optional[bool] = None
    limit_interactions: Optional[bool] = None
    hide_offensive_words: Optional[bool] = None
    show_suggested_posts: Optional[bool] = None
    hide_like_counts: Optional[bool] = None
    hide_share_counts: Optional[bool] = None
    data_saver: Optional[bool] = None
    autoplay_wifi: Optional[bool] = None
    autoplay_cellular: Optional[bool] = None
    high_quality_uploads: Optional[bool] = None
    save_original_photos: Optional[bool] = None
    save_posted_videos: Optional[bool] = None
    auto_captions: Optional[bool] = None
    larger_text: Optional[bool] = None
    reduce_motion: Optional[bool] = None
    auto_translate: Optional[bool] = None
    language: Optional[str] = None
    theme_mode: Optional[str] = None


def _settings_to_dict(s: UserSettings) -> dict:
    return {
        "id": s.id,
        "is_private_account": s.is_private_account,
        "allow_tags_from": s.allow_tags_from.value if s.allow_tags_from else "everyone",
        "allow_mentions": s.allow_mentions,
        "allow_comments_from": s.allow_comments_from.value if s.allow_comments_from else "everyone",
        "hide_offensive_comments": s.hide_offensive_comments,
        "hide_spam_comments": s.hide_spam_comments,
        "allow_sharing_to_messages": s.allow_sharing_to_messages,
        "allow_resharing_to_stories": s.allow_resharing_to_stories,
        "limit_interactions": s.limit_interactions,
        "hide_offensive_words": s.hide_offensive_words,
        "show_suggested_posts": s.show_suggested_posts,
        "hide_like_counts": s.hide_like_counts,
        "hide_share_counts": s.hide_share_counts,
        "data_saver": s.data_saver,
        "autoplay_wifi": s.autoplay_wifi,
        "autoplay_cellular": s.autoplay_cellular,
        "high_quality_uploads": s.high_quality_uploads,
        "save_original_photos": s.save_original_photos,
        "save_posted_videos": s.save_posted_videos,
        "auto_captions": s.auto_captions,
        "larger_text": s.larger_text,
        "reduce_motion": s.reduce_motion,
        "auto_translate": s.auto_translate,
        "language": s.language,
        "theme_mode": s.theme_mode.value if s.theme_mode else "system",
    }


@router.get("")
async def get_settings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the current user's settings. Auto-creates defaults if none exist."""
    member_id = current_user.member_id
    if not member_id:
        # Fallback: use user.id as member_id for users not yet linked
        member_id = current_user.id

    settings = (await db.execute(
        select(UserSettings).where(UserSettings.user_id == member_id)
    )).scalar_one_or_none()

    if not settings:
        # Auto-create default settings
        settings = UserSettings(user_id=member_id)
        db.add(settings)
        await db.commit()
        await db.refresh(settings)

    return {"data": _settings_to_dict(settings)}


@router.put("")
async def update_settings(
    data: SettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update the current user's settings."""
    member_id = current_user.member_id
    if not member_id:
        member_id = current_user.id

    settings = (await db.execute(
        select(UserSettings).where(UserSettings.user_id == member_id)
    )).scalar_one_or_none()

    if not settings:
        settings = UserSettings(user_id=member_id)
        db.add(settings)
        await db.commit()
        await db.refresh(settings)

    update_data = data.model_dump(exclude_unset=True)

    # Handle enum fields specially
    enum_fields = {"allow_tags_from", "allow_comments_from", "theme_mode"}
    for field, value in update_data.items():
        if field in enum_fields and isinstance(value, str):
            setattr(settings, field, value)
        else:
            setattr(settings, field, value)

    db.add(settings)
    await db.commit()
    await db.refresh(settings)

    return {"data": _settings_to_dict(settings)}
