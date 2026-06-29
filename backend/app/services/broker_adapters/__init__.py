"""Broker adapter package — adapters for each supported broker type.

Auto-discovery: all non-abstract subclasses of BrokerAdapter in this package
are automatically registered via discover_adapters(). Each broker type should
have an adapter class with a class-level `broker_type` attribute matching its
key in the BROKER_TYPES registry.
"""

import importlib
import inspect
import logging
import pkgutil
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .base import BrokerAdapter

logger = logging.getLogger(__name__)

_ADAPTER_MODULES: dict[str, str] = {
    "paper": "app.services.broker_adapters.paper",
    "futu": "app.services.broker_adapters.futu",
    "webull_hk": "app.services.broker_adapters.webull_hk",
    "webull_us": "app.services.broker_adapters.webull_us",
    "moomoo": "app.services.broker_adapters.moomoo",
    "tiger": "app.services.broker_adapters.tiger",
    "interactive_brokers": "app.services.broker_adapters.interactive_brokers",
    "alpaca": "app.services.broker_adapters.alpaca",
    "binance": "app.services.broker_adapters.binance",
    "bybit": "app.services.broker_adapters.bybit",
    "okx": "app.services.broker_adapters.okx",
}


def get_adapter_module(broker_type: str) -> str | None:
    """Return the dotted module path for a given broker type."""
    return _ADAPTER_MODULES.get(broker_type)


def load_adapter_class(broker_type: str):
    """Dynamically import and return the adapter class for a broker type.

    Returns None if the module/class cannot be loaded.
    """
    module_path = get_adapter_module(broker_type)
    if module_path is None:
        logger.warning("No adapter module mapped for broker_type=%s", broker_type)
        return None

    try:
        module = importlib.import_module(module_path)
    except ImportError as exc:
        logger.warning(
            "Could not import adapter module %s for broker_type=%s: %s",
            module_path, broker_type, exc,
        )
        return None

    # Locate the adapter class in the module — it should be a subclass of
    # BrokerAdapter (imported lazily to avoid circular deps).
    from .base import BrokerAdapter as _Base  # noqa: N813

    for _name, _cls in inspect.getmembers(module, inspect.isclass):
        if _cls is _Base:
            continue
        if issubclass(_cls, _Base) and not inspect.isabstract(_cls):
            return _cls

    logger.warning(
        "No BrokerAdapter subclass found in module %s for broker_type=%s",
        module_path, broker_type,
    )
    return None
