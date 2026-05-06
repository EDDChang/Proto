# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install (editable, with dev tools)
pip install -e ".[dev]"

# Run all tests
pytest

# Run a single test file
pytest tests/test_portfolio.py

# Run a single test by name
pytest tests/test_portfolio.py::test_sector_stats_percentages

# Lint
ruff check .

# Format
ruff format .
```

## Architecture

The app fetches positions from one or more brokers, aggregates them into a `Portfolio`, then computes sector allocations based on user-defined `Sector` groupings.

**Data flow:**
```
CLI (main.py)
  → BrokerBase.fetch_positions()   →  list[Position]
  → portfolio.aggregate()          →  Portfolio
  → portfolio.sector_stats()       →  list[SectorSnapshot]
  → display.render_*()             →  Rich table output
```

**Broker extension pattern** (`protofiler/brokers/`):
- `base.py` defines `BrokerBase` — one abstract method: `fetch_positions() -> list[Position]`
- `ib.py` and `sinopac.py` are the two current implementations
- `__init__.py` exports `BROKER_REGISTRY: dict[str, type]` — this is the only file to touch when registering a new broker
- The CLI resolves broker names through this registry; no other files need changes

**`portfolio.py` is pure** — no I/O, no side effects. `aggregate()` and `sector_stats()` take plain data and return plain data, making them straightforward to unit-test with fixture positions.

**Sector persistence** (`store.py`): sectors are stored as `~/.protofiler/sectors.json` — a flat `{name: [symbols]}` dict. `store.py` exposes `load / save / add_sector / remove_sector / assign_symbol / unassign_symbol`.

**Credentials** are read from environment variables (`.env` via `python-dotenv`). See `.env.example` for all required variable names per broker.
