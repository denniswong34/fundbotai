"""User settings model — language, theme, timezone per user."""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database import Base


class UserSettings(Base):
    """Per-user settings for i18n, theme, and Telegram notifications."""

    __tablename__ = "user_settings"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    language = Column(String(10), nullable=False, default="en")
    theme = Column(String(10), nullable=False, default="dark")
    timezone = Column(String(50), nullable=False, default="Asia/Hong_Kong")
    telegram_chat_id = Column(String(100), nullable=True)
    telegram_enabled = Column(Boolean, default=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
