"""Notification model for alerts and notifications."""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.sql import func
from app.database import Base
import enum


def enum_values(enum_type):
    return [e.value for e in enum_type]


class NotificationType(str, enum.Enum):
    REBALANCE = "rebalance"
    DRIFT_ALERT = "drift_alert"
    DAILY_REPORT = "daily_report"
    ERROR = "error"
    SYSTEM = "system"


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id", ondelete="SET NULL"), nullable=True)
    type = Column(Enum(NotificationType, values_callable=enum_values), nullable=False)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    telegram_sent = Column(Boolean, default=False)
    sent_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
