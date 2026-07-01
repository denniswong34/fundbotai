"""AI Manager API router — CRUD, decision triggering, leaderboard, comparison chart.
NOTE: Static routes MUST come before parameterized routes ({manager_id}) to avoid
FastAPI treating 'leaderboard' etc. as integer path params."""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, get_current_org
from app.models.user import User
from app.models.organization import Organization
from app.schemas.ai_manager import (
    AiManagerCreate,
    AiManagerUpdate,
    AiManagerResponse,
    TriggerDecisionRequest,
    DecisionLogResponse,
    LeaderboardResponse,
    ComparisonChartData,
)
from app.services.arena_service import ArenaService, AiManagerNotFound

router = APIRouter(prefix="/api/ai-managers", tags=["ai-managers"])


def _get_svc(db: AsyncSession) -> ArenaService:
    return ArenaService(db)


# ── STATIC ROUTES FIRST (before parameterized routes) ─────────


@router.get("/leaderboard", response_model=LeaderboardResponse)
async def get_leaderboard(
    user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """Get AI manager leaderboard ranked by performance."""
    svc = _get_svc(db)
    return await svc.get_leaderboard(org.id)


@router.get("/comparison-chart", response_model=ComparisonChartData)
async def get_comparison_chart(
    user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """Get multi-series comparison chart data for all active managers."""
    svc = _get_svc(db)
    return await svc.get_comparison_chart(org.id)


@router.post("/trigger-all")
async def trigger_all_managers(
    user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """Trigger decisions for all active AI managers."""
    svc = _get_svc(db)
    managers = await svc.get_managers(org.id)
    results = []
    for m in managers:
        if m.is_active:
            try:
                result = await svc.trigger_decision(org.id, m.id, trigger_source="bulk")
                results.append({"manager_id": m.id, "name": m.name, "status": "success"})
            except Exception as e:
                results.append({"manager_id": m.id, "name": m.name, "status": "error", "error": str(e)})
    return {"results": results, "total": len(results), "succeeded": sum(1 for r in results if r["status"] == "success")}


# ── CRUD ──────────────────────────────────────────────────────


@router.get("", response_model=list[AiManagerResponse])
async def list_managers(
    user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """List all AI managers for the current organization."""
    svc = _get_svc(db)
    return await svc.get_managers(org.id)


@router.post("", response_model=AiManagerResponse, status_code=status.HTTP_201_CREATED)
async def create_manager(
    data: AiManagerCreate,
    user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """Create a new AI fund manager."""
    svc = _get_svc(db)
    try:
        return await svc.create_manager(org.id, user.id, data.model_dump())
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ── PARAMETERIZED ROUTES ──────────────────────────────────────


@router.get("/{manager_id}", response_model=AiManagerResponse)
async def get_manager(
    manager_id: int,
    user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """Get details of a specific AI manager."""
    svc = _get_svc(db)
    try:
        return await svc.get_manager(org.id, manager_id)
    except AiManagerNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI Manager not found")


@router.put("/{manager_id}", response_model=AiManagerResponse)
async def update_manager(
    manager_id: int,
    data: AiManagerUpdate,
    user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """Update an AI manager's configuration."""
    svc = _get_svc(db)
    try:
        return await svc.update_manager(org.id, manager_id, data.model_dump(exclude_unset=True))
    except AiManagerNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI Manager not found")


@router.delete("/{manager_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_manager(
    manager_id: int,
    user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """Soft-delete (deactivate) an AI manager."""
    svc = _get_svc(db)
    try:
        await svc.delete_manager(org.id, manager_id)
    except AiManagerNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI Manager not found")


@router.post("/{manager_id}/trigger")
async def trigger_decision(
    manager_id: int,
    req: TriggerDecisionRequest,
    user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """Trigger an AI fund manager decision cycle."""
    svc = _get_svc(db)
    try:
        return await svc.trigger_decision(org.id, manager_id, trigger_source=req.trigger_source)
    except AiManagerNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI Manager not found")


# ── Decision Logs ─────────────────────────────────────────────


@router.get("/{manager_id}/decisions", response_model=list[DecisionLogResponse])
async def list_decisions(
    manager_id: int,
    limit: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """Get decision history for an AI manager."""
    svc = _get_svc(db)
    return await svc.get_decision_logs(org.id, manager_id, limit)


@router.get("/{manager_id}/decisions/{log_id}", response_model=DecisionLogResponse)
async def get_decision_log(
    manager_id: int,
    log_id: int,
    user: User = Depends(get_current_user),
    org: Organization = Depends(get_current_org),
    db: AsyncSession = Depends(get_db),
):
    """Get a single decision log entry."""
    svc = _get_svc(db)
    try:
        return await svc.get_decision_log(org.id, log_id)
    except AiManagerNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Decision log not found")
