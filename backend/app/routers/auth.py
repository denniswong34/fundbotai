"""Auth router — registration, login, token refresh, profile, and settings."""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import (
    get_current_user,
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.models.user import User, UserRole
from app.models.organization import Organization, OrganizationMember, OrgMemberRole
from app.models.user_settings import UserSettings
from app.i18n import t

router = APIRouter(prefix="/api/auth", tags=["auth"])


# ── Schemas ────────────────────────────────────────────


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)
    display_name: Optional[str] = None


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserSettingsUpdate(BaseModel):
    language: Optional[str] = None
    theme: Optional[str] = None
    timezone: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    telegram_enabled: Optional[bool] = None


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    display_name: Optional[str]
    role: str
    is_active: bool

    class Config:
        from_attributes = True


class UserSettingsResponse(BaseModel):
    language: str
    theme: str
    timezone: str
    telegram_chat_id: Optional[str]
    telegram_enabled: bool

    class Config:
        from_attributes = True


class OrgInfo(BaseModel):
    id: int
    name: str
    slug: str
    role: str

    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse
    organization: OrgInfo
    settings: UserSettingsResponse


class RegisterResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse
    organization: OrgInfo
    settings: UserSettingsResponse


# ── Helpers ────────────────────────────────────────────


async def _get_user_settings(db: AsyncSession, user_id: int) -> UserSettings:
    """Get or create user settings."""
    result = await db.execute(
        select(UserSettings).where(UserSettings.user_id == user_id)
    )
    settings = result.scalar_one_or_none()
    if settings is None:
        settings = UserSettings(user_id=user_id)
        db.add(settings)
        await db.commit()
        await db.refresh(settings)
    return settings


async def _get_user_org_info(db: AsyncSession, user_id: int) -> tuple[Organization, OrganizationMember]:
    """Get user's first organization and membership."""
    result = await db.execute(
        select(OrganizationMember).where(OrganizationMember.user_id == user_id)
    )
    membership = result.scalar_one_or_none()
    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User has no organization",
        )
    org_result = await db.execute(
        select(Organization).where(Organization.id == membership.org_id)
    )
    org = org_result.scalar_one_or_none()
    if org is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization not found",
        )
    return org, membership


# ── Endpoints ──────────────────────────────────────────


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Register a new user, auto-create an organization with slug from username."""
    # Check existing user
    result = await db.execute(
        select(User).where(
            (User.username == req.username) | (User.email == req.email)
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=t("error.already_exists", "en"),
        )

    # Create user
    user = User(
        username=req.username,
        email=req.email,
        password_hash=hash_password(req.password),
        display_name=req.display_name or req.username,
        role=UserRole.USER,
        is_active=True,
    )
    db.add(user)
    await db.flush()

    # Create user settings
    settings = UserSettings(user_id=user.id)
    db.add(settings)

    # Create organization with slug from username
    org = Organization(
        name=f"{req.username}'s Organization",
        slug=req.username.lower().replace(" ", "-"),
        settings={},
        is_active=True,
    )
    db.add(org)
    await db.flush()

    # Add user as owner
    member = OrganizationMember(
        org_id=org.id,
        user_id=user.id,
        role=OrgMemberRole.OWNER,
    )
    db.add(member)

    await db.commit()
    await db.refresh(user)
    await db.refresh(settings)
    await db.refresh(org)

    # Generate tokens
    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id), "type": "refresh"})

    return RegisterResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user),
        organization=OrgInfo(id=org.id, name=org.name, slug=org.slug, role="owner"),
        settings=UserSettingsResponse.model_validate(settings),
    )


@router.post("/login", response_model=LoginResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate a user and return tokens with org/settings info."""
    result = await db.execute(
        select(User).where(User.username == req.username)
    )
    user = result.scalar_one_or_none()

    if user is None or not verify_password(req.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=t("auth.login_failed", "en"),
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is disabled",
        )

    # Update last login
    user.last_login = datetime.now(timezone.utc)

    # Get settings
    settings = await _get_user_settings(db, user.id)

    # Get org info
    org, membership = await _get_user_org_info(db, user.id)

    await db.commit()

    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id), "type": "refresh"})

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user),
        organization=OrgInfo(id=org.id, name=org.name, slug=org.slug, role=membership.role.value),
        settings=UserSettingsResponse.model_validate(settings),
    )


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(req: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """Exchange a refresh token for a new access token."""
    token = req.refresh_token
    if not token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="refresh_token is required",
        )

    payload = decode_token(token)
    user_id = payload.get("sub")
    token_type = payload.get("type")

    if token_type != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    # Verify user still exists
    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    access_token = create_access_token({"sub": str(user.id)})
    new_refresh_token = create_refresh_token({"sub": str(user.id), "type": "refresh"})

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
    )


@router.get("/me")
async def get_me(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current user profile with org info and settings."""
    settings = await _get_user_settings(db, user.id)
    org, membership = await _get_user_org_info(db, user.id)

    return {
        "user": UserResponse.model_validate(user),
        "organization": OrgInfo(id=org.id, name=org.name, slug=org.slug, role=membership.role.value),
        "settings": UserSettingsResponse.model_validate(settings),
    }


@router.put("/settings", response_model=UserSettingsResponse)
async def update_settings(
    req: UserSettingsUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update current user's settings (language, theme, timezone, telegram)."""
    settings = await _get_user_settings(db, user.id)

    if req.language is not None:
        settings.language = req.language
    if req.theme is not None:
        settings.theme = req.theme
    if req.timezone is not None:
        settings.timezone = req.timezone
    if req.telegram_chat_id is not None:
        settings.telegram_chat_id = req.telegram_chat_id
    if req.telegram_enabled is not None:
        settings.telegram_enabled = req.telegram_enabled

    await db.commit()
    await db.refresh(settings)

    return UserSettingsResponse.model_validate(settings)
