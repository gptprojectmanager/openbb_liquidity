"""FRED collector for Fed balance sheet and macro data.

Fetches economic data from FRED (Federal Reserve Economic Data) via OpenBB SDK:
- WALCL: Fed Total Assets
- WLRRAL: Reverse Repo (RRP)
- WDTGAL: Treasury General Account (TGA)
- WRESBAL: Bank Reserves
- SOFR: Secured Overnight Financing Rate

Implements the Hayes Net Liquidity formula:
Net Liquidity = WALCL - WLRRAL - WDTGAL
"""

import asyncio
import logging
from datetime import UTC, datetime, timedelta
from typing import Any

import pandas as pd
from openbb import obb

from liquidity.collectors.base import BaseCollector, CollectorFetchError
from liquidity.collectors.registry import registry
from liquidity.config import Settings, get_settings

logger = logging.getLogger(__name__)

# FRED series mapping
# Keys are internal names, values are FRED series IDs
SERIES_MAP: dict[str, str] = {
    "fed_total_assets": "WALCL",  # Fed Total Assets (millions USD, weekly)
    "rrp": "WLRRAL",  # Reverse Repo (billions USD, weekly)
    "tga": "WDTGAL",  # Treasury General Account (billions USD, weekly)
    "bank_reserves": "WRESBAL",  # Reserve Balances (millions USD, biweekly)
    "sofr": "SOFR",  # Secured Overnight Financing Rate (percent, daily)
}

# Unit conversions for standardization (all to millions USD)
UNIT_MAP: dict[str, str] = {
    "WALCL": "millions_usd",
    "WLRRAL": "billions_usd",
    "WDTGAL": "billions_usd",
    "WRESBAL": "millions_usd",
    "SOFR": "percent",
}


class FredCollector(BaseCollector[pd.DataFrame]):
    """FRED data collector using OpenBB SDK.

    Fetches Fed balance sheet data and calculates Net Liquidity (Hayes formula).

    Example:
        collector = FredCollector()
        df = await collector.collect(["WALCL", "WLRRAL", "WDTGAL"])

        # Calculate Net Liquidity
        net_liq = FredCollector.calculate_net_liquidity(df)
    """

    SERIES_MAP = SERIES_MAP

    def __init__(
        self,
        name: str = "fred",
        settings: Settings | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize FRED collector.

        Args:
            name: Collector name for circuit breaker.
            settings: Optional settings override.
            **kwargs: Additional arguments passed to BaseCollector.
        """
        super().__init__(name=name, settings=settings, **kwargs)
        self._settings = settings or get_settings()

        # Set OpenBB FRED API key if available
        api_key = self._settings.fred_api_key.get_secret_value()
        if api_key:
            obb.user.credentials.fred_api_key = api_key
            logger.debug("FRED API key configured from settings")

    async def collect(
        self,
        symbols: list[str] | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> pd.DataFrame:
        """Collect FRED series data.

        Args:
            symbols: List of FRED series IDs to fetch. Defaults to all balance sheet series.
            start_date: Start date for data fetch. Defaults to 30 days ago.
            end_date: End date for data fetch. Defaults to today.

        Returns:
            DataFrame with columns: timestamp, series_id, source, value, unit

        Raises:
            CollectorFetchError: If data fetch fails after retries.
        """
        if symbols is None:
            # Default to balance sheet series (exclude SOFR)
            symbols = ["WALCL", "WLRRAL", "WDTGAL", "WRESBAL"]

        if start_date is None:
            start_date = datetime.now(UTC) - timedelta(days=30)

        if end_date is None:
            end_date = datetime.now(UTC)

        async def _fetch() -> pd.DataFrame:
            # OpenBB is synchronous, wrap in thread
            return await asyncio.to_thread(
                self._fetch_sync, symbols, start_date, end_date
            )

        try:
            return await self.fetch_with_retry(_fetch)
        except Exception as e:
            logger.error("FRED fetch failed: %s", e)
            raise CollectorFetchError(f"FRED data fetch failed: {e}") from e

    def _fetch_sync(
        self,
        symbols: list[str],
        start_date: datetime,
        end_date: datetime,
    ) -> pd.DataFrame:
        """Synchronous fetch implementation using OpenBB.

        Args:
            symbols: FRED series IDs.
            start_date: Start date.
            end_date: End date.

        Returns:
            Normalized DataFrame with timestamp, series_id, source, value, unit columns.
        """
        logger.info("Fetching FRED series: %s", symbols)

        # Fetch data using OpenBB
        result = obb.economy.fred_series(  # type: ignore[union-attr]
            symbol=",".join(symbols),
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d"),
            provider="fred",
        )

        # Convert to DataFrame
        df = result.to_df()

        if df.empty:
            logger.warning("No data returned from FRED for symbols: %s", symbols)
            return pd.DataFrame(
                columns=["timestamp", "series_id", "source", "value", "unit"]
            )

        # Normalize to long format
        # OpenBB returns wide format with date index and columns per series
        df = df.reset_index()

        # Handle different possible index column names
        date_col = None
        for col in ["date", "index", "timestamp"]:
            if col in df.columns:
                date_col = col
                break

        if date_col is None and df.index.name:
            df = df.reset_index()
            date_col = df.columns[0]

        if date_col is None:
            raise ValueError("Could not identify date column in FRED response")

        # Melt to long format
        id_vars = [date_col]
        value_vars = [col for col in df.columns if col in symbols]

        if not value_vars:
            logger.warning("No value columns found matching symbols: %s", symbols)
            return pd.DataFrame(
                columns=["timestamp", "series_id", "source", "value", "unit"]
            )

        df_long = df.melt(
            id_vars=id_vars,
            value_vars=value_vars,
            var_name="series_id",
            value_name="value",
        )

        # Rename date column
        df_long = df_long.rename(columns={date_col: "timestamp"})

        # Add source and unit columns
        df_long["source"] = "fred"
        df_long["unit"] = df_long["series_id"].map(UNIT_MAP).fillna("unknown")

        # Ensure timestamp is datetime
        df_long["timestamp"] = pd.to_datetime(df_long["timestamp"])

        # Drop NaN values
        df_long = df_long.dropna(subset=["value"])

        # Sort by timestamp
        df_long = df_long.sort_values("timestamp").reset_index(drop=True)

        logger.info("Fetched %d data points from FRED", len(df_long))

        result_df: pd.DataFrame = df_long[
            ["timestamp", "series_id", "source", "value", "unit"]
        ]
        return result_df

    @staticmethod
    def calculate_net_liquidity(df: pd.DataFrame) -> pd.DataFrame:
        """Calculate Net Liquidity using the Hayes formula.

        Net Liquidity = WALCL - WLRRAL - WDTGAL

        Note: WLRRAL and WDTGAL are in billions, WALCL in millions.
        Converts all to millions USD before calculation.

        Args:
            df: DataFrame with timestamp, series_id, value columns.

        Returns:
            DataFrame with timestamp, net_liquidity columns (in millions USD).
        """
        required = {"WALCL", "WLRRAL", "WDTGAL"}
        available = set(df["series_id"].unique())

        if not required.issubset(available):
            missing = required - available
            raise ValueError(f"Missing required series for Net Liquidity: {missing}")

        # Pivot to wide format for calculation
        pivot = df.pivot(index="timestamp", columns="series_id", values="value")

        # Convert units: WLRRAL and WDTGAL are in billions, convert to millions
        walcl = pivot["WALCL"]  # Already in millions
        rrp = pivot["WLRRAL"] * 1000  # Convert billions to millions
        tga = pivot["WDTGAL"] * 1000  # Convert billions to millions

        # Hayes formula
        net_liquidity = walcl - rrp - tga

        result = pd.DataFrame(
            {
                "timestamp": net_liquidity.index,
                "net_liquidity": net_liquidity.values,
            }
        ).dropna()

        result["unit"] = "millions_usd"

        logger.info(
            "Calculated Net Liquidity: min=%.0f, max=%.0f, latest=%.0f (millions USD)",
            result["net_liquidity"].min(),
            result["net_liquidity"].max(),
            result["net_liquidity"].iloc[-1] if len(result) > 0 else 0,
        )

        return result


# Register collector with the registry
registry.register("fred", FredCollector)
