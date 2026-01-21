"""Collector registry for discovery and management.

Provides a singleton registry pattern for registering and retrieving collectors.
"""

import logging
from typing import Any

from liquidity.collectors.base import BaseCollector

logger = logging.getLogger(__name__)


class CollectorRegistry:
    """Registry for data collectors.

    Provides a centralized registry for collector classes, enabling:
    - Dynamic collector discovery
    - Lazy instantiation
    - Plugin-style architecture for future extensions

    Example:
        # Register a collector class
        registry.register("fred", FredCollector)

        # Get and instantiate a collector
        collector_cls = registry.get("fred")
        collector = collector_cls(name="fred_balance_sheet")

        # List all registered collectors
        for name in registry.list_collectors():
            print(f"Available: {name}")
    """

    def __init__(self) -> None:
        """Initialize an empty collector registry."""
        self._collectors: dict[str, type[BaseCollector[Any]]] = {}

    def register(
        self,
        name: str,
        collector_class: type[BaseCollector[Any]],
        *,
        force: bool = False,
    ) -> None:
        """Register a collector class.

        Args:
            name: Unique name for the collector.
            collector_class: The collector class to register.
            force: If True, allow overwriting existing registrations.

        Raises:
            ValueError: If name is already registered and force is False.
            TypeError: If collector_class is not a BaseCollector subclass.
        """
        if not isinstance(collector_class, type) or not issubclass(
            collector_class, BaseCollector
        ):
            raise TypeError(
                f"collector_class must be a BaseCollector subclass, got {type(collector_class)}"
            )

        if name in self._collectors and not force:
            raise ValueError(
                f"Collector '{name}' is already registered. Use force=True to overwrite."
            )

        self._collectors[name] = collector_class
        logger.debug("Registered collector: %s -> %s", name, collector_class.__name__)

    def unregister(self, name: str) -> None:
        """Unregister a collector.

        Args:
            name: Name of the collector to unregister.

        Raises:
            KeyError: If the collector is not registered.
        """
        if name not in self._collectors:
            raise KeyError(f"Collector '{name}' is not registered")

        del self._collectors[name]
        logger.debug("Unregistered collector: %s", name)

    def get(self, name: str) -> type[BaseCollector[Any]]:
        """Get a registered collector class.

        Args:
            name: Name of the collector to retrieve.

        Returns:
            The registered collector class.

        Raises:
            KeyError: If the collector is not registered.
        """
        if name not in self._collectors:
            available = ", ".join(self._collectors.keys()) or "none"
            raise KeyError(
                f"Collector '{name}' is not registered. Available: {available}"
            )

        return self._collectors[name]

    def list_collectors(self) -> list[str]:
        """List all registered collector names.

        Returns:
            List of registered collector names, sorted alphabetically.
        """
        return sorted(self._collectors.keys())

    def is_registered(self, name: str) -> bool:
        """Check if a collector is registered.

        Args:
            name: Name of the collector to check.

        Returns:
            True if the collector is registered, False otherwise.
        """
        return name in self._collectors

    def clear(self) -> None:
        """Clear all registered collectors.

        Useful for testing or resetting the registry state.
        """
        self._collectors.clear()
        logger.debug("Cleared collector registry")

    def __len__(self) -> int:
        """Return the number of registered collectors."""
        return len(self._collectors)

    def __contains__(self, name: str) -> bool:
        """Check if a collector name is registered."""
        return name in self._collectors

    def __repr__(self) -> str:
        """Return string representation of the registry."""
        collectors = ", ".join(self._collectors.keys())
        return f"CollectorRegistry([{collectors}])"


# Global singleton registry instance
registry = CollectorRegistry()
