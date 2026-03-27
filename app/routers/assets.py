from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_
from typing import Optional
from app.database import get_db
from app.models.asset import Asset
from app.models.user import User
from app.schemas.asset import (
    AssetCreate, AssetUpdate, AssetResponse, AssetListResponse
)
from app.utils.security import get_current_user, require_role, get_church_id
from app.dependencies import PaginationParams

router = APIRouter(prefix="/assets", tags=["Assets"])


@router.get("", response_model=AssetListResponse)
async def list_assets(
    search: Optional[str] = Query(None, description="Search by name or serial number"),
    category: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(require_role("admin", "pastor", "staff", "finance_team", "ministry_leader")),
    db: AsyncSession = Depends(get_db),
):
    """List assets."""
    query = select(Asset).where(Asset.church_id == current_user.church_id)

    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                Asset.name.ilike(search_term),
                Asset.serial_number.ilike(search_term)
            )
        )
    if category:
        query = query.where(Asset.category == category)
    if status:
        query = query.where(Asset.status == status)

    total_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(total_query)

    query = query.offset(pagination.skip).limit(pagination.limit).order_by(Asset.name.asc())
    result = await db.execute(query)
    assets = result.scalars().all()

    return {
        "data": assets,
        "total": total,
        "page": pagination.page,
        "size": pagination.size
    }


@router.post("", response_model=AssetResponse)
async def create_asset(
    asset_in: AssetCreate,
    current_user: User = Depends(require_role("admin", "pastor", "staff", "finance_team")),
    db: AsyncSession = Depends(get_db),
):
    """Create a new asset."""
    asset = Asset(**asset_in.model_dump(), church_id=current_user.church_id)
    db.add(asset)
    await db.commit()
    await db.refresh(asset)
    return asset


@router.get("/{asset_id}", response_model=AssetResponse)
async def get_asset(
    asset_id: int,
    current_user: User = Depends(require_role("admin", "pastor", "staff", "finance_team", "ministry_leader")),
    db: AsyncSession = Depends(get_db),
):
    """Get specific asset."""
    result = await db.execute(
        select(Asset).where(
            Asset.id == asset_id,
            Asset.church_id == current_user.church_id
        )
    )
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset


@router.put("/{asset_id}", response_model=AssetResponse)
async def update_asset(
    asset_id: int,
    asset_in: AssetUpdate,
    current_user: User = Depends(require_role("admin", "pastor", "staff", "finance_team")),
    db: AsyncSession = Depends(get_db),
):
    """Update an asset."""
    result = await db.execute(
        select(Asset).where(
            Asset.id == asset_id,
            Asset.church_id == current_user.church_id
        )
    )
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    update_data = asset_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(asset, key, value)

    await db.commit()
    await db.refresh(asset)
    return asset


@router.delete("/{asset_id}", status_code=204)
async def delete_asset(
    asset_id: int,
    current_user: User = Depends(require_role("admin", "pastor", "finance_team")),
    db: AsyncSession = Depends(get_db),
):
    """Delete an asset."""
    result = await db.execute(
        select(Asset).where(
            Asset.id == asset_id,
            Asset.church_id == current_user.church_id
        )
    )
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    await db.delete(asset)
    await db.commit()
