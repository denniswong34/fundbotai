"""Broker connection model — stores API keys and connection config for each broker."""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum, Boolean, JSON
from sqlalchemy.sql import func
from app.database import Base
import enum


def enum_values(enum_type):
    return [e.value for e in enum_type]


class MarketType(str, enum.Enum):
    STOCKS = "stocks"
    CRYPTO = "crypto"
    BOTH = "both"


class BrokerConnection(Base):
    __tablename__ = "broker_connections"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    broker_type = Column(String(50), nullable=False, default="paper")
    market_type = Column(Enum(MarketType, values_callable=enum_values), default=MarketType.STOCKS, nullable=False)
    is_active = Column(Boolean, default=True)

    # Flexible JSON config for broker-type-specific settings
    config_json = Column(JSON, default=dict)

    # Multi-account support: store which sub-account this connection uses
    sub_account_id = Column(String(100), nullable=True)

    # Connection status
    is_connected = Column(Boolean, default=False)
    last_connected_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
