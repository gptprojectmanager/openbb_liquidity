"""Swiss National Bank collector via data portal CSV.

SNB publishes balance sheet data at https://data.snb.ch
Direct CSV download with no authentication required.
"""

import io
import logging
from datetime import datetime
from typing import Any

import httpx
import pandas as pd

from liquidity.collectors.base import BaseCollector, CollectorFetchError
from liquidity.collectors.registry import registry
from liquidity.config import Settings, get_settings

logger = logging.getLogger(__name__)

# SNB data portal endpoint
SNB_DATA_URL = "https://data.snb.ch/api/cube/snbbipo/data/csv/en"

UNIT_MAP: dict[str, str] = {
    "SNB_TOTAL_ASSETS": "millions_chf",
}


class SNBCollector(BaseCollector[pd.DataFrame]):
    """Swiss National Bank collector via data portal CSV."""

    SERIES_MAP: dict[str, str] = {
        "snb_total_assets": "SNB_TOTAL_ASSETS",
    }

    def __init__(
        self,
        name: str = "snb",
        settings: Settings | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(name=name, settings=settings, **kwargs)
        self._settings = settings or get_settings()

    async def collect(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> pd.DataFrame:
        """Collect SNB balance sheet data."""

        async def _fetch() -> pd.DataFrame:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(SNB_DATA_URL)
                response.raise_for_status()
                return self._parse_csv(response.text, start_date, end_date)

        try:
            return await self.fetch_with_retry(_fetch)
        except Exception as e:
            logger.error("SNB fetch failed: %s", e)
            raise CollectorFetchError(f"SNB data fetch failed: {e}") from e

    def _parse_csv(
        self,
        csv_text: str,
        start_date: datetime | None,
        end_date: datetime | None,
    ) -> pd.DataFrame:
        """Parse SNB CSV to standard format.

        SNB CSV structure:
        - Metadata lines at top (CubeId, PublishingDate)
        - Empty line, then data header
        - Semicolon separated
        - Column 'D0' contains item codes
        - Code 'T0' = Total (total assets)
        - Date column is 'Date' in YYYY-MM format
        - Value column is 'Value'
        """
        # SNB CSV has metadata lines before the actual data
        # Skip lines until we find the header row with "Date";"D0";"Value"
        lines = csv_text.split("\n")
        header_idx = None
        for i, line in enumerate(lines):
            if line.startswith('"Date";"D0"'):
                header_idx = i
                break

        if header_idx is None:
            raise CollectorFetchError("Could not find data header in SNB CSV")

        # Read CSV starting from the header row
        data_text = "\n".join(lines[header_idx:])
        df = pd.read_csv(io.StringIO(data_text), sep=";")

        logger.debug("SNB CSV columns: %s", df.columns.tolist())

        # Filter for Total (T0) row - this is the total assets
        if "D0" not in df.columns:
            raise CollectorFetchError(
                f"Expected 'D0' column in SNB data. Got: {df.columns.tolist()}"
            )

        total_df = df[df["D0"] == "T0"].copy()

        if total_df.empty:
            raise CollectorFetchError("No total assets (T0) found in SNB data")

        # Parse dates (YYYY-MM format)
        total_df["timestamp"] = pd.to_datetime(total_df["Date"], format="%Y-%m")

        # Filter by date range if specified
        if start_date:
            total_df = total_df[total_df["timestamp"] >= pd.to_datetime(start_date)]
        if end_date:
            total_df = total_df[total_df["timestamp"] <= pd.to_datetime(end_date)]

        # Normalize to standard format
        result = pd.DataFrame(
            {
                "timestamp": total_df["timestamp"],
                "series_id": "SNB_TOTAL_ASSETS",
                "source": "snb",
                "value": total_df["Value"].astype(float),
                "unit": "millions_chf",
            }
        )

        result = result.sort_values("timestamp").reset_index(drop=True)
        logger.info("Fetched %d SNB data points", len(result))

        return result

    async def collect_total_assets(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> pd.DataFrame:
        """Convenience method to collect SNB total assets."""
        return await self.collect(start_date, end_date)


# Register collector
registry.register("snb", SNBCollector)
