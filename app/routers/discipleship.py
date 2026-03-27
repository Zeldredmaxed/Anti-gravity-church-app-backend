from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database import get_db
from app.models.user import User
from app.models.discipleship import DiscipleshipStep, MemberDiscipleshipProgress
from app.models.member import Member
from app.schemas.discipleship import (
    DiscipleshipStepCreate, DiscipleshipStepUpdate, DiscipleshipStepResponse,
    MemberDiscipleshipProgressCreate, MemberDiscipleshipProgressUpdate, MemberDiscipleshipProgressResponse
)
from app.utils.security import get_current_user, require_role

router = APIRouter(prefix="/discipleship", tags=["Discipleship"])

@router.post("/steps", response_model=DiscipleshipStepResponse, status_code=status.HTTP_201_CREATED)
async def create_step(
    step: DiscipleshipStepCreate,
    current_user: User = Depends(require_role(["pastor", "admin", "ministry_leader"])),
    db: AsyncSession = Depends(get_db)
):
    new_step = DiscipleshipStep(**step.model_dump(), church_id=current_user.church_id)
    db.add(new_step)
    await db.commit()
    await db.refresh(new_step)
    return new_step


@router.get("/steps", response_model=List[DiscipleshipStepResponse])
async def list_steps(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(DiscipleshipStep).where(DiscipleshipStep.church_id == current_user.church_id).order_by(DiscipleshipStep.order_index.asc())
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/progress", response_model=MemberDiscipleshipProgressResponse, status_code=status.HTTP_201_CREATED)
async def record_progress(
    progress: MemberDiscipleshipProgressCreate,
    current_user: User = Depends(require_role(["pastor", "admin", "ministry_leader"])),
    db: AsyncSession = Depends(get_db)
):
    # Verify member and step belong to the user's church
    member_query = select(Member).where(Member.id == progress.member_id, Member.church_id == current_user.church_id)
    member_res = await db.execute(member_query)
    if not member_res.scalars().first():
        raise HTTPException(status_code=404, detail="Member not found in your church")

    step_query = select(DiscipleshipStep).where(DiscipleshipStep.id == progress.step_id, DiscipleshipStep.church_id == current_user.church_id)
    step_res = await db.execute(step_query)
    if not step_res.scalars().first():
        raise HTTPException(status_code=404, detail="Discipleship Step not found in your church")

    new_progress = MemberDiscipleshipProgress(**progress.model_dump())
    db.add(new_progress)
    await db.commit()
    await db.refresh(new_progress)
    return new_progress


@router.get("/progress/{member_id}", response_model=List[MemberDiscipleshipProgressResponse])
async def get_member_progress(
    member_id: int,
    current_user: User = Depends(require_role(["pastor", "admin", "ministry_leader", "staff"])),
    db: AsyncSession = Depends(get_db)
):
    # Verify member belongs to the church
    member_query = select(Member).where(Member.id == member_id, Member.church_id == current_user.church_id)
    member_res = await db.execute(member_query)
    if not member_res.scalars().first():
        raise HTTPException(status_code=404, detail="Member not found")

    query = select(MemberDiscipleshipProgress).where(
        MemberDiscipleshipProgress.member_id == member_id
    ).join(DiscipleshipStep)
    
    result = await db.execute(query)
    return result.scalars().all()
