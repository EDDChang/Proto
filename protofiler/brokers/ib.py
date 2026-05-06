"""Interactive Brokers connector using ib_insync."""

from decimal import Decimal

import ib_insync

from protofiler.brokers.base import BrokerBase
from protofiler.config import get
from protofiler.models import AssetType, Position

_SECTYPE_MAP: dict[str, AssetType] = {
    "STK": AssetType.STOCK,
    "FUT": AssetType.FUTURES,
    "OPT": AssetType.OPTIONS,
    "CASH": AssetType.CASH,
}


def _to_asset_type(sec_type: str) -> AssetType:
    return _SECTYPE_MAP.get(sec_type.upper(), AssetType.OTHER)


def _nan_safe(value: float | None) -> float | None:
    """Return None for NaN floats that ib_insync uses as 'not available'."""
    if value is None:
        return None
    return None if value != value else value


class IBBroker(BrokerBase):
    """Connects to TWS / IB Gateway via the ib_insync library.

    Config (env var or ~/.protofiler/config.toml [ib] section):
        host       — TWS/Gateway host (default: 127.0.0.1)
        port       — TWS/Gateway port (default: 7497 for paper, 7496 for live)
        client_id  — unique client ID (default: 1)
    """

    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
        client_id: int | None = None,
    ) -> None:
        self._host = host or get("ib", "host", "127.0.0.1")
        self._port = int(port or get("ib", "port", 7497))
        self._client_id = int(client_id or get("ib", "client_id", 1))

    @property
    def name(self) -> str:
        return "ib"

    def fetch_positions(self) -> list[Position]:
        ib = ib_insync.IB()
        try:
            ib.connect(self._host, self._port, clientId=self._client_id)

            raw_positions = ib.positions()
            if not raw_positions:
                return []

            # Qualify contracts so conId is populated (required for reqTickers)
            contracts = [pos.contract for pos in raw_positions]
            ib.qualifyContracts(*contracts)

            # Single batch snapshot request — much faster than one-per-position
            tickers = ib.reqTickers(*contracts)
            price_map: dict[int, ib_insync.Ticker] = {
                t.contract.conId: t for t in tickers
            }

            return [self._map_position(pos, price_map) for pos in raw_positions]

        except OSError as exc:
            raise ConnectionError(
                f"Cannot connect to IB at {self._host}:{self._port} — {exc}"
            ) from exc
        finally:
            if ib.isConnected():
                ib.disconnect()

    def _map_position(
        self,
        pos: ib_insync.Position,
        price_map: dict[int, ib_insync.Ticker],
    ) -> Position:
        contract = pos.contract
        avg_cost = Decimal(str(pos.avgCost))
        qty = Decimal(str(pos.position))

        market_price = avg_cost  # fallback if no market data
        ticker = price_map.get(contract.conId)
        if ticker:
            # Prefer last trade price, fall back to previous close
            price = _nan_safe(ticker.last) or _nan_safe(ticker.close)
            if price is not None:
                market_price = Decimal(str(price))

        return Position(
            symbol=contract.localSymbol or contract.symbol,
            quantity=qty,
            avg_cost=avg_cost,
            market_price=market_price,
            asset_type=_to_asset_type(contract.secType),
            broker=self.name,
            currency=contract.currency,
            name=contract.symbol,
        )
