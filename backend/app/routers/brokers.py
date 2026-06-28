"""Broker connections API router — CRUD, test connection, list types."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, get_current_org
from app.models.user import User
from app.models.organization import Organization
from app.models.broker_connection import BrokerConnection, MarketType
from app.schemas.broker import (
    BrokerConnectionCreate,
    BrokerConnectionUpdate,
    BrokerConnectionResponse,
    BrokerTypeResponse,
)
from app.services.broker_service import (
    get_broker_types,
    get_broker_type,
    test_connection as test_broker_connection,
    resolve_adapter,
)

router = APIRouter(prefix="/api/brokers", tags=["brokers"])


# ── Broker Types ────────────────────────────────────────────


@router.get("/types", response_model=list[BrokerTypeResponse])
async def list_broker_types():
    """List all available broker types from the registry."""
    return get_broker_types()


# ── Broker Connections CRUD ─────────────────────────────────


@router.get("", response_model=list[BrokerConnectionResponse])
async def list_connections(
    user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """List all broker connections for the current organization."""
    result = await db.execute(
        select(BrokerConnection).where(
            BrokerConnection.org_id == org.id
        ).order_by(BrokerConnection.created_at.desc())
    )
    return list(result.scalars().all())


@router.post("", response_model=BrokerConnectionResponse, status_code=status.HTTP_201_CREATED)
async def create_connection(
    data: BrokerConnectionCreate,
    user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """Create a new broker connection."""
    # Validate broker type exists
    broker_type_def = get_broker_type(data.broker_type)
    if broker_type_def is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown broker type: {data.broker_type}",
        )

    connection = BrokerConnection(
        user_id=user.id,
        org_id=org.id,
        name=data.name,
        broker_type=data.broker_type,
        market_type=MarketType(data.market_type) if data.market_type else MarketType.STOCKS,
        config_json=data.config_json or {},
        sub_account_id=data.sub_account_id,
        is_active=True,
    )
    db.add(connection)
    await db.commit()
    await db.refresh(connection)
    return connection


@router.get("/{connection_id}", response_model=BrokerConnectionResponse)
async def get_connection(
    connection_id: int,
    user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """Get a single broker connection."""
    connection = await _get_connection(db, org.id, connection_id)
    return connection


@router.put("/{connection_id}", response_model=BrokerConnectionResponse)
async def update_connection(
    connection_id: int,
    data: BrokerConnectionUpdate,
    user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """Update a broker connection."""
    connection = await _get_connection(db, org.id, connection_id)

    if data.name is not None:
        connection.name = data.name
    if data.market_type is not None:
        connection.market_type = MarketType(data.market_type)
    if data.config_json is not None:
        connection.config_json = data.config_json
    if data.sub_account_id is not None:
        connection.sub_account_id = data.sub_account_id
    if data.is_active is not None:
        connection.is_active = data.is_active

    await db.commit()
    await db.refresh(connection)
    return connection


@router.delete("/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_connection(
    connection_id: int,
    user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """Delete a broker connection."""
    connection = await _get_connection(db, org.id, connection_id)
    await db.delete(connection)
    await db.commit()


@router.post("/{connection_id}/test")
async def test_connection(
    connection_id: int,
    user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """Test a broker connection."""
    connection = await _get_connection(db, org.id, connection_id)
    result = await test_broker_connection(connection)

    # Update connection status
    connection.is_connected = result
    if result:
        from datetime import datetime, timezone
        connection.last_connected_at = datetime.now(timezone.utc)
    await db.commit()

    return {
        "success": result,
        "message": "Connection successful" if result else "Connection failed",
    }


# ── Helpers ────────────────────────────────────────────────


async def _get_connection(db: AsyncSession, org_id: int, connection_id: int) -> BrokerConnection:
    """Get a broker connection scoped to an organization."""
    result = await db.execute(
        select(BrokerConnection).where(
            BrokerConnection.id == connection_id,
            BrokerConnection.org_id == org_id,
        )
    )
    connection = result.scalar_one_or_none()
    if connection is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Broker connection not found",
        )
    return connection
