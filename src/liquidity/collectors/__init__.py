"""Data collectors for Global Liquidity Monitor.

This module provides the base collector pattern with resilience (retry + circuit breaker)
and a registry for collector discovery.
"""

from liquidity.collectors.base import (
    BaseCollector,
    CollectorCircuitOpenError,
    CollectorError,
    CollectorFetchError,
)
from liquidity.collectors.fred import SERIES_MAP, FredCollector
from liquidity.collectors.registry import CollectorRegistry, registry
from liquidity.collectors.yahoo import SYMBOLS as YAHOO_SYMBOLS
from liquidity.collectors.yahoo import YahooCollector

__all__ = [
    # Base
    "BaseCollector",
    "CollectorError",
    "CollectorFetchError",
    "CollectorCircuitOpenError",
    # Registry
    "CollectorRegistry",
    "registry",
    # FRED
    "FredCollector",
    "SERIES_MAP",
    # Yahoo
    "YahooCollector",
    "YAHOO_SYMBOLS",
]
