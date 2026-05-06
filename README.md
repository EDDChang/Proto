# Protofiler

A multi-broker portfolio profiler that fetches current holdings and computes sector allocation.

## Features

- Connects to **Interactive Brokers** (via `ib_insync`) and **Sinopac** / 永豐證券期貨 (via `shioaji`)
- Supports stocks, futures, and options
- User-defined sector/cluster groups with persistent local storage
- Sector allocation table with market value and % of portfolio
- Designed for easy extension to additional brokers

## Installation

```bash
pip install -e ".[dev]"
```

## Configuration

Credentials are stored in `~/.protofiler/config.toml` — outside the repository so they are never accidentally committed.

```toml
# ~/.protofiler/config.toml

[ib]
host = "127.0.0.1"
port = 7497        # 7497 = paper trading, 7496 = live
client_id = 1

[sinopac]
api_key = "your_api_key"
secret_key = "your_secret_key"
ca_path = "/path/to/ca.pfx"   # required for futures
ca_passwd = "your_ca_password"
person_id = "A123456789"
```

Environment variables (e.g. `IB_HOST`, `SINOPAC_API_KEY`) take precedence over the config file if both are set. See `.env.example` for the full list of variable names.

## Usage

### Fetch positions

```bash
# auto-detect configured brokers
protofiler fetch

# specify brokers explicitly
protofiler fetch --broker ib --broker sinopac
```

### Manage sectors

```bash
protofiler sectors list
protofiler sectors add Tech
protofiler sectors assign Tech AAPL
protofiler sectors assign Tech MSFT
protofiler sectors unassign MSFT
protofiler sectors remove Tech
```

### Sector allocation stats

```bash
protofiler sectors stats
protofiler sectors stats --broker ib
```

## Adding a New Broker

1. Create `protofiler/brokers/mybroker.py` implementing `BrokerBase`:

```python
from protofiler.brokers.base import BrokerBase
from protofiler.models import Position

class MyBroker(BrokerBase):
    @property
    def name(self) -> str:
        return "mybroker"

    def fetch_positions(self) -> list[Position]:
        ...
```

2. Register it in `protofiler/brokers/__init__.py`:

```python
from protofiler.brokers.mybroker import MyBroker

BROKER_REGISTRY = {
    ...,
    "mybroker": MyBroker,
}
```

## Running Tests

```bash
pytest
```

## Project Structure

```
protofiler/
├── protofiler/
│   ├── models.py         # Pydantic data models
│   ├── portfolio.py      # Aggregation + sector analytics (pure functions)
│   ├── store.py          # JSON persistence for sector definitions
│   ├── display.py        # Rich terminal rendering
│   ├── main.py           # Typer CLI entry point
│   └── brokers/
│       ├── base.py       # Abstract broker interface
│       ├── ib.py         # Interactive Brokers
│       └── sinopac.py    # Sinopac 永豐
└── tests/
    ├── conftest.py
    ├── test_portfolio.py
    └── test_store.py
```
