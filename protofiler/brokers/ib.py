"""Interactive Brokers connector using ib_insync."""

from decimal import Decimal

import ib_insync

from protofiler.brokers.base import BrokerBase
from protofiler.config import get
from protofiler.models import AccountSummary, AssetType, Position

_SECTYPE_MAP: dict[str, AssetType] = {
    "STK": AssetType.STOCK,
    "FUT": AssetType.FUTURES,
    "OPT": AssetType.OPTIONS,
    "CASH": AssetType.CASH,
}


def _to_asset_type(sec_type: str) -> AssetType:
    return _SECTYPE_MAP.get(sec_type.upper(), AssetType.OTHER)


def _valid_price(value: float | None) -> float | None:
    """Return None for IB sentinel values: NaN and -1 both mean 'not available'."""
    if value is None:
        return None
    if value != value:  # NaN check
        return None
    if value < 0:
        return None
    return value


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

    def _connect(self) -> ib_insync.IB:
        ib = ib_insync.IB()
        ib.connect(self._host, self._port, clientId=self._client_id)
        return ib

    def fetch_account_summary(self) -> AccountSummary:
        ib = self._connect()
        try:
            values = ib.accountValues()
            index: dict[str, str] = {v.tag: v.value for v in values if v.currency != "BASE"}

            def dec(tag: str) -> Decimal:
                raw = index.get(tag, "0")
                try:
                    return Decimal(raw)
                except Exception:
                    return Decimal(0)

            return AccountSummary(
                broker=self.name,
                net_liquidation=dec("NetLiquidation"),
                total_cash=dec("TotalCashValue"),
                gross_position_value=dec("GrossPositionValue"),
                unrealized_pnl=dec("UnrealizedPnL"),
                currency=next((v.currency for v in values if v.tag == "NetLiquidation"), "USD"),
            )
        except OSError as exc:
            raise ConnectionError(
                f"Cannot connect to IB at {self._host}:{self._port} — {exc}"
            ) from exc
        finally:
            if ib.isConnected():
                ib.disconnect()

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

            # Fall back to delayed data (type 3) when live subscription is unavailable
            ib.reqMarketDataType(3)

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

        # Options are quoted per-share; multiply by contract multiplier to get
        # per-contract value so that market_value = quantity * market_price is correct.
        multiplier = Decimal(str(contract.multiplier)) if contract.multiplier else Decimal(1)

        # IB avgCost for options is already the total per-contract cost (premium × multiplier).
        # Normalise to per-share so our model stays consistent: value = qty × price.
        if contract.secType == "OPT":
            avg_cost_per_unit = avg_cost  # already per-contract total
        else:
            avg_cost_per_unit = avg_cost
            multiplier = Decimal(1)

        market_price = avg_cost_per_unit  # fallback if no market data
        ticker = price_map.get(contract.conId)
        if ticker:
            # Prefer last trade price, fall back to previous close
            raw = _valid_price(ticker.last) or _valid_price(ticker.close)
            if raw is not None:
                market_price = Decimal(str(raw)) * multiplier

        return Position(
            symbol=contract.localSymbol or contract.symbol,
            quantity=qty,
            avg_cost=avg_cost_per_unit,
            market_price=market_price,
            asset_type=_to_asset_type(contract.secType),
            broker=self.name,
            currency=contract.currency,
            name=contract.symbol,
        )
