"""CLI entry point for protofiler."""

from __future__ import annotations

from typing import Annotated

import typer
from rich.console import Console

from protofiler.brokers import BROKER_REGISTRY
from protofiler.brokers.base import BrokerBase
from protofiler.config import get
import protofiler.portfolio as pf
import protofiler.store as store
import protofiler.display as display

app = typer.Typer(
    name="protofiler",
    help="Multi-broker portfolio profiler with sector analytics.",
    no_args_is_help=True,
)
sectors_app = typer.Typer(help="Manage sector/cluster definitions.")
app.add_typer(sectors_app, name="sectors")

err_console = Console(stderr=True, style="bold red")


def _build_brokers(broker_names: list[str]) -> list[BrokerBase]:
    brokers: list[BrokerBase] = []
    for name in broker_names:
        cls = BROKER_REGISTRY.get(name.lower())
        if cls is None:
            err_console.print(
                f"Unknown broker '{name}'. Available: {', '.join(BROKER_REGISTRY)}"
            )
            raise typer.Exit(code=1)
        brokers.append(cls())
    return brokers


# ---------------------------------------------------------------------------
# fetch
# ---------------------------------------------------------------------------


@app.command()
def fetch(
    brokers: Annotated[
        list[str],
        typer.Option("--broker", "-b", help="Broker to query (repeatable). E.g. -b ib -b sinopac"),
    ] = [],
) -> None:
    """Fetch current positions from one or more brokers and display them."""
    if not brokers:
        # Default: try all brokers whose env vars are set
        brokers = _detect_configured_brokers()
        if not brokers:
            err_console.print(
                "No brokers specified. Use --broker ib or --broker sinopac, "
                "or set the required environment variables."
            )
            raise typer.Exit(code=1)

    broker_instances = _build_brokers(brokers)
    positions_by_broker: dict[str, list] = {}
    summaries = []

    for broker in broker_instances:
        typer.echo(f"Fetching from {broker.name}…")
        try:
            positions_by_broker[broker.name] = broker.fetch_positions()
            summary = broker.fetch_account_summary()
            if summary:
                summaries.append(summary)
        except (ConnectionError, RuntimeError) as exc:
            err_console.print(f"[{broker.name}] {exc}")

    portfolio = pf.aggregate(positions_by_broker, summaries)
    display.render_positions(portfolio)
    if portfolio.account_summaries:
        display.render_account_summaries(portfolio.account_summaries)


def _detect_configured_brokers() -> list[str]:
    detected: list[str] = []
    if get("ib", "host") or get("ib", "port"):
        detected.append("ib")
    if get("sinopac", "api_key"):
        detected.append("sinopac")
    return detected


# ---------------------------------------------------------------------------
# sectors list
# ---------------------------------------------------------------------------


@sectors_app.command("list")
def sectors_list() -> None:
    """List all defined sectors."""
    sectors = store.load()
    if not sectors:
        typer.echo("No sectors defined yet. Use 'protofiler sectors add <name>' to create one.")
        return
    display.render_sectors(sectors)


# ---------------------------------------------------------------------------
# sectors add
# ---------------------------------------------------------------------------


@sectors_app.command("add")
def sectors_add(name: str = typer.Argument(..., help="Sector name")) -> None:
    """Create a new sector."""
    store.add_sector(name)
    typer.echo(f"Sector '{name}' created.")


# ---------------------------------------------------------------------------
# sectors remove
# ---------------------------------------------------------------------------


@sectors_app.command("remove")
def sectors_remove(name: str = typer.Argument(..., help="Sector name to delete")) -> None:
    """Delete a sector."""
    store.remove_sector(name)
    typer.echo(f"Sector '{name}' removed.")


# ---------------------------------------------------------------------------
# sectors assign
# ---------------------------------------------------------------------------


@sectors_app.command("assign")
def sectors_assign(
    sector: str = typer.Argument(..., help="Sector name"),
    symbol: str = typer.Argument(..., help="Ticker symbol to assign"),
) -> None:
    """Assign a symbol to a sector."""
    store.assign_symbol(sector, symbol)
    typer.echo(f"'{symbol.upper()}' assigned to '{sector}'.")


# ---------------------------------------------------------------------------
# sectors unassign
# ---------------------------------------------------------------------------


@sectors_app.command("unassign")
def sectors_unassign(
    symbol: str = typer.Argument(..., help="Ticker symbol to remove from its sector"),
) -> None:
    """Remove a symbol from its current sector."""
    store.unassign_symbol(symbol)
    typer.echo(f"'{symbol.upper()}' unassigned.")


# ---------------------------------------------------------------------------
# sectors stats
# ---------------------------------------------------------------------------


@sectors_app.command("stats")
def sectors_stats(
    brokers: Annotated[
        list[str],
        typer.Option("--broker", "-b", help="Broker to query (repeatable)"),
    ] = [],
) -> None:
    """Show sector allocation as a percentage of the total portfolio."""
    if not brokers:
        brokers = _detect_configured_brokers()
        if not brokers:
            err_console.print("No brokers specified or configured.")
            raise typer.Exit(code=1)

    broker_instances = _build_brokers(brokers)
    positions_by_broker: dict[str, list] = {}

    for broker in broker_instances:
        typer.echo(f"Fetching from {broker.name}…")
        try:
            positions_by_broker[broker.name] = broker.fetch_positions()
        except (ConnectionError, RuntimeError) as exc:
            err_console.print(f"[{broker.name}] {exc}")

    portfolio = pf.aggregate(positions_by_broker)
    sectors = store.load()
    snapshots = pf.sector_stats(portfolio, sectors)
    display.render_sector_stats(snapshots, portfolio.total_market_value)


if __name__ == "__main__":
    app()
