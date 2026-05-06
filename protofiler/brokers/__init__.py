"""Broker registry — maps string identifiers to broker classes.

To add a new broker:
1. Create a module in this package implementing BrokerBase.
2. Import the class here and add it to BROKER_REGISTRY.
"""

from protofiler.brokers.ib import IBBroker
from protofiler.brokers.sinopac import SinopacBroker

BROKER_REGISTRY: dict[str, type] = {
    "ib": IBBroker,
    "sinopac": SinopacBroker,
}

__all__ = ["BROKER_REGISTRY", "IBBroker", "SinopacBroker"]
