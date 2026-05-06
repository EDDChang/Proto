"""Abstract base class for broker connectors."""

from abc import ABC, abstractmethod

from protofiler.models import Position


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

    @property
    @abstractmethod
    def name(self) -> str:
        """Short identifier for this broker (e.g. 'ib', 'sinopac')."""
        ...
