"""Pydantic schemas for portfolio management."""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


# ── Portfolio ────────────────────────────────────────────────


class PortfolioCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    base_currency: str = Field(default="USD", max_length=10)
    broker_connection_id: Optional[int] = None
    broker_sub_account_id: Optional[str] = None

    # Rebalance config (optional on create)
    rebalance_method: Optional[str] = None
    rebalance_order_type: Optional[str] = None
    drift_threshold_pct: Optional[Decimal] = None
    cash_reserve_pct: Optional[Decimal] = None
    auto_rebalance_enabled: Optional[bool] = None
    rebalance_frequency: Optional[str] = None


class PortfolioUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    base_currency: Optional[str] = None
    broker_connection_id: Optional[int] = None
    broker_sub_account_id: Optional[str] = None
    status: Optional[str] = None

    # Rebalance config
    rebalance_method: Optional[str] = None
    rebalance_order_type: Optional[str] = None
    drift_threshold_pct: Optional[Decimal] = None
    cash_reserve_pct: Optional[Decimal] = None
    auto_rebalance_enabled: Optional[bool] = None
    rebalance_frequency: Optional[str] = None


class PortfolioResponse(BaseModel):
    id: int
    user_id: int
    org_id: int
    broker_connection_id: Optional[int] = None
    name: str
    description: Optional[str] = None
    base_currency: str
    total_capital: Decimal
    total_value: Decimal
    total_cost: Decimal
    total_pnl: Decimal
    total_pnl_pct: Decimal
    status: str
    rebalance_method: str
    rebalance_order_type: str
    drift_threshold_pct: Decimal
    cash_reserve_pct: Decimal
    auto_rebalance_enabled: bool
    rebalance_frequency: str
    last_rebalanced_at: Optional[datetime] = None
    last_synced_at: Optional[datetime] = None
    broker_sub_account_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PortfolioSummary(BaseModel):
    total_portfolios: int
    total_value: Decimal
    total_pnl: Decimal
    total_pnl_pct: Decimal
    active_count: int


# ── Holdings ─────────────────────────────────────────────────


class PortfolioHoldingCreate(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=20)
    asset_type: str = Field(default="stock", max_length=20)
    market: str = Field(default="US", max_length=10)
    currency: str = Field(default="USD", max_length=10)
    target_weight_pct: Decimal = Field(..., ge=0, le=100)
    current_shares: Decimal = Field(default=0)
    avg_cost: Decimal = Field(default=0)
    current_price: Decimal = Field(default=0)
    notes: Optional[str] = None
    lot_size: Optional[int] = None


class PortfolioHoldingUpdate(BaseModel):
    target_weight_pct: Optional[Decimal] = Field(None, ge=0, le=100)
    current_shares: Optional[Decimal] = None
    avg_cost: Optional[Decimal] = None
    current_price: Optional[Decimal] = None
    market_value: Optional[Decimal] = None
    unrealized_pnl: Optional[Decimal] = None
    unrealized_pnl_pct: Optional[Decimal] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None
    lot_size: Optional[int] = None


class PortfolioHoldingResponse(BaseModel):
    id: int
    portfolio_id: int
    symbol: str
    asset_type: str
    market: str
    currency: str
    target_weight_pct: Decimal
    current_shares: Decimal
    avg_cost: Decimal
    current_price: Decimal
    market_value: Decimal
    unrealized_pnl: Decimal
    unrealized_pnl_pct: Decimal
    is_active: bool
    notes: Optional[str] = None
    lot_size: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class BatchHoldingUpdate(BaseModel):
    holdings: list[PortfolioHoldingCreate]


# ── Rebalance ────────────────────────────────────────────────


class RebalanceOrder(BaseModel):
    symbol: str
    side: str  # buy / sell
    current_weight_pct: Decimal
    target_weight_pct: Decimal
    current_value: Decimal
    target_value: Decimal
    diff_value: Decimal
    diff_shares: Decimal
    estimated_price: Decimal
    lot_size: Optional[int] = None
    min_units: Optional[Decimal] = None
    market: Optional[str] = None


class RebalancePlan(BaseModel):
    portfolio_id: int
    portfolio_name: str
    total_value: Decimal
    cash_reserve: Decimal
    investable_value: Decimal
    total_cost_estimate: Decimal
    orders: list[RebalanceOrder]


class RebalanceExecuteRequest(BaseModel):
    order_type: str = Field(default="market", pattern=r"^(market|limit)$")
    confirm: bool = Field(default=False)


class RebalanceOrderResponse(BaseModel):
    id: int
    portfolio_id: int
    user_id: int
    org_id: int
    rebalance_group_id: str
    sequence: int
    symbol: str
    side: str
    order_type: str
    target_qty: Decimal
    target_value: Decimal
    limit_price: Optional[Decimal] = None
    status: str
    filled_qty: Decimal
    avg_fill_price: Decimal
    filled_value: Decimal
    broker_order_id: Optional[str] = None
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ── Performance ──────────────────────────────────────────────


class PerformanceData(BaseModel):
    date: str
    total_value: Decimal
    daily_pnl: Decimal
    daily_return_pct: Decimal
    total_pnl: Decimal
    total_return_pct: Decimal


class AllocationData(BaseModel):
    symbol: str
    current_weight_pct: Decimal
    target_weight_pct: Decimal
    market_value: Decimal
    drift_pct: Decimal
    color: str = "#4CAF50"
