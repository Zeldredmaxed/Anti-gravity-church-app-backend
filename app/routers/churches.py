"""Church onboarding and management router."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from app.database import get_db
from datetime import datetime, timezone
from app.models.church import Church, RegistrationKey
from app.models.user import User
from app.schemas.church import ChurchCreate, ChurchUpdate, ChurchResponse, ChurchOnboardRequest, ChurchPublicResponse
from app.utils.security import (
    hash_password, create_access_token, create_refresh_token,
    get_current_user, require_role, get_church_id,
)

router = APIRouter(prefix="/churches", tags=["Churches (Multi-Tenant)"])


@router.post("/onboard", status_code=201)
async def onboard_church(data: ChurchOnboardRequest, db: AsyncSession = Depends(get_db)):
    """Register a new church + its first admin user. Public endpoint for onboarding."""
    # Validate registration key
    key_record = (await db.execute(
        select(RegistrationKey).where(RegistrationKey.key_string == data.registration_key)
    )).scalar_one_or_none()
    
    if not key_record or key_record.is_used:
        raise HTTPException(status_code=400, detail="Invalid or already used registration key")

    # Check subdomain uniqueness
    existing = (await db.execute(
        select(Church).where(Church.subdomain == data.church.subdomain)
    )).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Subdomain already taken")

    # Check email uniqueness
    existing_user = (await db.execute(
        select(User).where(User.email == data.admin_email)
    )).scalar_one_or_none()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    church = Church(**data.church.model_dump())
    db.add(church)
    await db.commit()
    await db.refresh(church)

    # Consume the registration key
    key_record.is_used = True
    key_record.church_id = church.id
    key_record.used_at = datetime.now(timezone.utc)
    db.add(key_record)

    # Create admin user
    admin = User(
        church_id=church.id,
        email=data.admin_email,
        hashed_password=hash_password(data.admin_password),
        full_name=data.admin_name,
        role="admin",
    )
    db.add(admin)
    await db.commit()
    await db.refresh(admin)

    # Issue tokens
    token_data = {"sub": str(admin.id), "church_id": church.id, "role": admin.role}
    return {
        "church": ChurchResponse.model_validate(church),
        "user_id": admin.id,
        "access_token": create_access_token(token_data),
        "refresh_token": create_refresh_token(token_data),
        "token_type": "bearer",
    }


@router.get("/me", response_model=ChurchResponse)
async def get_my_church(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)):
    church = (await db.execute(
        select(Church).where(Church.id == current_user.church_id)
    )).scalar_one_or_none()
    if not church:
        raise HTTPException(status_code=404, detail="Church not found")
    return church


@router.put("/me", response_model=ChurchResponse)
async def update_my_church(
    data: ChurchUpdate,
    current_user: User = Depends(require_role("admin", "pastor")),
    db: AsyncSession = Depends(get_db)):
    church = (await db.execute(
        select(Church).where(Church.id == current_user.church_id)
    )).scalar_one_or_none()
    if not church:
        raise HTTPException(status_code=404, detail="Church not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(church, field, value)
    db.add(church)
    await db.commit()
    await db.refresh(church)
    return church


@router.get("", response_model=list[ChurchPublicResponse])
@router.get("/", response_model=list[ChurchPublicResponse], include_in_schema=False)
async def list_churches(q: str | None = None, search: str | None = None, db: AsyncSession = Depends(get_db)):
    """Public: list or search active churches (for discovery/directory/member signup)."""
    search_term = q or search  # Accept both ?q= and ?search=
    query = select(Church).where(Church.is_active == True)
    if search_term:
        query = query.where(
            or_(
                Church.name.ilike(f"%{search_term}%"),
                Church.subdomain.ilike(f"%{search_term}%")
            )
        )
    query = query.order_by(Church.name).limit(50)
    
    churches = (await db.execute(query)).scalars().all()
    return churches


@router.get("/{church_id}")
async def get_church_by_id(church_id: int, db: AsyncSession = Depends(get_db)):
    """Public: get a church by its ID."""
    church = (await db.execute(
        select(Church).where(Church.id == church_id)
    )).scalar_one_or_none()
    if not church:
        raise HTTPException(status_code=404, detail="Church not found")
    return {
        "data": {
            "id": church.id,
            "name": church.name,
            "subdomain": church.subdomain,
            "description": getattr(church, "description", None),
            "address": getattr(church, "address", None),
            "phone_number": getattr(church, "phone_number", None),
            "website": getattr(church, "website", None),
            "logo_url": getattr(church, "logo_url", None),
            "cover_image_url": getattr(church, "cover_image_url", None),
            "timezone": getattr(church, "timezone", None),
            "is_active": church.is_active,
        }
    }


@router.get("/about")
async def get_church_about(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)):
    """Get public about info for the current church."""
    church = (await db.execute(
        select(Church).where(Church.id == current_user.church_id)
    )).scalar_one_or_none()
    if not church:
        raise HTTPException(status_code=404, detail="Church not found")
    return {"data": {
        "id": church.id,
        "name": church.name,
        "subdomain": church.subdomain,
        "description": getattr(church, "description", None),
        "address": getattr(church, "address", None),
        "phone": getattr(church, "phone", None),
        "email": getattr(church, "email", None),
        "website": getattr(church, "website", None),
        "logo_url": getattr(church, "logo_url", None),
        "cover_url": getattr(church, "cover_url", None),
        "service_times": getattr(church, "service_times", None),
        "social_links": getattr(church, "social_links", None),
    }}


@router.put("/settings")
async def update_church_settings(
    data: dict,
    current_user: User = Depends(require_role("admin", "pastor")),
    db: AsyncSession = Depends(get_db)):
    """Update church feature toggles and settings."""
    church = (await db.execute(
        select(Church).where(Church.id == current_user.church_id)
    )).scalar_one_or_none()
    if not church:
        raise HTTPException(status_code=404, detail="Church not found")

    # Apply any matching fields
    allowed = {"name", "description", "address", "phone", "email", "website",
               "logo_url", "cover_url", "service_times", "social_links",
               "features_enabled", "theme_color", "latitude", "longitude"}
    for key, value in data.items():
        if key in allowed:
            setattr(church, key, value)

    db.add(church)
    await db.commit()
    await db.refresh(church)
    return {"data": {"message": "Settings updated"}}

