"""Organization (tenant) model for multi-tenant support."""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, ForeignKey, Enum
from sqlalchemy.sql import func
from app.database import Base
import enum


def enum_values(enum_type):
    return [e.value for e in enum_type]


class OrgMemberRole(str, enum.Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"


class Organization(Base):
    """A tenant — each organization is an isolated workspace with its own members and data."""

    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    settings = Column(JSON, default=dict, comment="Org-level settings (branding, defaults, etc.)")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class OrganizationMember(Base):
    """Links a user to an organization with a specific role."""

    __tablename__ = "organization_members"

    id = Column(Integer, primary_key=True, autoincrement=True)
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = Column(
        Enum(OrgMemberRole, values_callable=enum_values),
        default=OrgMemberRole.MEMBER,
        nullable=False,
    )
    joined_at = Column(DateTime, server_default=func.now())
    created_at = Column(DateTime, server_default=func.now())
