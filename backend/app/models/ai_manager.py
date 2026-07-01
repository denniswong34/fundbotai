"""AI Manager models — LLM-powered portfolio managers for the Arena."""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, JSON, DECIMAL
from sqlalchemy.sql import func
from app.database import Base


class AiManager(Base):
    """Configuration for an AI fund manager — which LLM, which portfolio, what style."""
    __tablename__ = "ai_managers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Identity
    name = Column(String(100), nullable=False)
    description = Column(Text)

    # LLM Configuration
    model_provider = Column(String(50), nullable=False, default="opencode-go",
                            comment="Provider name, e.g. opencode-go, openai, custom")
    model_name = Column(String(100), nullable=False,
                        comment="Model identifier, e.g. deepseek-v4-flash, gpt-4o, claude-sonnet-4")
    api_base_url = Column(String(255), nullable=True,
                          comment="Optional custom API base URL for the LLM provider")
    system_prompt = Column(Text, comment="Overrides the default trading style system prompt")
    temperature = Column(DECIMAL(3, 2), default=0.70)
    max_tokens = Column(Integer, default=4000)

    # Portfolio link
    assigned_portfolio_id = Column(Integer, ForeignKey("portfolios.id", ondelete="SET NULL"), nullable=True)

    # Schedule
    run_frequency = Column(String(20), default="daily",
                           comment="daily, weekly, manual — how often to auto-trigger decisions")
    auto_run_enabled = Column(Boolean, default=False,
                              comment="If True, cron/APScheduler will auto-trigger decisions")

    # Cached performance stats (updated after each decision cycle)
    total_return_pct = Column(DECIMAL(7, 4), default=0.00)
    sharpe_ratio = Column(DECIMAL(7, 4), default=0.00)
    win_rate = Column(DECIMAL(5, 2), default=0.00)
    total_trades = Column(Integer, default=0)
    decisions_count = Column(Integer, default=0)
    last_decision_at = Column(DateTime, nullable=True)

    # Status
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class AiDecisionLog(Base):
    """Record of every AI manager decision — full audit trail."""
    __tablename__ = "ai_decision_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ai_manager_id = Column(Integer, ForeignKey("ai_managers.id", ondelete="CASCADE"), nullable=False)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id", ondelete="SET NULL"), nullable=True)
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Trigger info
    triggered_at = Column(DateTime, nullable=False, server_default=func.now())
    market_regime = Column(String(20), nullable=True,
                           comment="bull, bear, range, volatile, uncertain")
    trigger_source = Column(String(20), default="manual",
                            comment="manual, cron, api")

    # Full data context
    data_snapshot = Column(JSON, comment="Live market data snapshot at decision time")
    rag_results_used = Column(JSON, comment="RAG retrieval results injected into prompt")

    # LLM interaction
    prompt_sent = Column(Text)
    raw_response = Column(Text)
    parsed_decision = Column(JSON)
    reasoning = Column(Text)

    # Risk & benchmark
    risk_assessment = Column(JSON)
    benchmark_analysis = Column(JSON)

    # Portfolio state
    portfolio_snapshot_before = Column(JSON)
    portfolio_snapshot_after = Column(JSON)

    # Execution
    orders_created = Column(Integer, default=0)
    execution_status = Column(String(20), default="pending",
                              comment="pending, executed, rejected, failed")
    execution_error = Column(Text)

    created_at = Column(DateTime, server_default=func.now())
