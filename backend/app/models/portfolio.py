"""Portfolio management models — the core of FundPort."""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum, Boolean, JSON, DECIMAL
from sqlalchemy.sql import func
from app.database import Base
import enum


def enum_values(enum_type):
    return [e.value for e in enum_type]


# ── Enums ──────────────────────────────────────────────

class PortfolioStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class RebalanceMethod(str, enum.Enum):
    WEIGHT_ONLY = "weight_only"
    TARGET_VALUE = "target_value"
    DRIFT = "drift"


class OrderType(str, enum.Enum):
    MARKET = "market"
    LIMIT = "limit"


class OrderSide(str, enum.Enum):
    BUY = "buy"
    SELL = "sell"


class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    SUBMITTED = "submitted"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    FAILED = "failed"


# ── Models ─────────────────────────────────────────────

class Portfolio(Base):
    """
    A named collection of target-weight holdings linked to a broker connection.
    Each portfolio tracks its own capital allocation and rebalance settings.
    """
    __tablename__ = "portfolios"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    broker_connection_id = Column(
        Integer, ForeignKey("broker_connections.id", ondelete="SET NULL"), nullable=True
    )

    # Identity
    name = Column(String(100), nullable=False)
    description = Column(Text)
    base_currency = Column(String(10), nullable=False, default="USD")

    # Capital
    total_capital = Column(DECIMAL(15, 2), nullable=False, default=0.00)

    # Status
    status = Column(Enum(PortfolioStatus, values_callable=enum_values), default=PortfolioStatus.ACTIVE)

    # ── Rebalance User Config (configurable in app/web) ──
    rebalance_method = Column(
        Enum(RebalanceMethod, values_callable=enum_values),
        default=RebalanceMethod.WEIGHT_ONLY
    )
    rebalance_order_type = Column(
        Enum(OrderType, values_callable=enum_values),
        default=OrderType.MARKET,
        comment="market or limit — user configurable"
    )
    limit_price_tolerance_pct = Column(
        DECIMAL(5, 2), default=0.50,
        comment="e.g. 0.50 = 0.5% tolerance from market price for limit orders"
    )
    drift_threshold_pct = Column(
        DECIMAL(5, 2), default=5.00,
        comment="% deviation from target weight that triggers rebalance alert"
    )
    cash_reserve_pct = Column(
        DECIMAL(5, 2), default=0.00,
        comment="% of total capital kept as cash (user configurable)"
    )
    auto_rebalance_enabled = Column(
        Boolean, default=False,
        comment="cron will auto-rebalance when drift exceeds threshold"
    )
    rebalance_frequency = Column(
        String(20), default="drift_only",
        comment="User config: 'drift_only', 'daily', 'weekly', 'monthly', 'quarterly'"
    )

    # Aggregated stats (updated after sync/rebalance)
    total_value = Column(DECIMAL(15, 2), default=0.00)
    total_cost = Column(DECIMAL(15, 2), default=0.00)
    total_pnl = Column(DECIMAL(15, 2), default=0.00)
    total_pnl_pct = Column(DECIMAL(7, 4), default=0.00)
    last_rebalanced_at = Column(DateTime, nullable=True)
    last_synced_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Broker sub-account selection (for multi-account brokers)
    broker_sub_account_id = Column(String(100), nullable=True)


class PortfolioHolding(Base):
    """
    A single holding within a portfolio: symbol + target weight + current state.
    """
    __tablename__ = "portfolio_holdings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False)

    # Identity
    symbol = Column(String(20), nullable=False)
    asset_type = Column(String(20), default="stock")  # stock, etf, crypto
    market = Column(String(10), nullable=False, default="US")  # US, HK, CN, JP
    currency = Column(String(10), nullable=False, default="USD")

    # Target
    target_weight_pct = Column(DECIMAL(7, 4), nullable=False)

    # Current state (from broker sync)
    current_shares = Column(DECIMAL(15, 4), default=0)
    avg_cost = Column(DECIMAL(15, 4), default=0)
    current_price = Column(DECIMAL(15, 4), default=0)
    market_value = Column(DECIMAL(15, 2), default=0)
    unrealized_pnl = Column(DECIMAL(15, 2), default=0)
    unrealized_pnl_pct = Column(DECIMAL(7, 4), default=0)

    # Market-specific lot size (minimum purchase unit)
    lot_size = Column(Integer, default=1, nullable=False,
                      comment="Minimum tradable unit: US=1, HK=lot (default 100), CN=100, JP=100")

    # Flags
    is_active = Column(Boolean, default=True)
    notes = Column(Text)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class PortfolioRebalanceOrder(Base):
    """
    Tracks individual orders placed during a portfolio rebalance.
    Orders are grouped by rebalance_group_id (UUID) for a single rebalance run.
    """
    __tablename__ = "portfolio_rebalance_orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)

    # Group tracking
    rebalance_group_id = Column(String(36), nullable=False, index=True)
    sequence = Column(Integer, default=0)

    # Order details
    symbol = Column(String(20), nullable=False)
    side = Column(Enum(OrderSide, values_callable=enum_values), nullable=False)
    order_type = Column(Enum(OrderType, values_callable=enum_values), default=OrderType.MARKET)
    target_qty = Column(DECIMAL(15, 4), nullable=False)
    target_value = Column(DECIMAL(15, 2), nullable=False)
    limit_price = Column(DECIMAL(15, 4), nullable=True)

    # Execution
    status = Column(Enum(OrderStatus, values_callable=enum_values), default=OrderStatus.PENDING)
    filled_qty = Column(DECIMAL(15, 4), default=0)
    avg_fill_price = Column(DECIMAL(15, 4), default=0)
    filled_value = Column(DECIMAL(15, 2), default=0)
    broker_order_id = Column(String(100))

    # Error handling
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class PortfolioPerformanceSnapshot(Base):
    """
    Daily snapshot of portfolio value and composition.
    Used for performance charts and historical tracking.
    """
    __tablename__ = "portfolio_performance_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False)
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    snapshot_date = Column(DateTime, nullable=False)

    total_value = Column(DECIMAL(15, 2), nullable=False)
    cash_balance = Column(DECIMAL(15, 2), default=0)
    invested_value = Column(DECIMAL(15, 2), default=0)
    daily_pnl = Column(DECIMAL(15, 2), default=0)
    daily_return_pct = Column(DECIMAL(7, 4), default=0)
    total_pnl = Column(DECIMAL(15, 2), default=0)
    total_return_pct = Column(DECIMAL(7, 4), default=0)

    holdings_snapshot = Column(JSON)  # Full snapshot of all holdings

    created_at = Column(DateTime, server_default=func.now())
