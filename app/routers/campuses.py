from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database import get_db
from app.models.user import User
from app.models.campus import Campus
from app.schemas.campus import CampusCreate, CampusUpdate, CampusResponse
from app.utils.security import get_current_user, require_role

router = APIRouter(prefix="/campuses", tags=["Campuses"])

@router.post("/", response_model=CampusResponse, status_code=status.HTTP_201_CREATED)
async def create_campus(
    campus: CampusCreate,
    current_user: User = Depends(require_role(["pastor", "admin"])),
    db: AsyncSession = Depends(get_db)
):
    # Ensure there is only one main campus per church
    if campus.is_main_campus:
        query = select(Campus).where(Campus.church_id == current_user.church_id, Campus.is_main_campus == True)
        result = await db.execute(query)
        existing_main = result.scalars().first()
        if existing_main:
            existing_main.is_main_campus = False
            db.add(existing_main)

    new_campus = Campus(**campus.model_dump(), church_id=current_user.church_id)
    db.add(new_campus)
    await db.commit()
    await db.refresh(new_campus)
    return new_campus

@router.get("/", response_model=List[CampusResponse])
async def list_campuses(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(Campus).where(Campus.church_id == current_user.church_id)
    result = await db.execute(query)
    return result.scalars().all()

@router.put("/{campus_id}", response_model=CampusResponse)
async def update_campus(
    campus_id: int,
    campus_update: CampusUpdate,
    current_user: User = Depends(require_role(["pastor", "admin"])),
    db: AsyncSession = Depends(get_db)
):
    query = select(Campus).where(Campus.id == campus_id, Campus.church_id == current_user.church_id)
    result = await db.execute(query)
    campus = result.scalars().first()
    
    if not campus:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campus not found")

    if campus_update.is_main_campus and not campus.is_main_campus:
        main_query = select(Campus).where(Campus.church_id == current_user.church_id, Campus.is_main_campus == True)
        main_res = await db.execute(main_query)
        existing_main = main_res.scalars().first()
        if existing_main:
            existing_main.is_main_campus = False
            db.add(existing_main)

    update_data = campus_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(campus, key, value)
        
    await db.commit()
    await db.refresh(campus)
    return campus
