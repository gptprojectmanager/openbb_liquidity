"""Bank of Canada collector using Valet API.

Fetches BoC balance sheet data via the official Valet API (no auth required).
"""

import logging
from datetime import datetime
from typing import Any

import httpx
import pandas as pd

from liquidity.collectors.base import BaseCollector
from liquidity.collectors.registry import registry
from liquidity.config import Settings, get_settings

logger = logging.getLogger(__name__)

# BoC series mapping
SERIES_MAP: dict[str, str] = {
    "boc_total_assets": "V36610",  # Total assets - Weekly, Millions CAD
    "boc_total_liabilities": "V36624",  # Total liabilities and equity
}

UNIT_MAP: dict[str, str] = {
    "V36610": "millions_cad",
    "V36624": "millions_cad",
}

BOC_VALET_BASE_URL = "https://www.bankofcanada.ca/valet/observations"


class BOCCollector(BaseCollector[pd.DataFrame]):
    """Bank of Canada collector using Valet API."""

    SERIES_MAP = SERIES_MAP

    def __init__(
        self,
        name: str = "boc",
        settings: Settings | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize BoC collector.

        Args:
            name: Collector name for circuit breaker.
            settings: Optional settings override.
            **kwargs: Additional arguments passed to BaseCollector.
        """
        super().__init__(name=name, settings=settings, **kwargs)
        self._settings = settings or get_settings()

    async def collect(
        self,
        series_id: str = "V36610",
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> pd.DataFrame:
        """Collect BoC data via Valet API.

        Args:
            series_id: Valet series ID to fetch. Defaults to V36610 (total assets).
            start_date: Start date for data fetch.
            end_date: End date for data fetch.

        Returns:
            DataFrame with columns: timestamp, series_id, source, value, unit

        Raises:
            CollectorFetchError: If data fetch fails after retries.
        """

        async def _fetch() -> pd.DataFrame:
            return await self._fetch_async(series_id, start_date, end_date)

        return await self.fetch_with_retry(_fetch)

    async def _fetch_async(
        self,
        series_id: str,
        start_date: datetime | None,
        end_date: datetime | None,
    ) -> pd.DataFrame:
        """Async fetch using httpx.

        Args:
            series_id: Valet series ID.
            start_date: Start date.
            end_date: End date.

        Returns:
            Normalized DataFrame.
        """
        url = f"{BOC_VALET_BASE_URL}/{series_id}/json"

        params: dict[str, str] = {}
        if start_date:
            params["start_date"] = start_date.strftime("%Y-%m-%d")
        if end_date:
            params["end_date"] = end_date.strftime("%Y-%m-%d")

        logger.info("Fetching BoC series %s from Valet API", series_id)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params if params else None)
            response.raise_for_status()
            data = response.json()

        return self._parse_response(data, series_id)

    def _parse_response(self, data: dict[str, Any], series_id: str) -> pd.DataFrame:
        """Parse Valet API JSON response.

        Args:
            data: JSON response from Valet API.
            series_id: Series ID for column naming.

        Returns:
            Normalized DataFrame with standard columns.
        """
        observations = data.get("observations", [])

        if not observations:
            logger.warning("No observations returned from BoC for series %s", series_id)
            return pd.DataFrame(
                columns=["timestamp", "series_id", "source", "value", "unit"]
            )

        records = []
        for obs in observations:
            date_str = obs.get("d")  # Date key
            value = obs.get(series_id, {}).get("v")  # Value nested under series_id

            if date_str and value is not None:
                records.append(
                    {
                        "timestamp": pd.to_datetime(date_str),
                        "series_id": series_id,
                        "source": "boc",
                        "value": float(value),
                        "unit": UNIT_MAP.get(series_id, "unknown"),
                    }
                )

        df = pd.DataFrame(records)
        df = df.sort_values("timestamp").reset_index(drop=True)

        logger.info("Fetched %d data points from BoC Valet API", len(df))

        return df[["timestamp", "series_id", "source", "value", "unit"]]

    async def collect_total_assets(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> pd.DataFrame:
        """Convenience method to collect BoC total assets.

        Args:
            start_date: Start date for data fetch.
            end_date: End date for data fetch.

        Returns:
            DataFrame with BoC total assets data.
        """
        return await self.collect("V36610", start_date, end_date)


# Register collector
registry.register("boc", BOCCollector)
