"""Integration tests for Global Central Bank collectors.

These tests require:
- Valid FRED API key (LIQUIDITY_FRED_API_KEY env var) for ECB/BoJ tests
- Network access to external central bank data portals for SNB tests
- Running QuestDB instance (localhost:9009 for ILP, localhost:8812 for PGWire)

Run with: uv run pytest tests/integration/test_global_cb_collectors.py -v
"""

import os

import pytest

from liquidity.collectors.fred import FredCollector
from liquidity.collectors.snb import SNBCollector
from liquidity.storage.questdb import QuestDBStorage

# Marker for tests that require FRED API key
requires_fred_api = pytest.mark.skipif(
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


class TestSNBCollector:
    """Tests for Swiss National Bank collector."""

    @pytest.mark.asyncio
    async def test_snb_collect_balance_sheet(self) -> None:
        """Test fetching SNB balance sheet data."""
        collector = SNBCollector()
        df = await collector.collect()

        assert not df.empty
        assert "timestamp" in df.columns
        assert "value" in df.columns
        assert df["source"].iloc[0] == "snb"
        assert df["unit"].iloc[0] == "millions_chf"

    @pytest.mark.asyncio
    async def test_snb_data_reasonable_range(self) -> None:
        """Test SNB data is in reasonable range."""
        collector = SNBCollector()
        df = await collector.collect()

        # SNB total assets should be 500-1500 billion CHF range
        # In millions: 500,000 - 1,500,000
        # Current value ~896,721 million CHF (verified Nov 2024)
        latest = df["value"].iloc[-1]
        assert 500_000 < latest < 1_500_000, (
            f"SNB total assets {latest} out of expected range"
        )

    @pytest.mark.asyncio
    async def test_snb_collector_registered(self) -> None:
        """Test that SNB collector is registered."""
        from liquidity.collectors import registry

        assert "snb" in registry.list_collectors()


class TestBOCCollector:
    """Tests for Bank of Canada collector."""

    @pytest.mark.asyncio
    async def test_boc_collect_total_assets(self) -> None:
        """Test fetching BoC total assets."""
        from liquidity.collectors.boc import BOCCollector

        collector = BOCCollector()
        df = await collector.collect_total_assets()

        assert not df.empty
        assert "timestamp" in df.columns
        assert "value" in df.columns
        assert df["source"].iloc[0] == "boc"
        assert df["unit"].iloc[0] == "millions_cad"

    @pytest.mark.asyncio
    async def test_boc_data_reasonable_range(self) -> None:
        """Test BoC data is in reasonable range."""
        from liquidity.collectors.boc import BOCCollector

        collector = BOCCollector()
        df = await collector.collect_total_assets()

        # BoC total assets should be 200-500 billion CAD range
        # In millions: 200,000 - 500,000
        latest = df["value"].iloc[-1]
        assert 200_000 < latest < 500_000, (
            f"BoC total assets {latest} out of expected range"
        )

    @pytest.mark.asyncio
    async def test_boc_collector_registered(self) -> None:
        """Test that BoC collector is registered."""
        from liquidity.collectors import registry

        assert "boc" in registry.list_collectors()


class TestBOECollector:
    """Tests for Bank of England collector."""

    @pytest.mark.asyncio
    async def test_boe_collect_always_returns_data(self) -> None:
        """Test BoE collection with fallback (ALWAYS returns data)."""
        from liquidity.collectors.boe import BOECollector

        collector = BOECollector()
        df = await collector.collect()

        # Should ALWAYS return data due to fallback chain
        assert not df.empty
        assert "timestamp" in df.columns
        assert "value" in df.columns
        assert df["unit"].iloc[0] == "millions_gbp"

    @pytest.mark.asyncio
    async def test_boe_data_reasonable_range(self) -> None:
        """Test BoE data is in reasonable range."""
        from liquidity.collectors.boe import BOECollector

        collector = BOECollector()
        df = await collector.collect()

        # BoE total assets should be 400-1500 billion GBP range
        # In millions: 400,000 - 1,500,000
        latest = df["value"].iloc[-1]
        assert 400_000 < latest < 1_500_000, (
            f"BoE total assets {latest} out of expected range"
        )

    @pytest.mark.asyncio
    async def test_boe_cached_baseline_works(self) -> None:
        """Test that cached baseline returns valid data."""
        from liquidity.collectors.boe import BOECollector

        collector = BOECollector()
        df = collector._get_cached_baseline()

        assert not df.empty
        assert df["source"].iloc[0] == "cached_baseline"
        assert df["stale"].iloc[0] is True
        assert df["value"].iloc[0] == 848_000

    @pytest.mark.asyncio
    async def test_boe_collector_registered(self) -> None:
        """Test that BoE collector is registered."""
        from liquidity.collectors import registry

        assert "boe" in registry.list_collectors()


class TestPBOCCollector:
    """Tests for People's Bank of China collector."""

    @pytest.mark.asyncio
    async def test_pboc_collect_with_fallback(self) -> None:
        """Test PBoC collection (scraping or FRED fallback)."""
        from liquidity.collectors.pboc import PBOCCollector

        collector = PBOCCollector(use_fred_fallback=True)
        df = await collector.collect()

        # Should ALWAYS return data due to fallback chain
        assert not df.empty
        assert "timestamp" in df.columns
        assert "value" in df.columns

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.environ.get("LIQUIDITY_FRED_API_KEY"),
        reason="LIQUIDITY_FRED_API_KEY not set",
    )
    async def test_pboc_fred_fallback_works(self) -> None:
        """Test FRED fallback explicitly."""
        from liquidity.collectors.pboc import PBOCCollector

        collector = PBOCCollector(use_fred_fallback=True)
        df = await collector._collect_via_fred(None, None)

        assert not df.empty
        assert df["series_id"].iloc[0] == "CHINA_FOREIGN_RESERVES"
        assert df["source"].iloc[0] == "fred_proxy"

    @pytest.mark.asyncio
    async def test_pboc_cached_baseline_works(self) -> None:
        """Test that cached baseline returns valid data."""
        from liquidity.collectors.pboc import PBOCCollector

        collector = PBOCCollector()
        df = collector._get_cached_baseline()

        assert not df.empty
        assert df["source"].iloc[0] == "cached_baseline"
        assert df["stale"].iloc[0] is True
        assert df["value"].iloc[0] == 47_296_970

    @pytest.mark.asyncio
    async def test_pboc_collector_registered(self) -> None:
        """Test that PBoC collector is registered."""
        from liquidity.collectors import registry

        assert "pboc" in registry.list_collectors()
