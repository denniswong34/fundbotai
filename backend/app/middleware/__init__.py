"""Tenant middleware — resolves the current user's organization and attaches it to request.state.

Middleware flow:
1. Skip unauthenticated routes (health, auth endpoints)
2. Extract and validate JWT token
3. Look up the user's organization membership
4. Attach org_id and org to request.state
5. Provide helper dependency get_current_org
"""

import re
from typing import Optional

from fastapi import Request, HTTPException, status
from sqlalchemy import select
from starlette.middleware.base import BaseHTTPMiddleware

from app.database import AsyncSessionLocal
from app.dependencies import decode_token, verify_password  # noqa: F401
from app.models.user import User
from app.models.organization import Organization, OrganizationMember

# Routes that don't need tenant resolution
_PUBLIC_ROUTES = re.compile(
    r"^/api/(health|auth/(register|login|refresh))"
)


class TenantMiddleware(BaseHTTPMiddleware):
    """Middleware that resolves org context for authenticated requests."""

    async def dispatch(self, request: Request, call_next):
        # Skip public routes
        if _PUBLIC_ROUTES.match(request.url.path) or request.method == "OPTIONS":
            return await call_next(request)

        # Set defaults on state
        request.state.org_id = None
        request.state.org = None
        request.state.user_id = None

        # Try to extract user from token
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]
            try:
                payload = decode_token(token)
                user_id = payload.get("sub")
                if user_id:
                    request.state.user_id = int(user_id)

                    # Look up user's org
                    async with AsyncSessionLocal() as db:
                        result = await db.execute(
                            select(OrganizationMember).where(
                                OrganizationMember.user_id == int(user_id)
                            )
                        )
                        memberships = result.scalars().all()

                        if memberships:
                            # Check for X-Org-ID header (admin override)
                            org_id = request.headers.get("X-Org-ID")
                            if org_id:
                                try:
                                    target_org_id = int(org_id)
                                    # Verify user is actually a member of this org
                                    for m in memberships:
                                        if m.org_id == target_org_id:
                                            request.state.org_id = target_org_id
                                            break
                                except (ValueError, TypeError):
                                    pass

                            if request.state.org_id is None:
                                request.state.org_id = memberships[0].org_id

                            # Load org
                            org_result = await db.execute(
                                select(Organization).where(
                                    Organization.id == request.state.org_id
                                )
                            )
                            org = org_result.scalar_one_or_none()
                            if org and org.is_active:
                                request.state.org = org
            except (HTTPException, Exception):
                # Token invalid — let the route handler decide if auth is needed
                pass

        return await call_next(request)


async def get_current_org_from_state(request: Request) -> Optional[Organization]:
    """Dependency that returns the org resolved by the middleware."""
    org = getattr(request.state, "org", None)
    if org is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No organization context available",
        )
    return org
