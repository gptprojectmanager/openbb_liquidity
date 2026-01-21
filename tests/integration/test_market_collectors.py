"""Integration tests for market collectors.

These tests require:
- Valid FRED API key (LIQUIDITY_FRED_API_KEY env var)
- Running QuestDB instance (localhost:9009 for ILP, localhost:8812 for PGWire)

Run with: uv run pytest tests/integration/test_market_collectors.py -v
"""

import asyncio
import os

import pytest

from liquidity.collectors.fred import FredCollector
from liquidity.collectors.yahoo import YahooCollector
from liquidity.storage.questdb import QuestDBStorage

# Skip integration tests if no FRED API key is set
pytestmark_fred = pytest.mark.skipif(
    not os.environ.get("LIQUIDITY_FRED_API_KEY"),
    reason="LIQUIDITY_FRED_API_KEY not set - skipping FRED integration tests",
)


@pytest.fixture
def fred_collector() -> FredCollector:
    """Create a FRED collector instance."""
    return FredCollector()


@pytest.fixture
def yahoo_collector() -> YahooCollector:
    """Create a Yahoo collector instance."""
    return YahooCollector()


@pytest.fixture
def questdb_storage() -> QuestDBStorage:
    """Create a QuestDB storage instance."""
    return QuestDBStorage()


class TestFredVolatilityCollector:
    """Integration tests for FRED volatility series (VIX, VIX3M)."""

    @pytestmark_fred
    @pytest.mark.asyncio
    async def test_fred_volatility_collector(
        self, fred_collector: FredCollector
    ) -> None:
        """Test fetching VIX and VIX3M volatility data."""
        df = await fred_collector.collect_volatility()

        # Verify DataFrame structure
        assert not df.empty, "DataFrame should not be empty"
        assert set(df.columns) == {"timestamp", "series_id", "source", "value", "unit"}

        # Verify series are present
        series_present = set(df["series_id"].unique())
        assert "VIXCLS" in series_present, "VIXCLS (VIX) should be present"
        assert "VXVCLS" in series_present, "VXVCLS (VIX3M) should be present"

        # Verify source
        assert df["source"].unique().tolist() == ["fred"]

        # Verify reasonable value ranges for VIX (typically 10-80)
        vix_values = df[df["series_id"] == "VIXCLS"]["value"]
        assert vix_values.min() >= 0, "VIX should be non-negative"
        assert vix_values.max() < 100, "VIX should be < 100 (extreme crisis levels)"

        # Verify VIX3M range (typically 10-60)
        vix3m_values = df[df["series_id"] == "VXVCLS"]["value"]
        assert vix3m_values.min() >= 0, "VIX3M should be non-negative"
        assert vix3m_values.max() < 80, "VIX3M should be < 80"

        print(f"\nVIX latest: {vix_values.iloc[-1]:.2f}")
        print(f"VIX3M latest: {vix3m_values.iloc[-1]:.2f}")


class TestFredYieldCollector:
    """Integration tests for FRED yield curve series."""

    @pytestmark_fred
    @pytest.mark.asyncio
    async def test_fred_yield_collector(self, fred_collector: FredCollector) -> None:
        """Test fetching yield curve data (DGS2, DGS10, T10Y2Y)."""
        df = await fred_collector.collect_yields()

        # Verify DataFrame structure
        assert not df.empty, "DataFrame should not be empty"
        assert set(df.columns) == {"timestamp", "series_id", "source", "value", "unit"}

        # Verify series are present
        series_present = set(df["series_id"].unique())
        assert "DGS2" in series_present, "DGS2 (2Y Treasury) should be present"
        assert "DGS10" in series_present, "DGS10 (10Y Treasury) should be present"
        assert "T10Y2Y" in series_present, "T10Y2Y (10Y-2Y Spread) should be present"

        # Verify calculated spread matches T10Y2Y
        yield_spread_calc = FredCollector.calculate_yield_spread(df)
        t10y2y_data = df[df["series_id"] == "T10Y2Y"][["timestamp", "value"]].rename(
            columns={"value": "t10y2y"}
        )
        merged = yield_spread_calc.merge(t10y2y_data, on="timestamp", how="inner")

        # Allow small tolerance due to timing differences
        if not merged.empty:
            diff = (merged["yield_spread"] - merged["t10y2y"]).abs()
            assert diff.max() < 0.05, (
                f"Calculated spread should match T10Y2Y (max diff: {diff.max():.3f})"
            )

        # Verify reasonable yield values (-1% to 8% for modern era)
        dgs10_values = df[df["series_id"] == "DGS10"]["value"]
        assert dgs10_values.min() > -1, "10Y yield should be > -1%"
        assert dgs10_values.max() < 10, "10Y yield should be < 10%"

        print(f"\n10Y Treasury latest: {dgs10_values.iloc[-1]:.2f}%")


class TestFredCreditCollector:
    """Integration tests for FRED credit spread series."""

    @pytestmark_fred
    @pytest.mark.asyncio
    async def test_fred_credit_collector(self, fred_collector: FredCollector) -> None:
        """Test fetching credit spread data (HY OAS, IG OAS)."""
        df = await fred_collector.collect_credit()

        # Verify DataFrame structure
        assert not df.empty, "DataFrame should not be empty"
        assert set(df.columns) == {"timestamp", "series_id", "source", "value", "unit"}

        # Verify series are present
        series_present = set(df["series_id"].unique())
        assert "BAMLH0A0HYM2" in series_present, (
            "BAMLH0A0HYM2 (HY OAS) should be present"
        )
        assert "BAMLC0A0CM" in series_present, "BAMLC0A0CM (IG OAS) should be present"

        # Verify reasonable ranges for credit spreads (in basis points)
        # HY OAS typically 200-1000 bps in normal conditions
        hy_values = df[df["series_id"] == "BAMLH0A0HYM2"]["value"]
        assert hy_values.min() > 50, "HY OAS should be > 50 bps"
        assert hy_values.max() < 2500, "HY OAS should be < 2500 bps (crisis levels)"

        # IG OAS typically 50-300 bps in normal conditions
        ig_values = df[df["series_id"] == "BAMLC0A0CM"]["value"]
        assert ig_values.min() > 0, "IG OAS should be > 0 bps"
        assert ig_values.max() < 1000, "IG OAS should be < 1000 bps (crisis levels)"

        print(f"\nHY OAS latest: {hy_values.iloc[-1]:.0f} bps")
        print(f"IG OAS latest: {ig_values.iloc[-1]:.0f} bps")


class TestYahooMoveCollector:
    """Integration tests for Yahoo Finance MOVE index collector."""

    @pytest.mark.asyncio
    async def test_yahoo_move_collector(self, yahoo_collector: YahooCollector) -> None:
        """Test fetching MOVE bond volatility index."""
        df = await yahoo_collector.collect_move()

        # MOVE may not be available in all environments
        if df.empty:
            pytest.skip("MOVE index data not available from Yahoo Finance")

        # Verify DataFrame structure
        assert set(df.columns) == {"timestamp", "symbol", "source", "value", "unit"}

        # Verify symbol is MOVE
        assert df["symbol"].unique().tolist() == ["^MOVE"]

        # Verify source
        assert df["source"].unique().tolist() == ["yahoo"]

        # Verify reasonable MOVE range (typically 60-200)
        move_values = df["value"]
        assert move_values.min() > 30, "MOVE should be > 30"
        assert move_values.max() < 400, "MOVE should be < 400 (extreme crisis levels)"

        print(f"\nMOVE latest: {move_values.iloc[-1]:.2f}")

    @pytest.mark.asyncio
    async def test_yahoo_collector_registered(self) -> None:
        """Test that Yahoo collector is registered in the registry."""
        from liquidity.collectors import registry

        assert "yahoo" in registry.list_collectors()
        collector_cls = registry.get("yahoo")
        assert collector_cls is YahooCollector


class TestFullPhase1Pipeline:
    """End-to-end integration tests for the complete Phase 1 data pipeline."""

    @pytestmark_fred
    @pytest.mark.asyncio
    async def test_full_phase1_pipeline(
        self,
        fred_collector: FredCollector,
        yahoo_collector: YahooCollector,
        questdb_storage: QuestDBStorage,
    ) -> None:
        """Test full Phase 1 pipeline: fetch all series, store, query back."""
        # Skip if QuestDB is not available
        if not questdb_storage.health_check():
            pytest.skip("QuestDB not available")

        # Create tables
        questdb_storage.create_tables()

        # Collect ALL Phase 1 data
        # 1. Fed Balance Sheet (from 01-02)
        fed_df = await fred_collector.collect(["WALCL", "WLRRAL", "WDTGAL"])
        assert not fed_df.empty, "Fed balance sheet data should not be empty"

        # 2. Volatility
        vol_df = await fred_collector.collect_volatility()
        assert not vol_df.empty, "Volatility data should not be empty"

        # 3. Yield Curve
        yield_df = await fred_collector.collect_yields()
        assert not yield_df.empty, "Yield curve data should not be empty"

        # 4. Credit Spreads
        credit_df = await fred_collector.collect_credit()
        assert not credit_df.empty, "Credit spread data should not be empty"

        # 5. MOVE (from Yahoo)
        move_df = await yahoo_collector.collect_move()
        # MOVE may not be available, so we don't require it

        # Store Fed data
        fed_rows = questdb_storage.ingest_dataframe("raw_data", fed_df)
        assert fed_rows > 0, "Should ingest Fed data"

        # Store volatility data
        vol_rows = questdb_storage.ingest_dataframe("raw_data", vol_df)
        assert vol_rows > 0, "Should ingest volatility data"

        # Store yield data
        yield_rows = questdb_storage.ingest_dataframe("raw_data", yield_df)
        assert yield_rows > 0, "Should ingest yield data"

        # Store credit data
        credit_rows = questdb_storage.ingest_dataframe("raw_data", credit_df)
        assert credit_rows > 0, "Should ingest credit data"

        # Wait for QuestDB to flush
        await asyncio.sleep(1)

        # Verify all series are stored
        expected_series = [
            "WALCL",
            "WLRRAL",
            "WDTGAL",  # Fed
            "VIXCLS",
            "VXVCLS",  # Volatility
            "DGS2",
            "DGS10",
            "T10Y2Y",  # Yields
            "BAMLH0A0HYM2",
            "BAMLC0A0CM",  # Credit
        ]

        for series_id in expected_series:
            result = questdb_storage.query(
                f"SELECT count() as cnt FROM raw_data WHERE series_id = '{series_id}'"
            )
            count = result[0]["cnt"] if result else 0
            assert count > 0, f"Series {series_id} should be in QuestDB"

        # Calculate and verify Net Liquidity
        net_liq = FredCollector.calculate_net_liquidity(fed_df)
        assert not net_liq.empty, "Net Liquidity should be calculated"

        # Store liquidity index
        net_liq["index_name"] = "net_liquidity"
        net_liq["regime"] = "unknown"
        net_liq = net_liq.rename(columns={"net_liquidity": "value"})

        idx_rows = questdb_storage.ingest_dataframe(
            "liquidity_indexes",
            net_liq[["timestamp", "index_name", "value", "regime"]],
            symbols=["index_name", "regime"],
        )
        assert idx_rows > 0, "Should ingest Net Liquidity index"

        await asyncio.sleep(1)

        # Query Net Liquidity
        idx_result = questdb_storage.query(
            "SELECT * FROM liquidity_indexes WHERE index_name = 'net_liquidity' ORDER BY timestamp DESC LIMIT 1"
        )
        assert len(idx_result) > 0, "Net Liquidity should be in QuestDB"

        print("\n=== Phase 1 Pipeline Complete ===")
        print(f"Fed data rows: {fed_rows}")
        print(f"Volatility rows: {vol_rows}")
        print(f"Yield rows: {yield_rows}")
        print(f"Credit rows: {credit_rows}")
        print(f"Net Liquidity: ${idx_result[0]['value'] / 1_000_000:.2f} trillion USD")


if __name__ == "__main__":
    # Run a quick sanity check
    async def main() -> None:
        fred = FredCollector()
        yahoo = YahooCollector()

        print("Testing FRED volatility...")
        vol_df = await fred.collect_volatility()
        print(f"  VIX points: {len(vol_df[vol_df['series_id'] == 'VIXCLS'])}")

        print("Testing FRED yields...")
        yield_df = await fred.collect_yields()
        print(f"  DGS10 points: {len(yield_df[yield_df['series_id'] == 'DGS10'])}")

        print("Testing FRED credit...")
        credit_df = await fred.collect_credit()
        print(
            f"  HY OAS points: {len(credit_df[credit_df['series_id'] == 'BAMLH0A0HYM2'])}"
        )

        print("Testing Yahoo MOVE...")
        move_df = await yahoo.collect_move()
        print(f"  MOVE points: {len(move_df)}")

    asyncio.run(main())
