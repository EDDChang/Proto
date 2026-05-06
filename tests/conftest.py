"""Shared test fixtures."""

from decimal import Decimal

import pytest

from protofiler.models import AssetType, Position, Sector


@pytest.fixture
def sample_positions() -> list[Position]:
    return [
        Position(
            symbol="AAPL",
            quantity=Decimal("10"),
            avg_cost=Decimal("150.00"),
            market_price=Decimal("170.00"),
            asset_type=AssetType.STOCK,
            broker="ib",
            currency="USD",
        ),
        Position(
            symbol="MSFT",
            quantity=Decimal("5"),
            avg_cost=Decimal("300.00"),
            market_price=Decimal("320.00"),
            asset_type=AssetType.STOCK,
            broker="ib",
            currency="USD",
        ),
        Position(
            symbol="XOM",
            quantity=Decimal("20"),
            avg_cost=Decimal("90.00"),
            market_price=Decimal("95.00"),
            asset_type=AssetType.STOCK,
            broker="sinopac",
            currency="USD",
        ),
    ]


@pytest.fixture
def sample_sectors() -> list[Sector]:
    return [
        Sector(name="Tech", symbols=["AAPL", "MSFT"]),
        Sector(name="Energy", symbols=["XOM"]),
    ]
