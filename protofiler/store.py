"""Local JSON persistence for sector definitions.

Sectors are stored in ~/.protofiler/sectors.json:
    { "Tech": ["AAPL", "MSFT"], "Energy": ["XOM"] }
"""

import json
from pathlib import Path

from protofiler.models import Sector

_DATA_DIR = Path.home() / ".protofiler"
_SECTORS_FILE = _DATA_DIR / "sectors.json"


def _ensure_dir() -> None:
    _DATA_DIR.mkdir(parents=True, exist_ok=True)


def load() -> list[Sector]:
    """Return all persisted sectors, or an empty list if none exist."""
    if not _SECTORS_FILE.exists():
        return []
    raw: dict[str, list[str]] = json.loads(_SECTORS_FILE.read_text())
    return [Sector(name=name, symbols=symbols) for name, symbols in raw.items()]


def save(sectors: list[Sector]) -> None:
    """Overwrite the sectors file with the provided list."""
    _ensure_dir()
    data = {s.name: s.symbols for s in sectors}
    _SECTORS_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False))


def add_sector(name: str) -> list[Sector]:
    """Create a new empty sector if it does not already exist."""
    sectors = load()
    if any(s.name == name for s in sectors):
        return sectors
    sectors.append(Sector(name=name))
    save(sectors)
    return sectors


def remove_sector(name: str) -> list[Sector]:
    """Delete a sector by name."""
    sectors = [s for s in load() if s.name != name]
    save(sectors)
    return sectors


def assign_symbol(sector_name: str, symbol: str) -> list[Sector]:
    """Add a symbol to a sector, creating the sector if necessary."""
    sectors = load()
    symbol = symbol.upper()
    for s in sectors:
        if s.name == sector_name:
            if symbol not in s.symbols:
                s.symbols.append(symbol)
            save(sectors)
            return sectors
    # Sector does not exist yet — create it
    sectors.append(Sector(name=sector_name, symbols=[symbol]))
    save(sectors)
    return sectors


def unassign_symbol(symbol: str) -> list[Sector]:
    """Remove a symbol from whichever sector it belongs to."""
    symbol = symbol.upper()
    sectors = load()
    for s in sectors:
        if symbol in s.symbols:
            s.symbols.remove(symbol)
    save(sectors)
    return sectors
