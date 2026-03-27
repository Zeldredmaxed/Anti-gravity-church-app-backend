"""Auth router: registration, login, token refresh, profile — multi-tenant."""

from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.database import get_db
from app.models.user import User, AuditLog, UserRole
from app.models.login_streak import UserLoginDay, UserStreak
from app.schemas.user import (
    UserRegister, UserLogin, TokenResponse, TokenRefresh,
    UserResponse, UserUpdate, UserRoleUpdate,
)
from app.utils.security import (
    hash_password, verify_password, create_access_token,
    create_refresh_token, decode_token, get_current_user, require_role,
)
from app.schemas.user import JoinChurchRequest

router = APIRouter(prefix="/auth", tags=["Authentication"])


async def _track_login(db: AsyncSession, user_id: int):
    """Record today's login and update the streak."""
    today = date.today()

    # Upsert the daily record (skip if already logged in today)
    existing_day = (await db.execute(select(UserLoginDay).where(
        UserLoginDay.user_id == user_id, UserLoginDay.login_date == today
    ))).scalar_one_or_none()
    if existing_day:
        return  # Already counted for today

    try:
        async with db.begin_nested():
            db.add(UserLoginDay(user_id=user_id, login_date=today))
    except IntegrityError:
        return  # Race condition matched, another request inserted first

    # Update streak record
    streak = (await db.execute(select(UserStreak).where(
        UserStreak.user_id == user_id
    ))).scalar_one_or_none()

    if not streak:
        db.add(UserStreak(
            user_id=user_id, current_streak=1, longest_streak=1,
            total_logins=1, last_login_date=today,
        ))
    else:
        streak.total_logins += 1
        yesterday = today - timedelta(days=1)
        if streak.last_login_date == yesterday:
            streak.current_streak += 1
        elif streak.last_login_date != today:
            streak.current_streak = 1  # Streak broken
        if streak.current_streak > streak.longest_streak:
            streak.longest_streak = streak.current_streak
        streak.last_login_date = today
        db.add(streak)

    await db.flush()


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(
    data: UserRegister,
    db: AsyncSession = Depends(get_db),
):
    """Register a new user.
    Allows passing an optional church_id to join upon registration.
    """
    result = await db.execute(select(User).where(User.email == data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    if data.username:
        result_username = await db.execute(select(User).where(User.username == data.username))
        if result_username.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Username already taken")

    user = User(
        church_id=data.church_id,
        email=data.email,
        username=data.username,
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
        date_of_birth=data.date_of_birth,
        role=data.role,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


@router.post("/leave-church")
async def leave_church(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Sign out of current church but remain logged in."""
    if current_user.church_id is None:
        raise HTTPException(status_code=400, detail="Not actively in a church")

    current_user.church_id = None
    db.add(current_user)
    await db.flush()

    token_data = {"sub": str(current_user.id), "church_id": None, "role": current_user.role}
    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
    )


@router.post("/join-church")
async def join_church(
    data: JoinChurchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Join a specific church from the directory."""
    # Note: In a real environment, you might enforce they can only join if church_id is None,
    # or you might allow them to switch. For this SaaS, they can switch directly.
    current_user.church_id = data.church_id
    db.add(current_user)
    await db.flush()

    token_data = {"sub": str(current_user.id), "church_id": current_user.church_id, "role": current_user.role}
    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    data: UserLogin,
    db: AsyncSession = Depends(get_db),
):
    """Authenticate and receive JWT tokens with church_id claim."""
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    audit = AuditLog(
        church_id=user.church_id,
        user_id=user.id,
        action="LOGIN",
        resource="auth",
        details=f"User {user.email} logged in",
    )
    db.add(audit)

    # Track login streak
    await _track_login(db, user.id)

    token_data = {"sub": str(user.id), "church_id": user.church_id, "role": user.role}
    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    data: TokenRefresh,
    db: AsyncSession = Depends(get_db),
):
    payload = decode_token(data.refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Invalid user")

    token_data = {"sub": str(user.id), "church_id": user.church_id, "role": user.role}
    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
    )


@router.get("/me", response_model=UserResponse)
async def get_profile(current_user: User = Depends(get_current_user)):
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_profile(
    data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if data.full_name is not None:
        current_user.full_name = data.full_name
    if data.email is not None:
        result = await db.execute(
            select(User).where(User.email == data.email, User.id != current_user.id)
        )
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Email already in use")
        current_user.email = data.email
    if data.username is not None:
        result = await db.execute(
            select(User).where(User.username == data.username, User.id != current_user.id)
        )
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Username already taken")
        current_user.username = data.username
    if data.date_of_birth is not None:
        current_user.date_of_birth = data.date_of_birth

    if data.testimony_summary is not None:
        current_user.testimony_summary = data.testimony_summary
    if data.website is not None:
        current_user.website = data.website
    if data.avatar_url is not None:
        current_user.avatar_url = data.avatar_url

    db.add(current_user)
    await db.flush()
    await db.refresh(current_user)
    return current_user


from pydantic import BaseModel

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Allow a user to update their password securely."""
    if not verify_password(data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password"
        )
    
    current_user.hashed_password = hash_password(data.new_password)
    db.add(current_user)
    await db.commit()


@router.get("/streak")
async def get_my_streak(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return the authenticated user's login streak stats."""
    await _track_login(db, current_user.id)
    
    streak = (await db.execute(select(UserStreak).where(
        UserStreak.user_id == current_user.id
    ))).scalar_one_or_none()

    if not streak:
        return {"data": {
            "current_streak": 0, "longest_streak": 0,
            "total_logins": 0, "last_login_date": None,
        }}
    return {"data": {
        "current_streak": streak.current_streak,
        "longest_streak": streak.longest_streak,
        "total_logins": streak.total_logins,
        "last_login_date": streak.last_login_date.isoformat() if streak.last_login_date else None,
    }}
