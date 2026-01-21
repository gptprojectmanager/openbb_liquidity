"""Integration tests for FRED collector.

These tests require:
- Valid FRED API key (LIQUIDITY_FRED_API_KEY env var)
- Running QuestDB instance (localhost:9009 for ILP, localhost:8812 for PGWire)

Run with: uv run pytest tests/integration/test_fred_collector.py -v
"""

import asyncio
import os

import pytest

from liquidity.collectors.fred import FredCollector
from liquidity.storage.questdb import QuestDBStorage

# Skip integration tests if no FRED API key is set
pytestmark = pytest.mark.skipif(
    not os.environ.get("LIQUIDITY_FRED_API_KEY"),
    reason="LIQUIDITY_FRED_API_KEY not set - skipping FRED integration tests",
)


@pytest.fixture
def fred_collector() -> FredCollector:
    """Create a FRED collector instance."""
    return FredCollector()


@pytest.fixture
def questdb_storage() -> QuestDBStorage:
    """Create a QuestDB storage instance."""
    return QuestDBStorage()


class TestFredCollector:
    """Integration tests for FredCollector."""

    @pytest.mark.asyncio
    async def test_fetch_balance_sheet_series(
        self, fred_collector: FredCollector
    ) -> None:
        """Test fetching Fed balance sheet series."""
        # Fetch last 30 days of balance sheet data
        symbols = ["WALCL", "WLRRAL", "WDTGAL"]
        df = await fred_collector.collect(symbols)

        # Verify DataFrame structure
        assert not df.empty, "DataFrame should not be empty"
        assert set(df.columns) == {"timestamp", "series_id", "source", "value", "unit"}

        # Verify all series are present
        series_present = set(df["series_id"].unique())
        assert series_present == set(symbols), (
            f"Expected {symbols}, got {series_present}"
        )

        # Verify source is 'fred'
        assert df["source"].unique().tolist() == ["fred"]

        # Verify values are reasonable (Fed assets ~7 trillion USD = ~7,000,000 millions)
        walcl_values = df[df["series_id"] == "WALCL"]["value"]
        assert walcl_values.min() > 5_000_000, "WALCL should be > 5 trillion"
        assert walcl_values.max() < 15_000_000, "WALCL should be < 15 trillion"

    @pytest.mark.asyncio
    async def test_calculate_net_liquidity(self, fred_collector: FredCollector) -> None:
        """Test Net Liquidity calculation using Hayes formula."""
        symbols = ["WALCL", "WLRRAL", "WDTGAL"]
        df = await fred_collector.collect(symbols)

        # Calculate Net Liquidity
        net_liq = FredCollector.calculate_net_liquidity(df)

        # Verify result structure
        assert "timestamp" in net_liq.columns
        assert "net_liquidity" in net_liq.columns
        assert "unit" in net_liq.columns

        # Verify values are reasonable (Net Liquidity ~5-7 trillion USD range in 2024-2025)
        # Note: Values in millions
        latest_value = net_liq["net_liquidity"].iloc[-1]
        assert latest_value > 3_000_000, f"Net Liquidity too low: {latest_value}"
        assert latest_value < 10_000_000, f"Net Liquidity too high: {latest_value}"

        print(f"\nNet Liquidity (latest): ${latest_value / 1_000_000:.2f} trillion USD")

    @pytest.mark.asyncio
    async def test_collector_registered(self) -> None:
        """Test that FRED collector is registered in the registry."""
        from liquidity.collectors import registry

        assert "fred" in registry.list_collectors()
        collector_cls = registry.get("fred")
        assert collector_cls is FredCollector


class TestFredQuestDBIntegration:
    """Integration tests for FRED collector with QuestDB storage."""

    @pytest.mark.asyncio
    async def test_end_to_end_pipeline(
        self,
        fred_collector: FredCollector,
        questdb_storage: QuestDBStorage,
    ) -> None:
        """Test full pipeline: fetch FRED data, store in QuestDB, query back."""
        # Skip if QuestDB is not available
        if not questdb_storage.health_check():
            pytest.skip("QuestDB not available")

        # Create tables
        questdb_storage.create_tables()

        # Fetch data
        symbols = ["WALCL", "WLRRAL", "WDTGAL"]
        df = await fred_collector.collect(symbols)

        assert not df.empty, "No data fetched from FRED"

        # Store in QuestDB
        rows_ingested = questdb_storage.ingest_dataframe("raw_data", df)
        assert rows_ingested > 0, "No rows ingested"

        # Wait for QuestDB to flush (ILP is async)
        await asyncio.sleep(1)

        # Query back
        result = questdb_storage.query(
            "SELECT * FROM raw_data WHERE series_id = 'WALCL' ORDER BY timestamp DESC LIMIT 5"
        )

        assert len(result) > 0, "No data found in QuestDB"
        assert result[0]["series_id"] == "WALCL"
        assert result[0]["source"] == "fred"

        # Calculate and store Net Liquidity
        net_liq = FredCollector.calculate_net_liquidity(df)
        net_liq["index_name"] = "net_liquidity"
        net_liq["regime"] = "unknown"  # Regime classification comes later
        net_liq = net_liq.rename(columns={"net_liquidity": "value"})

        # Store liquidity index
        rows_ingested = questdb_storage.ingest_dataframe(
            "liquidity_indexes",
            net_liq[["timestamp", "index_name", "value", "regime"]],
            symbols=["index_name", "regime"],
        )
        assert rows_ingested > 0, "No liquidity index rows ingested"

        # Wait for flush
        await asyncio.sleep(1)

        # Query liquidity index
        idx_result = questdb_storage.query(
            "SELECT * FROM liquidity_indexes WHERE index_name = 'net_liquidity' ORDER BY timestamp DESC LIMIT 1"
        )

        assert len(idx_result) > 0, "No liquidity index found in QuestDB"

        latest = idx_result[0]
        print(
            f"\nStored Net Liquidity: ${latest['value'] / 1_000_000:.2f} trillion USD"
        )
        print(f"Timestamp: {latest['timestamp']}")


if __name__ == "__main__":
    # Run a quick sanity check
    async def main() -> None:
        collector = FredCollector()
        df = await collector.collect(["WALCL", "WLRRAL", "WDTGAL"])
        print(f"Fetched {len(df)} rows")
        print(df.head())

        net_liq = FredCollector.calculate_net_liquidity(df)
        print(
            f"\nNet Liquidity (latest): ${net_liq['net_liquidity'].iloc[-1] / 1_000_000:.2f} trillion USD"
        )

    asyncio.run(main())
