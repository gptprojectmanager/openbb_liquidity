"""Base collector with resilience patterns (retry + circuit breaker).

This module provides the abstract base class for all data collectors with:
- Exponential backoff retry via tenacity
- Circuit breaker pattern via purgatory
- Standardized error handling and logging
"""

import logging
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from typing import Any, Generic, TypeVar

import httpx
from purgatory import AsyncCircuitBreakerFactory
from tenacity import (
    RetryError,
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from liquidity.config import Settings, get_settings

logger = logging.getLogger(__name__)

# Type variable for collector output
T = TypeVar("T")


class CollectorError(Exception):
    """Base exception for collector errors."""

    pass


class CollectorFetchError(CollectorError):
    """Error during data fetching."""

    pass


class CollectorCircuitOpenError(CollectorError):
    """Circuit breaker is open, requests are being rejected."""

    pass


class BaseCollector(ABC, Generic[T]):
    """Abstract base class for data collectors with resilience patterns.

    Provides:
    - Exponential backoff retry (1-60s, 5 attempts by default)
    - Circuit breaker integration
    - Standardized logging for retries and failures

    Subclasses must implement the `collect()` method.

    Example:
        class FredCollector(BaseCollector[pd.DataFrame]):
            async def collect(self, symbols: list[str]) -> pd.DataFrame:
                async def _fetch():
                    # Actual fetch logic
                    return await self._fetch_from_api(symbols)
                return await self.fetch_with_retry(_fetch)
    """

    def __init__(
        self,
        name: str,
        circuit_breaker_factory: AsyncCircuitBreakerFactory | None = None,
        settings: Settings | None = None,
    ) -> None:
        """Initialize the collector.

        Args:
            name: Unique name for this collector (used for circuit breaker).
            circuit_breaker_factory: Optional circuit breaker factory.
                If not provided, a new one will be created from settings.
            settings: Optional settings override. Uses global settings if not provided.
        """
        self.name = name
        self._settings = settings or get_settings()
        self._cb_factory = circuit_breaker_factory or self._create_cb_factory()

    def _create_cb_factory(self) -> AsyncCircuitBreakerFactory:
        """Create a circuit breaker factory from settings."""
        return AsyncCircuitBreakerFactory(
            default_threshold=self._settings.circuit_breaker.threshold,
            default_ttl=self._settings.circuit_breaker.ttl,
        )

    def _create_retry_decorator(
        self,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Create a retry decorator configured from settings.

        Returns:
            Configured retry decorator with exponential backoff.
        """
        return retry(
            stop=stop_after_attempt(self._settings.retry.max_attempts),
            wait=wait_exponential(
                multiplier=self._settings.retry.multiplier,
                min=self._settings.retry.min_wait,
                max=self._settings.retry.max_wait,
            ),
            retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError)),
            before_sleep=before_sleep_log(logger, logging.WARNING),
            reraise=True,
        )

    async def fetch_with_retry(
        self,
        fetch_fn: Callable[[], Awaitable[T]],
        breaker_name: str | None = None,
    ) -> T:
        """Execute a fetch function with retry and circuit breaker protection.

        This method wraps an async fetch function with:
        1. Exponential backoff retry for transient errors
        2. Circuit breaker to prevent cascading failures

        Args:
            fetch_fn: Async function that performs the actual data fetching.
            breaker_name: Optional circuit breaker name. Defaults to collector name.

        Returns:
            The result of the fetch function.

        Raises:
            CollectorFetchError: If all retries are exhausted.
            CollectorCircuitOpenError: If the circuit breaker is open.
        """
        breaker_name = breaker_name or self.name

        retry_decorator = self._create_retry_decorator()

        @retry_decorator
        async def _fetch_with_retry() -> T:
            breaker = await self._cb_factory.get_breaker(breaker_name)
            async with breaker:
                return await fetch_fn()

        try:
            result: T = await _fetch_with_retry()
            return result
        except RetryError as e:
            logger.error(
                "Collector %s: All retry attempts exhausted",
                self.name,
                exc_info=True,
            )
            raise CollectorFetchError(
                f"Failed to fetch data after {self._settings.retry.max_attempts} attempts"
            ) from e
        except Exception as e:
            # Check if it's a circuit breaker error
            if "circuit" in str(e).lower() and "open" in str(e).lower():
                logger.warning(
                    "Collector %s: Circuit breaker is open, rejecting request",
                    self.name,
                )
                raise CollectorCircuitOpenError(
                    f"Circuit breaker for {breaker_name} is open"
                ) from e
            raise

    @abstractmethod
    async def collect(self, *args: Any, **kwargs: Any) -> T:
        """Collect data from the source.

        This method must be implemented by subclasses. It should use
        `fetch_with_retry()` to wrap the actual data fetching logic.

        Returns:
            Collected data of type T.

        Raises:
            CollectorError: If data collection fails.
        """
        pass

    def __repr__(self) -> str:
        """Return string representation of the collector."""
        return f"{self.__class__.__name__}(name={self.name!r})"
