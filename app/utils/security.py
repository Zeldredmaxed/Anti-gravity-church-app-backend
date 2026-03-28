"""Security utilities: JWT tokens, password hashing, role enforcement, tenant isolation, fine-grained RBAC."""

from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Set
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import settings
from app.database import get_db

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


# ── Fine-Grained Permission System ──────────────────────────────────────────
# Maps roles to specific permissions. Checked via require_permission().
ROLE_PERMISSIONS: Dict[str, Set[str]] = {
    "admin": {
        "members:read", "members:write", "members:delete",
        "finance:read", "finance:write", "finance:export",
        "attendance:read", "attendance:write",
        "events:read", "events:write", "events:delete",
        "groups:read", "groups:write", "groups:delete",
        "volunteers:read", "volunteers:write", "volunteers:manage",
        "care:read", "care:write", "care:assign",
        "tasks:read", "tasks:write", "tasks:assign",
        "settings:read", "settings:write",
        "reports:read", "reports:export",
        "dashboard:read",
        "facilities:read", "facilities:write",
        "communications:send",
    },
    "pastor": {
        "members:read", "members:write",
        "finance:read", "finance:export",
        "attendance:read", "attendance:write",
        "events:read", "events:write",
        "groups:read", "groups:write",
        "volunteers:read", "volunteers:write", "volunteers:manage",
        "care:read", "care:write", "care:assign",
        "tasks:read", "tasks:write", "tasks:assign",
        "settings:read",
        "reports:read", "reports:export",
        "dashboard:read",
        "facilities:read", "facilities:write",
        "communications:send",
    },
    "staff": {
        "members:read", "members:write",
        "attendance:read", "attendance:write",
        "events:read", "events:write",
        "groups:read", "groups:write",
        "volunteers:read", "volunteers:write",
        "care:read", "care:write",
        "tasks:read", "tasks:write",
        "dashboard:read",
        "facilities:read",
        "reports:read",
    },
    "ministry_leader": {
        "members:read",
        "attendance:read", "attendance:write",
        "events:read",
        "groups:read", "groups:write",
        "volunteers:read",
        "care:read", "care:write",
        "tasks:read", "tasks:write",
        "dashboard:read",
    },
    "finance_team": {
        "finance:read", "finance:write", "finance:export",
        "members:read",
        "reports:read", "reports:export",
        "dashboard:read",
    },
    "volunteer": {
        "members:read",
        "events:read",
        "groups:read",
        "volunteers:read",
        "dashboard:read",
    },
    "member": {
        "events:read",
        "groups:read",
        "dashboard:read",
    },
}


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token. `data` should include `sub` (user_id) and `church_id`."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(data: dict) -> str:
    """Create JWT refresh token with church_id claim."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    """Dependency: extract current user + church_id from JWT."""
    from app.models.user import User

    payload = decode_token(token)
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    return user


def get_church_id(current_user=Depends(get_current_user)) -> int:
    """Dependency: extract church_id from authenticated user."""
    return current_user.church_id


def require_role(*allowed_roles: str):
    """Dependency factory: enforce role-based access control."""

    async def _check_role(current_user=Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of roles: {', '.join(allowed_roles)}",
            )
        return current_user

    return _check_role


def require_permission(*required_permissions: str):
    """Dependency factory: enforce fine-grained permission checks.

    Usage:
        @router.get("/finance", dependencies=[Depends(require_permission("finance:read"))])
    """

    async def _check_permission(current_user=Depends(get_current_user)):
        user_role = current_user.role or "member"
        user_perms = ROLE_PERMISSIONS.get(user_role, set())

        missing = [p for p in required_permissions if p not in user_perms]
        if missing:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing permissions: {', '.join(missing)}",
            )
        return current_user

    return _check_permission
