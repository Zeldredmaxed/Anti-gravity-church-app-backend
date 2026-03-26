from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from app.database import get_db
from app.models.user import User
from app.models.social import FlockMember, Meditation, Report, ReportStatus
from app.schemas.social import (
    FlockMemberResponse, FlockListResponse, MeditationCreate, MeditationResponse, 
    ReportCreate, ReportResponse
)
from app.schemas.user import UserResponse
from app.utils.security import get_current_user

router = APIRouter(tags=["Social"])


# --- FLOCK MEMBERS ---

@router.post("/flock/{user_id}", response_model=FlockMemberResponse, status_code=status.HTTP_201_CREATED)
async def join_flock(user_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Join a user's flock."""
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="You cannot join your own flock.")
    
    # Check if user exists
    target_user = await db.get(User, user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
        
    # Check if already in flock
    existing = await db.execute(
        select(FlockMember).where(FlockMember.follower_id == current_user.id, FlockMember.followed_id == user_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Already in this user's flock")
        
    new_member = FlockMember(follower_id=current_user.id, followed_id=user_id)
    db.add(new_member)
    await db.commit()
    await db.refresh(new_member)
    return new_member


@router.delete("/flock/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def leave_flock(user_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Leave a user's flock."""
    result = await db.execute(
        select(FlockMember).where(FlockMember.follower_id == current_user.id, FlockMember.followed_id == user_id)
    )
    member_record = result.scalar_one_or_none()
    
    if not member_record:
        raise HTTPException(status_code=404, detail="Flock membership not found")
        
    await db.delete(member_record)
    await db.commit()


@router.get("/users/{user_id}/flock", response_model=List[FlockListResponse])
async def get_flock(user_id: int, db: AsyncSession = Depends(get_db)):
    """Get users in a specific user's flock."""
    result = await db.execute(
        select(FlockMember, User).join(User, FlockMember.follower_id == User.id).where(FlockMember.followed_id == user_id)
    )
    return [{"user": user, "created_at": member.created_at} for member, user in result.all()]


@router.get("/users/{user_id}/shepherding", response_model=List[FlockListResponse])
async def get_shepherding(user_id: int, db: AsyncSession = Depends(get_db)):
    """Get users a specific user is shepherding."""
    result = await db.execute(
        select(FlockMember, User).join(User, FlockMember.followed_id == User.id).where(FlockMember.follower_id == user_id)
    )
    return [{"user": user, "created_at": member.created_at} for member, user in result.all()]


# --- MEDITATIONS ---

@router.post("/meditations", response_model=MeditationResponse, status_code=status.HTTP_201_CREATED)
async def add_meditation(save_data: MeditationCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Add a post or glory clip to meditations."""
    # Check if already saved
    existing = await db.execute(
        select(Meditation).where(
            Meditation.user_id == current_user.id, 
            Meditation.entity_type == save_data.entity_type,
            Meditation.entity_id == save_data.entity_id
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Content already in meditations")
        
    new_save = Meditation(
        user_id=current_user.id,
        entity_type=save_data.entity_type,
        entity_id=save_data.entity_id
    )
    db.add(new_save)
    await db.commit()
    await db.refresh(new_save)
    return new_save


@router.delete("/meditations/{entity_type}/{entity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_meditation(entity_type: str, entity_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Remove a post or glory clip from meditations."""
    result = await db.execute(
        select(Meditation).where(
            Meditation.user_id == current_user.id, 
            Meditation.entity_type == entity_type,
            Meditation.entity_id == entity_id
        )
    )
    save_record = result.scalar_one_or_none()
    
    if not save_record:
        raise HTTPException(status_code=404, detail="Meditation not found")
        
    await db.delete(save_record)
    await db.commit()


@router.get("/meditations", response_model=List[MeditationResponse])
async def get_meditations(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """List all meditations for the logged-in user."""
    result = await db.execute(
        select(Meditation).where(Meditation.user_id == current_user.id).order_by(Meditation.created_at.desc())
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
