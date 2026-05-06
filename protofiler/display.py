"""Rich-based terminal rendering for portfolio and sector views."""

from decimal import Decimal

from rich.console import Console
from rich.table import Table
from rich import box

from protofiler.models import Portfolio, SectorSnapshot

console = Console()


def render_positions(portfolio: Portfolio) -> None:
    """Display all positions in a formatted table."""
    table = Table(
        title="Portfolio Positions",
        box=box.ROUNDED,
        show_lines=False,
    )
    table.add_column("Symbol", style="cyan", no_wrap=True)
    table.add_column("Name", style="white")
    table.add_column("Type", style="yellow")
    table.add_column("Broker", style="magenta")
    table.add_column("Qty", justify="right")
    table.add_column("Avg Cost", justify="right")
    table.add_column("Market Price", justify="right")
    table.add_column("Market Value", justify="right", style="green")
    table.add_column("PnL", justify="right")

    for pos in portfolio.positions:
        pnl = pos.unrealized_pnl
        pnl_str = f"{pnl:,.2f}"
        pnl_style = "green" if pnl >= Decimal(0) else "red"

        table.add_row(
            pos.symbol,
            pos.name or "",
            pos.asset_type.value,
            pos.broker,
            f"{pos.quantity:,}",
            f"{pos.avg_cost:,.4f}",
            f"{pos.market_price:,.4f}",
            f"{pos.market_value:,.2f}",
            f"[{pnl_style}]{pnl_str}[/{pnl_style}]",
        )

    table.caption = f"Total Market Value: {portfolio.total_market_value:,.2f}"
    console.print(table)


def render_sector_stats(snapshots: list[SectorSnapshot], total_value: Decimal) -> None:
    """Display sector allocation breakdown."""
    table = Table(
        title="Sector Allocation",
        box=box.ROUNDED,
        show_lines=False,
    )
    table.add_column("Sector", style="cyan")
    table.add_column("Symbols", style="white")
    table.add_column("Market Value", justify="right", style="green")
    table.add_column("% of Portfolio", justify="right", style="yellow")
    table.add_column("Bar", style="blue")

    for snap in snapshots:
        symbols = ", ".join(p.symbol for p in snap.positions)
        bar_len = max(1, round(snap.pct_of_total / 2))
        bar = "█" * bar_len
        table.add_row(
            snap.sector,
            symbols,
            f"{snap.market_value:,.2f}",
            f"{snap.pct_of_total:.1f}%",
            bar,
        )

    table.caption = f"Total: {total_value:,.2f}"
    console.print(table)


def render_sectors(sectors: list) -> None:
    """Display all defined sectors and their symbols."""
    table = Table(title="Defined Sectors", box=box.ROUNDED)
    table.add_column("Sector", style="cyan")
    table.add_column("Symbols", style="white")
    table.add_column("Count", justify="right", style="yellow")

    for sector in sectors:
        table.add_row(
            sector.name,
            ", ".join(sector.symbols) or "(none)",
            str(len(sector.symbols)),
        )

    console.print(table)
