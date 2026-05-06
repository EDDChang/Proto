"""Portfolio aggregation and sector analytics — pure functions, no I/O."""

from decimal import Decimal

from protofiler.models import AccountSummary, Portfolio, Position, Sector, SectorSnapshot

_UNASSIGNED = "Unassigned"


def aggregate(
    positions_by_broker: dict[str, list[Position]],
    summaries: list[AccountSummary] | None = None,
) -> Portfolio:
    """Flatten all broker positions into a single Portfolio."""
    all_positions: list[Position] = []
    for positions in positions_by_broker.values():
        all_positions.extend(positions)
    return Portfolio(positions=all_positions, account_summaries=summaries or [])


def sector_stats(portfolio: Portfolio, sectors: list[Sector]) -> list[SectorSnapshot]:
    """Compute market value and portfolio percentage for each sector.

    Positions not assigned to any sector appear under 'Unassigned'.
    """
    total = portfolio.total_market_value
    if total == Decimal(0):
        return []

    # Build a lookup: symbol -> sector name
    symbol_to_sector: dict[str, str] = {}
    for sector in sectors:
        for sym in sector.symbols:
            symbol_to_sector[sym.upper()] = sector.name

    # Bucket positions by sector
    buckets: dict[str, list[Position]] = {}
    for pos in portfolio.positions:
        sector_name = symbol_to_sector.get(pos.symbol.upper(), _UNASSIGNED)
        buckets.setdefault(sector_name, []).append(pos)

    snapshots: list[SectorSnapshot] = []
    for sector_name, positions in sorted(buckets.items()):
        mv = sum((p.market_value for p in positions), Decimal(0))
        pct = float(mv / total * 100)
        snapshots.append(
            SectorSnapshot(
                sector=sector_name,
                market_value=mv,
                pct_of_total=pct,
                positions=positions,
            )
        )

    return sorted(snapshots, key=lambda s: s.pct_of_total, reverse=True)
