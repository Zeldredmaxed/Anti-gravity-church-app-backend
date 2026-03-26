"""Admin router: user management, audit logs, church settings."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
import string
import secrets

from app.database import get_db
from app.models.user import User, AuditLog
from app.models.church import RegistrationKey
from app.schemas.user import UserResponse, UserRegister, UserRoleUpdate, AuditLogResponse
from app.utils.security import hash_password, get_current_user, require_role
from app.dependencies import PaginationParams
from app.config import settings

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/generate-master-key")
async def generate_master_key(db: AsyncSession = Depends(get_db)):
    """Generate a master registration key (temporary endpoint for production setup)."""
    chars = string.ascii_uppercase + string.digits
    part1 = ''.join(secrets.choice(chars) for _ in range(4))
    part2 = ''.join(secrets.choice(chars) for _ in range(4))
    key_str = f"NG-{part1}-{part2}"
    key = RegistrationKey(key_string=key_str)
    db.add(key)
    await db.commit()
    return {"success": True, "master_key": key_str}


@router.get("/users", response_model=list[UserResponse])
async def list_users(
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db)):
    return (await db.execute(select(User).order_by(User.full_name))).scalars().all()


@router.post("/users", response_model=UserResponse, status_code=201)
async def create_user(data: UserRegister,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db)):
    existing = (await db.execute(select(User).where(User.email == data.email))).scalar_one_or_none()
    if existing: raise HTTPException(status_code=400, detail="Email already registered")
    user = User(email=data.email, hashed_password=hash_password(data.password),
                full_name=data.full_name, role=data.role)
    db.add(user); await db.flush(); await db.refresh(user)
    return user


@router.put("/users/{user_id}/role", response_model=UserResponse)
async def update_user_role(user_id: int, data: UserRoleUpdate,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db)):
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if not user: raise HTTPException(status_code=404, detail="User not found")
    user.role = data.role; db.add(user)
    await db.flush(); await db.refresh(user)
    return user


@router.put("/users/{user_id}/deactivate", response_model=UserResponse)
async def deactivate_user(user_id: int,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db)):
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if not user: raise HTTPException(status_code=404, detail="User not found")
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot deactivate yourself")
    user.is_active = False; db.add(user)
    await db.flush(); await db.refresh(user)
    return user


@router.get("/audit-log", response_model=list[AuditLogResponse])
async def get_audit_log(
    action: Optional[str] = None, resource: Optional[str] = None,
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db)):
    query = select(AuditLog)
    if action: query = query.where(AuditLog.action == action)
    if resource: query = query.where(AuditLog.resource == resource)
    query = query.order_by(AuditLog.timestamp.desc()).offset(pagination.offset).limit(pagination.per_page)
    return (await db.execute(query)).scalars().all()


@router.get("/settings")
async def get_settings(current_user: User = Depends(require_role("admin", "pastor"))):
    return {
        "church_name": settings.CHURCH_NAME,
        "church_address": settings.CHURCH_ADDRESS,
        "church_phone": settings.CHURCH_PHONE,
        "church_email": settings.CHURCH_EMAIL,
        "church_website": settings.CHURCH_WEBSITE,
    }
