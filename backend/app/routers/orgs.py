"""Organizations router — manage orgs, members, and roles."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.organization import Organization, OrganizationMember, OrgMemberRole
from app.models.user_settings import UserSettings

router = APIRouter(prefix="/api/orgs", tags=["organizations"])


# ── Schemas ────────────────────────────────────────────


class OrgCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    slug: str = Field(..., min_length=1, max_length=100, pattern=r"^[a-z0-9\-]+$")


class OrgUpdate(BaseModel):
    name: Optional[str] = None
    settings: Optional[dict] = None


class OrgMemberResponse(BaseModel):
    id: int
    user_id: int
    org_id: int
    role: str
    username: Optional[str] = None
    email: Optional[str] = None
    joined_at: Optional[str] = None

    class Config:
        from_attributes = True


class OrgResponse(BaseModel):
    id: int
    name: str
    slug: str
    settings: Optional[dict]
    is_active: bool
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    member_count: int = 0

    class Config:
        from_attributes = True


class MemberInviteRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=50)
    role: str = Field(default="member", pattern=r"^(admin|member)$")


class MemberRoleUpdate(BaseModel):
    role: str = Field(..., pattern=r"^(owner|admin|member)$")


# ── Helpers ────────────────────────────────────────────


def _role_enum(value: str) -> OrgMemberRole:
    mapping = {
        "owner": OrgMemberRole.OWNER,
        "admin": OrgMemberRole.ADMIN,
        "member": OrgMemberRole.MEMBER,
    }
    return mapping[value]


async def _get_org_and_check_permission(
    org_id: int,
    user: User,
    db: AsyncSession,
    required_roles: Optional[list[OrgMemberRole]] = None,
) -> tuple[Organization, OrganizationMember]:
    """Get an org and verify the user is a member with required role."""
    result = await db.execute(
        select(Organization).where(Organization.id == org_id)
    )
    org = result.scalar_one_or_none()
    if org is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )

    result = await db.execute(
        select(OrganizationMember).where(
            OrganizationMember.org_id == org_id,
            OrganizationMember.user_id == user.id,
        )
    )
    membership = result.scalar_one_or_none()
    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this organization",
        )

    if required_roles and membership.role not in required_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have the required role for this action",
        )

    return org, membership


# ── Endpoints ──────────────────────────────────────────


@router.get("")
async def list_orgs(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all organizations the current user belongs to."""
    result = await db.execute(
        select(OrganizationMember).where(OrganizationMember.user_id == user.id)
    )
    memberships = result.scalars().all()

    orgs = []
    for m in memberships:
        org_result = await db.execute(
            select(Organization).where(Organization.id == m.org_id)
        )
        org = org_result.scalar_one()
        # Count members
        count_result = await db.execute(
            select(OrganizationMember).where(OrganizationMember.org_id == org.id)
        )
        member_count = len(count_result.scalars().all())
        orgs.append(OrgResponse(
            id=org.id,
            name=org.name,
            slug=org.slug,
            settings=org.settings,
            is_active=org.is_active,
            created_at=str(org.created_at) if org.created_at else None,
            updated_at=str(org.updated_at) if org.updated_at else None,
            member_count=member_count,
        ))

    return orgs


@router.get("/{org_id}", response_model=OrgResponse)
async def get_org(
    org_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get organization details."""
    org, membership = await _get_org_and_check_permission(org_id, user, db)

    # Count members
    count_result = await db.execute(
        select(OrganizationMember).where(OrganizationMember.org_id == org.id)
    )
    member_count = len(count_result.scalars().all())

    return OrgResponse(
        id=org.id,
        name=org.name,
        slug=org.slug,
        settings=org.settings,
        is_active=org.is_active,
        created_at=str(org.created_at) if org.created_at else None,
        updated_at=str(org.updated_at) if org.updated_at else None,
        member_count=member_count,
    )


@router.put("/{org_id}", response_model=OrgResponse)
async def update_org(
    org_id: int,
    req: OrgUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update organization name or settings."""
    org, membership = await _get_org_and_check_permission(
        org_id, user, db,
        required_roles=[OrgMemberRole.OWNER, OrgMemberRole.ADMIN],
    )

    if req.name is not None:
        org.name = req.name
    if req.settings is not None:
        org.settings = req.settings

    await db.commit()
    await db.refresh(org)

    # Count members
    count_result = await db.execute(
        select(OrganizationMember).where(OrganizationMember.org_id == org.id)
    )
    member_count = len(count_result.scalars().all())

    return OrgResponse(
        id=org.id,
        name=org.name,
        slug=org.slug,
        settings=org.settings,
        is_active=org.is_active,
        created_at=str(org.created_at) if org.created_at else None,
        updated_at=str(org.updated_at) if org.updated_at else None,
        member_count=member_count,
    )


@router.get("/{org_id}/members", response_model=list[OrgMemberResponse])
async def list_members(
    org_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all members of an organization."""
    org, membership = await _get_org_and_check_permission(org_id, user, db)

    result = await db.execute(
        select(OrganizationMember).where(OrganizationMember.org_id == org_id)
    )
    members = result.scalars().all()

    responses = []
    for m in members:
        user_result = await db.execute(
            select(User).where(User.id == m.user_id)
        )
        u = user_result.scalar_one_or_none()
        responses.append(OrgMemberResponse(
            id=m.id,
            user_id=m.user_id,
            org_id=m.org_id,
            role=m.role.value,
            username=u.username if u else None,
            email=u.email if u else None,
            joined_at=str(m.joined_at) if m.joined_at else None,
        ))

    return responses


@router.post("/{org_id}/members", status_code=status.HTTP_201_CREATED)
async def invite_member(
    org_id: int,
    req: MemberInviteRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add a user to the organization (owner/admin only)."""
    org, membership = await _get_org_and_check_permission(
        org_id, user, db,
        required_roles=[OrgMemberRole.OWNER, OrgMemberRole.ADMIN],
    )

    # Find user to invite
    result = await db.execute(
        select(User).where(User.username == req.username)
    )
    invited_user = result.scalar_one_or_none()
    if invited_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{req.username}' not found",
        )

    # Check if already a member
    result = await db.execute(
        select(OrganizationMember).where(
            OrganizationMember.org_id == org_id,
            OrganizationMember.user_id == invited_user.id,
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User is already a member of this organization",
        )

    new_member = OrganizationMember(
        org_id=org_id,
        user_id=invited_user.id,
        role=_role_enum(req.role),
    )
    db.add(new_member)
    await db.commit()
    await db.refresh(new_member)

    return {
        "detail": "Member added successfully",
        "member": OrgMemberResponse(
            id=new_member.id,
            user_id=new_member.user_id,
            org_id=new_member.org_id,
            role=new_member.role.value,
            username=invited_user.username,
            email=invited_user.email,
            joined_at=str(new_member.joined_at) if new_member.joined_at else None,
        ),
    }


@router.put("/{org_id}/members/{target_user_id}")
async def update_member_role(
    org_id: int,
    target_user_id: int,
    req: MemberRoleUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a member's role in the organization."""
    org, membership = await _get_org_and_check_permission(
        org_id, user, db,
        required_roles=[OrgMemberRole.OWNER, OrgMemberRole.ADMIN],
    )

    result = await db.execute(
        select(OrganizationMember).where(
            OrganizationMember.org_id == org_id,
            OrganizationMember.user_id == target_user_id,
        )
    )
    target_member = result.scalar_one_or_none()
    if target_member is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found in this organization",
        )

    # Only owner can assign owner role
    if req.role == "owner" and membership.role != OrgMemberRole.OWNER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the organization owner can assign the owner role",
        )

    # Admin cannot change the owner's role
    if target_member.role == OrgMemberRole.OWNER and membership.role != OrgMemberRole.OWNER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot change the owner's role",
        )

    target_member.role = _role_enum(req.role)
    await db.commit()
    await db.refresh(target_member)

    return {
        "detail": "Member role updated",
        "member": OrgMemberResponse(
            id=target_member.id,
            user_id=target_member.user_id,
            org_id=target_member.org_id,
            role=target_member.role.value,
            joined_at=str(target_member.joined_at) if target_member.joined_at else None,
        ),
    }


@router.delete("/{org_id}/members/{target_user_id}")
async def remove_member(
    org_id: int,
    target_user_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove a member from the organization."""
    org, membership = await _get_org_and_check_permission(
        org_id, user, db,
        required_roles=[OrgMemberRole.OWNER, OrgMemberRole.ADMIN],
    )

    result = await db.execute(
        select(OrganizationMember).where(
            OrganizationMember.org_id == org_id,
            OrganizationMember.user_id == target_user_id,
        )
    )
    target_member = result.scalar_one_or_none()
    if target_member is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found in this organization",
        )

    # Cannot remove the owner
    if target_member.role == OrgMemberRole.OWNER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot remove the organization owner",
        )

    # Admin cannot remove other admins unless they're the owner
    if (target_member.role == OrgMemberRole.ADMIN
            and membership.role != OrgMemberRole.OWNER):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the owner can remove admins",
        )

    await db.delete(target_member)
    await db.commit()

    return {"detail": "Member removed successfully"}
