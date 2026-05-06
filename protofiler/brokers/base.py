"""Abstract base class for broker connectors."""

from abc import ABC, abstractmethod
from typing import Optional

from protofiler.models import AccountSummary, Position


class BrokerBase(ABC):
    """All broker implementations must satisfy this interface."""

    @abstractmethod
    def fetch_positions(self) -> list[Position]:
        """Return all currently held positions from this broker.

        Raises:
            ConnectionError: if the broker API is unreachable.
            RuntimeError: for unexpected API errors.
        """
        ...

    def fetch_account_summary(self) -> Optional[AccountSummary]:
        """Return account-level figures (cash, margin, PnL).

        Returns None if the broker does not support account summaries.
        Brokers that support this should override this method.
        """
        return None

    @property
    @abstractmethod
    def name(self) -> str:
        """Short identifier for this broker (e.g. 'ib', 'sinopac')."""
        ...
