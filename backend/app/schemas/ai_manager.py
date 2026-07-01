"""AI Manager Pydantic schemas for request/response validation."""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field


# ── Create ────────────────────────────────────────────────────

class AiManagerCreate(BaseModel):
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    model_provider: str = "opencode-go"
    model_name: str = Field(..., description="e.g. deepseek-v4-flash, gpt-4o, claude-sonnet-4")
    api_base_url: Optional[str] = None
    system_prompt: Optional[str] = None
    temperature: float = 0.70
    max_tokens: int = 4000
    assigned_portfolio_id: Optional[int] = None
    run_frequency: str = "daily"
    auto_run_enabled: bool = False
    is_active: bool = True


class AiManagerUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    model_provider: Optional[str] = None
    model_name: Optional[str] = None
    api_base_url: Optional[str] = None
    system_prompt: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    assigned_portfolio_id: Optional[int] = None
    run_frequency: Optional[str] = None
    auto_run_enabled: Optional[bool] = None
    is_active: Optional[bool] = None


# ── Response ──────────────────────────────────────────────────

class AiManagerResponse(BaseModel):
    id: int
    org_id: int
    user_id: int
    name: str
    description: Optional[str] = None
    model_provider: str
    model_name: str
    api_base_url: Optional[str] = None
    system_prompt: Optional[str] = None
    temperature: float
    max_tokens: int
    assigned_portfolio_id: Optional[int] = None
    run_frequency: str
    auto_run_enabled: bool
    total_return_pct: float
    sharpe_ratio: float
    win_rate: float
    total_trades: int
    decisions_count: int
    last_decision_at: Optional[datetime] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ── Trigger Decision ──────────────────────────────────────────

class TriggerDecisionRequest(BaseModel):
    trigger_source: str = "manual"


class DecisionLogResponse(BaseModel):
    id: int
    ai_manager_id: int
    portfolio_id: Optional[int] = None
    triggered_at: datetime
    market_regime: Optional[str] = None
    trigger_source: str
    data_snapshot: Optional[dict] = None
    rag_results_used: Optional[list] = None
    prompt_sent: Optional[str] = None
    raw_response: Optional[str] = None
    parsed_decision: Optional[dict] = None
    reasoning: Optional[str] = None
    risk_assessment: object = None
    benchmark_analysis: object = None
    portfolio_snapshot_before: Optional[dict] = None
    orders_created: int
    execution_status: str
    execution_error: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True


# ── Leaderboard ───────────────────────────────────────────────

class LeaderboardEntry(BaseModel):
    rank: int
    medal: str
    id: int
    name: str
    model_name: str
    portfolio_id: Optional[int] = None
    total_return_pct: float
    alpha_pct: float
    sharpe_ratio: float
    max_drawdown_pct: float
    ai_score: float
    volatility_pct: float
    total_trades: int
    decisions_count: int
    last_decision_at: Optional[datetime] = None
    is_active: bool


class LeaderboardResponse(BaseModel):
    entries: list[LeaderboardEntry]
    total_count: int
    updated_at: datetime


# ── Comparison Chart ──────────────────────────────────────────

class ComparisonSeries(BaseModel):
    manager_id: int
    manager_name: str
    model_name: str
    color: str
    data: list[dict]  # [{date, value}, ...]


class ComparisonChartData(BaseModel):
    series: list[ComparisonSeries]
    benchmark_series: Optional[list[dict]] = None  # SPY comparison
