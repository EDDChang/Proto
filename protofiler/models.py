"""Core data models for protofiler."""

from decimal import Decimal
from enum import StrEnum
from typing import Optional

from pydantic import BaseModel, computed_field


class AssetType(StrEnum):
    STOCK = "stock"
    FUTURES = "futures"
    OPTIONS = "options"
    CASH = "cash"
    OTHER = "other"


class Position(BaseModel):
    """A single holding at a broker."""

    symbol: str
    quantity: Decimal
    avg_cost: Decimal
    market_price: Decimal
    asset_type: AssetType
    broker: str
    currency: str = "USD"
    # Human-readable name, optional — may not be available from all brokers
    name: Optional[str] = None

    @computed_field
    @property
    def market_value(self) -> Decimal:
        return self.quantity * self.market_price

    @computed_field
    @property
    def unrealized_pnl(self) -> Decimal:
        return (self.market_price - self.avg_cost) * self.quantity


class Sector(BaseModel):
    """A user-defined group of symbols for sector/cluster analysis."""

    name: str
    symbols: list[str] = []


class SectorSnapshot(BaseModel):
    """Computed sector allocation at a point in time."""

    sector: str
    market_value: Decimal
    pct_of_total: float
    positions: list[Position] = []


class Portfolio(BaseModel):
    """Aggregated view of all positions across brokers."""

    positions: list[Position] = []

    @computed_field
    @property
    def total_market_value(self) -> Decimal:
        return sum((p.market_value for p in self.positions), Decimal(0))
