"""Sinopac (永豐證券/期貨) connector using the shioaji SDK."""

import os
from decimal import Decimal

import shioaji as sj

from protofiler.brokers.base import BrokerBase
from protofiler.models import AssetType, Position


def _futures_or_options(contract: sj.contracts.BaseContract) -> AssetType:
    category = getattr(contract, "category", "") or ""
    if "option" in category.lower() or "opt" in category.lower():
        return AssetType.OPTIONS
    return AssetType.FUTURES


class SinopacBroker(BrokerBase):
    """Connects to Sinopac via the shioaji SDK.

    Environment variables:
        SINOPAC_API_KEY     — API key from the Sinopac developer portal
        SINOPAC_SECRET_KEY  — Secret key
        SINOPAC_CA_PATH     — Path to the CA certificate file (for futures)
        SINOPAC_CA_PASSWD   — CA certificate password
        SINOPAC_PERSON_ID   — National ID / person ID for CA authentication
    """

    def __init__(
        self,
        api_key: str | None = None,
        secret_key: str | None = None,
        ca_path: str | None = None,
        ca_passwd: str | None = None,
        person_id: str | None = None,
        simulation: bool = False,
    ) -> None:
        self._api_key = api_key or os.environ.get("SINOPAC_API_KEY", "")
        self._secret_key = secret_key or os.environ.get("SINOPAC_SECRET_KEY", "")
        self._ca_path = ca_path or os.environ.get("SINOPAC_CA_PATH", "")
        self._ca_passwd = ca_passwd or os.environ.get("SINOPAC_CA_PASSWD", "")
        self._person_id = person_id or os.environ.get("SINOPAC_PERSON_ID", "")
        self._simulation = simulation

    @property
    def name(self) -> str:
        return "sinopac"

    def fetch_positions(self) -> list[Position]:
        api = sj.Shioaji(simulation=self._simulation)
        try:
            api.login(self._api_key, self._secret_key)
            if self._ca_path:
                api.activate_ca(
                    ca_path=self._ca_path,
                    ca_passwd=self._ca_passwd,
                    person_id=self._person_id,
                )

            positions: list[Position] = []
            positions.extend(self._fetch_stock_positions(api))
            positions.extend(self._fetch_futures_positions(api))
            return positions
        except Exception as exc:
            raise RuntimeError(f"Sinopac API error: {exc}") from exc
        finally:
            try:
                api.logout()
            except Exception:
                pass

    def _fetch_stock_positions(self, api: sj.Shioaji) -> list[Position]:
        results: list[Position] = []
        for item in api.list_positions(api.stock_account):
            contract = api.Contracts.Stocks.get(item.code)
            market_price = Decimal(str(item.last_price)) if item.last_price else Decimal(str(item.price))
            results.append(
                Position(
                    symbol=item.code,
                    quantity=Decimal(str(item.quantity)),
                    avg_cost=Decimal(str(item.price)),
                    market_price=market_price,
                    asset_type=AssetType.STOCK,
                    broker=self.name,
                    currency="TWD",
                    name=getattr(contract, "name", None),
                )
            )
        return results

    def _fetch_futures_positions(self, api: sj.Shioaji) -> list[Position]:
        results: list[Position] = []
        if not api.futopt_account:
            return results

        for item in api.list_positions(api.futopt_account):
            contract = api.Contracts.Futures.get(item.code) or api.Contracts.Options.get(item.code)
            asset_type = _futures_or_options(contract) if contract else AssetType.FUTURES
            results.append(
                Position(
                    symbol=item.code,
                    quantity=Decimal(str(item.quantity)),
                    avg_cost=Decimal(str(item.price)),
                    market_price=Decimal(str(item.last_price)) if item.last_price else Decimal(str(item.price)),
                    asset_type=asset_type,
                    broker=self.name,
                    currency="TWD",
                    name=getattr(contract, "name", None),
                )
            )
        return results
