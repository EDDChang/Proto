"""Interactive Brokers connector using ib_insync."""

import os
from decimal import Decimal

import ib_insync

from protofiler.brokers.base import BrokerBase
from protofiler.models import AssetType, Position

# Mapping from IB secType string to our AssetType enum
_SECTYPE_MAP: dict[str, AssetType] = {
    "STK": AssetType.STOCK,
    "FUT": AssetType.FUTURES,
    "OPT": AssetType.OPTIONS,
    "CASH": AssetType.CASH,
}


def _to_asset_type(sec_type: str) -> AssetType:
    return _SECTYPE_MAP.get(sec_type.upper(), AssetType.OTHER)


class IBBroker(BrokerBase):
    """Connects to TWS / IB Gateway via the ib_insync library.

    Environment variables:
        IB_HOST  — TWS/Gateway host (default: 127.0.0.1)
        IB_PORT  — TWS/Gateway port (default: 7497 for paper, 7496 for live)
        IB_CLIENT_ID — unique client ID (default: 1)
    """

    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
        client_id: int | None = None,
    ) -> None:
        self._host = host or os.environ.get("IB_HOST", "127.0.0.1")
        self._port = int(port or os.environ.get("IB_PORT", 7497))
        self._client_id = int(client_id or os.environ.get("IB_CLIENT_ID", 1))

    @property
    def name(self) -> str:
        return "ib"

    def fetch_positions(self) -> list[Position]:
        ib = ib_insync.IB()
        try:
            ib.connect(self._host, self._port, clientId=self._client_id)
            raw_positions = ib.positions()
            return [self._map_position(p) for p in raw_positions]
        except OSError as exc:
            raise ConnectionError(
                f"Cannot connect to IB at {self._host}:{self._port} — {exc}"
            ) from exc
        finally:
            if ib.isConnected():
                ib.disconnect()

    def _map_position(self, pos: ib_insync.Position) -> Position:
        contract = pos.contract
        avg_cost = Decimal(str(pos.avgCost))
        qty = Decimal(str(pos.position))

        # IB does not provide live market price in the positions snapshot;
        # request market data for each contract to get the last price.
        ib = ib_insync.IB()
        market_price = avg_cost  # fallback
        try:
            ib.connect(self._host, self._port, clientId=self._client_id + 100)
            ticker = ib.reqMktData(contract, "", True, False)
            ib_insync.util.sleep(1)
            if ticker.last and ticker.last == ticker.last:  # NaN check
                market_price = Decimal(str(ticker.last))
            elif ticker.close and ticker.close == ticker.close:
                market_price = Decimal(str(ticker.close))
        except Exception:
            pass
        finally:
            if ib.isConnected():
                ib.disconnect()

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
