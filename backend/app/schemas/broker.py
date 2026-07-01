"""Pydantic schemas for broker connections."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class BrokerConnectionCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    broker_type: str = Field(..., min_length=1, max_length=50)
    market_type: str = Field(default="stocks", pattern=r"^(stocks|crypto|both)$")
    sandbox: bool = Field(default=True, description="True=sandbox/testnet, False=live/production")
    config_json: Optional[dict] = Field(default_factory=dict)
    sub_account_id: Optional[str] = None


class BrokerConnectionUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    market_type: Optional[str] = None
    sandbox: Optional[bool] = None
    config_json: Optional[dict] = None
    sub_account_id: Optional[str] = None
    is_active: Optional[bool] = None


class BrokerConnectionResponse(BaseModel):
    id: int
    user_id: int
    org_id: int
    name: str
    broker_type: str
    market_type: str
    is_active: bool
    sandbox: bool
    config_json: Optional[dict] = None
    sub_account_id: Optional[str] = None
    is_connected: bool
    last_connected_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class BrokerTypeResponse(BaseModel):
    type: str
    name: str
    description: str
    markets: list[str] = ["stocks"]
    config_schema: dict = Field(default_factory=dict)
