from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from app.database import get_db
from app.models.user import User
from app.models.social import Follower, SavedContent, Report, ReportStatus
from app.schemas.social import (
    FollowerResponse, FollowListResponse, SaveCreate, SaveResponse, 
    ReportCreate, ReportResponse
)
from app.schemas.user import UserResponse
from app.utils.security import get_current_user

router = APIRouter(tags=["Social"])


# --- FOLLOWERS ---

@router.post("/users/{user_id}/follow", response_model=FollowerResponse, status_code=status.HTTP_201_CREATED)
async def follow_user(user_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Follow another user."""
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="You cannot follow yourself.")
    
    # Check if user exists
    target_user = await db.get(User, user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
        
    # Check if already following
    existing = await db.execute(
        select(Follower).where(Follower.follower_id == current_user.id, Follower.followed_id == user_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Already following this user")
        
    new_follow = Follower(follower_id=current_user.id, followed_id=user_id)
    db.add(new_follow)
    await db.commit()
    await db.refresh(new_follow)
    return new_follow


@router.delete("/users/{user_id}/unfollow", status_code=status.HTTP_204_NO_CONTENT)
async def unfollow_user(user_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Unfollow a user."""
    result = await db.execute(
        select(Follower).where(Follower.follower_id == current_user.id, Follower.followed_id == user_id)
    )
    follow_record = result.scalar_one_or_none()
    
    if not follow_record:
        raise HTTPException(status_code=404, detail="Follow relationship not found")
        
    await db.delete(follow_record)
    await db.commit()


@router.get("/users/{user_id}/followers", response_model=List[FollowListResponse])
async def get_followers(user_id: int, db: AsyncSession = Depends(get_db)):
    """Get users following a specific user."""
    result = await db.execute(
        select(Follower, User).join(User, Follower.follower_id == User.id).where(Follower.followed_id == user_id)
    )
    return [{"user": user, "created_at": follow.created_at} for follow, user in result.all()]


@router.get("/users/{user_id}/following", response_model=List[FollowListResponse])
async def get_following(user_id: int, db: AsyncSession = Depends(get_db)):
    """Get users a specific user is following."""
    result = await db.execute(
        select(Follower, User).join(User, Follower.followed_id == User.id).where(Follower.follower_id == user_id)
    )
    return [{"user": user, "created_at": follow.created_at} for follow, user in result.all()]


# --- SAVED CONTENT ---

@router.post("/saves", response_model=SaveResponse, status_code=status.HTTP_201_CREATED)
async def save_content(save_data: SaveCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Save a post or short."""
    # Check if already saved
    existing = await db.execute(
        select(SavedContent).where(
            SavedContent.user_id == current_user.id, 
            SavedContent.entity_type == save_data.entity_type,
            SavedContent.entity_id == save_data.entity_id
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Content already saved")
        
    new_save = SavedContent(
        user_id=current_user.id,
        entity_type=save_data.entity_type,
        entity_id=save_data.entity_id
    )
    db.add(new_save)
    await db.commit()
    await db.refresh(new_save)
    return new_save


@router.delete("/saves/{entity_type}/{entity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unsave_content(entity_type: str, entity_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Remove a saved post or short."""
    result = await db.execute(
        select(SavedContent).where(
            SavedContent.user_id == current_user.id, 
            SavedContent.entity_type == entity_type,
            SavedContent.entity_id == entity_id
        )
    )
    save_record = result.scalar_one_or_none()
    
    if not save_record:
        raise HTTPException(status_code=404, detail="Saved content not found")
        
    await db.delete(save_record)
    await db.commit()


@router.get("/saves", response_model=List[SaveResponse])
async def get_saved_content(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """List all saved posts and shorts for the logged-in user."""
    result = await db.execute(
        select(SavedContent).where(SavedContent.user_id == current_user.id).order_by(SavedContent.created_at.desc())
    )
    return result.scalars().all()


# --- REPORTS ---

@router.post("/reports", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def report_content(report_data: ReportCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Report a post, short, comment, or user."""
    new_report = Report(
        reporter_id=current_user.id,
        entity_type=report_data.entity_type,
        entity_id=report_data.entity_id,
        reason=report_data.reason,
        status=ReportStatus.PENDING.value
    )
    db.add(new_report)
    await db.commit()
    await db.refresh(new_report)
    
    # Ideally trigger an admin email or notification here
    return new_report
