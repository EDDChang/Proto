"""Rich-based terminal rendering for portfolio and sector views."""

from decimal import Decimal
from typing import Union

from rich.console import Console
from rich.table import Table
from rich import box

from protofiler.models import AccountSummary, Portfolio, SectorSnapshot

console = Console()


def _fmt(value: Decimal) -> str:
    """Compact number format: K suffix >= 1,000, 2 dp below that."""
    f = float(value)
    if abs(f) >= 1_000:
        return f"{f/1000:,.2f}K"
    return f"{f:,.2f}"


def render_positions(portfolio: Portfolio) -> None:
    """Display all positions in a formatted table."""
    table = Table(
        title="Portfolio Positions",
        box=box.ROUNDED,
        show_lines=False,
        expand=False,
    )
    table.add_column("Symbol", style="cyan", no_wrap=True, max_width=22)
    table.add_column("T", style="yellow", no_wrap=True)   # asset type initial
    table.add_column("Qty", justify="right", no_wrap=True, min_width=6)
    table.add_column("Avg", justify="right", no_wrap=True)
    table.add_column("Price", justify="right", no_wrap=True)
    table.add_column("Value", justify="right", style="green", no_wrap=True)
    table.add_column("PnL", justify="right", no_wrap=True)

    for pos in portfolio.positions:
        pnl = pos.unrealized_pnl
        pnl_style = "green" if pnl >= Decimal(0) else "red"

        pnl_sign = "+" if pnl >= Decimal(0) else ""
        table.add_row(
            pos.symbol,
            pos.asset_type.value[0].upper(),  # S / F / O / C
            f"{pos.quantity:,}",
            _fmt(pos.avg_cost),
            _fmt(pos.market_price),
            _fmt(pos.market_value),
            f"[{pnl_style}]{pnl_sign}{_fmt(pnl)}[/{pnl_style}]",
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


def render_account_summaries(summaries: list[AccountSummary]) -> None:
    """Display account-level cash and margin figures."""
    table = Table(title="Account Summary", box=box.ROUNDED, show_lines=False)
    table.add_column("Broker", style="magenta", no_wrap=True)
    table.add_column("Net Liq", justify="right", style="green", no_wrap=True)
    table.add_column("Cash", justify="right", no_wrap=True)
    table.add_column("Positions", justify="right", no_wrap=True)
    table.add_column("Unrealized PnL", justify="right", no_wrap=True)
    table.add_column("CCY", no_wrap=True)

    for s in summaries:
        cash_style = "red" if s.total_cash < Decimal(0) else "white"
        pnl_style = "green" if s.unrealized_pnl >= Decimal(0) else "red"
        pnl_sign = "+" if s.unrealized_pnl >= Decimal(0) else ""
        table.add_row(
            s.broker,
            _fmt(s.net_liquidation),
            f"[{cash_style}]{_fmt(s.total_cash)}[/{cash_style}]",
            _fmt(s.gross_position_value),
            f"[{pnl_style}]{pnl_sign}{_fmt(s.unrealized_pnl)}[/{pnl_style}]",
            s.currency,
        )

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
