"""Tests for portfolio aggregation and sector analytics."""

from decimal import Decimal

import pytest

from protofiler.models import Portfolio
from protofiler.portfolio import aggregate, sector_stats


def test_aggregate_combines_all_brokers(sample_positions):
    ib_pos = sample_positions[:2]
    sinopac_pos = sample_positions[2:]
    portfolio = aggregate({"ib": ib_pos, "sinopac": sinopac_pos})

    assert len(portfolio.positions) == 3
    # AAPL 10*170 + MSFT 5*320 + XOM 20*95
    expected = Decimal("1700") + Decimal("1600") + Decimal("1900")
    assert portfolio.total_market_value == expected


def test_aggregate_empty_returns_zero_value():
    portfolio = aggregate({})
    assert portfolio.total_market_value == Decimal(0)


def test_sector_stats_percentages(sample_positions, sample_sectors):
    portfolio = Portfolio(positions=sample_positions)
    snapshots = sector_stats(portfolio, sample_sectors)

    total = portfolio.total_market_value
    assert total > 0

    pct_sum = sum(s.pct_of_total for s in snapshots)
    assert abs(pct_sum - 100.0) < 0.01

    by_name = {s.sector: s for s in snapshots}
    assert "Tech" in by_name
    assert "Energy" in by_name

    tech_mv = Decimal("1700") + Decimal("1600")  # AAPL + MSFT
    assert by_name["Tech"].market_value == tech_mv


def test_sector_stats_unassigned(sample_positions, sample_sectors):
    """Positions not in any sector should appear as 'Unassigned'."""
    from protofiler.models import AssetType, Position

    extra = Position(
        symbol="TSLA",
        quantity=Decimal("2"),
        avg_cost=Decimal("200"),
        market_price=Decimal("210"),
        asset_type=AssetType.STOCK,
        broker="ib",
        currency="USD",
    )
    from protofiler.models import Portfolio

    portfolio = Portfolio(positions=sample_positions + [extra])
    snapshots = sector_stats(portfolio, sample_sectors)
    by_name = {s.sector: s for s in snapshots}
    assert "Unassigned" in by_name


def test_sector_stats_empty_portfolio(sample_sectors):
    portfolio = Portfolio(positions=[])
    snapshots = sector_stats(portfolio, sample_sectors)
    assert snapshots == []


def test_position_market_value(sample_positions):
    aapl = sample_positions[0]
    assert aapl.market_value == Decimal("1700.00")


def test_position_unrealized_pnl(sample_positions):
    aapl = sample_positions[0]
    assert aapl.unrealized_pnl == Decimal("200.00")
