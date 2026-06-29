"""Portfolio management API router — CRUD, holdings, rebalance, sync, performance."""

from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, get_current_org
from app.models.user import User
from app.models.organization import Organization
from app.schemas.portfolio import (
    PortfolioCreate,
    PortfolioUpdate,
    PortfolioResponse,
    PortfolioSummary,
    PortfolioHoldingCreate,
    PortfolioHoldingUpdate,
    PortfolioHoldingResponse,
    RebalancePlan,
    RebalanceExecuteRequest,
    RebalanceOrderResponse,
    PerformanceData,
    AllocationData,
)
from app.services.portfolio_service import PortfolioManager, PortfolioNotFound, HoldingNotFound, InsufficientCapitalError

router = APIRouter(prefix="/api/portfolios", tags=["portfolios"])


def _get_pm(db: AsyncSession) -> PortfolioManager:
    return PortfolioManager(db)


# ── Portfolio CRUD ──────────────────────────────────────────


@router.get("", response_model=list[PortfolioResponse])
async def list_portfolios(
    user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """List all portfolios for the current organization."""
    pm = _get_pm(db)
    portfolios = await pm.get_portfolios(org.id, user.id)
    return portfolios


@router.post("", response_model=PortfolioResponse, status_code=status.HTTP_201_CREATED)
async def create_portfolio(
    data: PortfolioCreate,
    user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """Create a new portfolio."""
    pm = _get_pm(db)
    portfolio = await pm.create_portfolio(org.id, user.id, data.model_dump(exclude_unset=True))
    return portfolio


@router.get("/summary", response_model=PortfolioSummary)
async def portfolio_summary(
    user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """Get aggregate portfolio summary for the organization."""
    pm = _get_pm(db)
    return await pm.get_summary(org.id)


@router.get("/{portfolio_id}", response_model=PortfolioResponse)
async def get_portfolio(
    portfolio_id: int,
    user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """Get a single portfolio by ID."""
    pm = _get_pm(db)
    try:
        return await pm.get_portfolio(org.id, portfolio_id)
    except PortfolioNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio not found")


@router.put("/{portfolio_id}", response_model=PortfolioResponse)
async def update_portfolio(
    portfolio_id: int,
    data: PortfolioUpdate,
    user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """Update a portfolio."""
    pm = _get_pm(db)
    try:
        return await pm.update_portfolio(org.id, portfolio_id, data.model_dump(exclude_unset=True))
    except PortfolioNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio not found")


@router.delete("/{portfolio_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_portfolio(
    portfolio_id: int,
    user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """Archive (soft-delete) a portfolio."""
    pm = _get_pm(db)
    try:
        await pm.delete_portfolio(org.id, portfolio_id)
    except PortfolioNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio not found")


# ── Holdings ────────────────────────────────────────────────


@router.get("/{portfolio_id}/holdings", response_model=list[PortfolioHoldingResponse])
async def list_holdings(
    portfolio_id: int,
    user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """List all active holdings for a portfolio."""
    pm = _get_pm(db)
    # Verify portfolio access
    try:
        await pm.get_portfolio(org.id, portfolio_id)
    except PortfolioNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio not found")
    return await pm.get_holdings(portfolio_id)


@router.post("/{portfolio_id}/holdings", response_model=PortfolioHoldingResponse, status_code=status.HTTP_201_CREATED)
async def add_holding(
    portfolio_id: int,
    data: PortfolioHoldingCreate,
    user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """Add a holding to a portfolio."""
    pm = _get_pm(db)
    try:
        await pm.get_portfolio(org.id, portfolio_id)
    except PortfolioNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio not found")
    try:
        return await pm.add_holding(portfolio_id, data.model_dump())
    except InsufficientCapitalError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{portfolio_id}/holdings/batch", response_model=list[PortfolioHoldingResponse])
async def batch_update_holdings(
    portfolio_id: int,
    holdings_data: list[PortfolioHoldingCreate],
    user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """Batch update all holdings for a portfolio (replaces the set)."""
    pm = _get_pm(db)
    try:
        await pm.get_portfolio(org.id, portfolio_id)
    except PortfolioNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio not found")
    try:
        return await pm.batch_update_holdings(
            portfolio_id, [h.model_dump() for h in holdings_data]
        )
    except InsufficientCapitalError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{portfolio_id}/holdings/{holding_id}", response_model=PortfolioHoldingResponse)
async def update_holding(
    portfolio_id: int,
    holding_id: int,
    data: PortfolioHoldingUpdate,
    user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """Update a specific holding."""
    pm = _get_pm(db)
    try:
        return await pm.update_holding(holding_id, data.model_dump(exclude_unset=True))
    except HoldingNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Holding not found")
    except InsufficientCapitalError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{portfolio_id}/holdings/{holding_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_holding(
    portfolio_id: int,
    holding_id: int,
    user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """Remove (soft-delete) a holding."""
    pm = _get_pm(db)
    try:
        await pm.remove_holding(holding_id)
    except HoldingNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Holding not found")


# ── Rebalance ───────────────────────────────────────────────


@router.post("/{portfolio_id}/rebalance/plan", response_model=RebalancePlan)
async def rebalance_plan(
    portfolio_id: int,
    user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """Preview a rebalance plan without executing."""
    pm = _get_pm(db)
    try:
        await pm.get_portfolio(org.id, portfolio_id)
    except PortfolioNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio not found")
    return await pm.calculate_rebalance_plan(portfolio_id, org.id)


@router.post("/{portfolio_id}/rebalance/execute", response_model=list[RebalanceOrderResponse])
async def rebalance_execute(
    portfolio_id: int,
    req: RebalanceExecuteRequest,
    user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """Execute a rebalance for a portfolio."""
    if not req.confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must set confirm=true to execute the rebalance",
        )
    pm = _get_pm(db)
    try:
        await pm.get_portfolio(org.id, portfolio_id)
    except PortfolioNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio not found")
    return await pm.execute_rebalance(portfolio_id, user.id, req.order_type, org.id)


# ── Sync ────────────────────────────────────────────────────


@router.post("/{portfolio_id}/sync")
async def sync_portfolio(
    portfolio_id: int,
    user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """Sync portfolio holdings from the linked broker connection."""
    pm = _get_pm(db)
    try:
        await pm.get_portfolio(org.id, portfolio_id)
    except PortfolioNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio not found")
    result = await pm.sync_from_broker(portfolio_id, org.id)
    return result


# ── Performance & Allocation ────────────────────────────────


@router.get("/{portfolio_id}/performance", response_model=list[PerformanceData])
async def portfolio_performance(
    portfolio_id: int,
    days: int = Query(default=30, ge=1, le=365),
    user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """Get performance data for charting."""
    pm = _get_pm(db)
    try:
        await pm.get_portfolio(org.id, portfolio_id)
    except PortfolioNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio not found")
    return await pm.get_performance(portfolio_id, days)


@router.get("/{portfolio_id}/allocation", response_model=list[AllocationData])
async def portfolio_allocation(
    portfolio_id: int,
    user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """Get current vs target allocation for pie chart."""
    pm = _get_pm(db)
    try:
        await pm.get_portfolio(org.id, portfolio_id)
    except PortfolioNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio not found")
    return await pm.get_allocation(portfolio_id)
