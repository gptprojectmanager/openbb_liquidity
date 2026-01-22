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
        assert bool(df["stale"].iloc[0]) is True
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


class TestGlobalCBSeriesMapping:
    """Test that ECB/BoJ series are properly mapped in FRED collector."""

    def test_ecb_series_in_series_map(self) -> None:
        """Verify ECBASSETSW is in SERIES_MAP."""
        from liquidity.collectors.fred import SERIES_MAP

        assert "ecb_total_assets" in SERIES_MAP
        assert SERIES_MAP["ecb_total_assets"] == "ECBASSETSW"

    def test_boj_series_in_series_map(self) -> None:
        """Verify JPNASSETS is in SERIES_MAP."""
        from liquidity.collectors.fred import SERIES_MAP

        assert "boj_total_assets" in SERIES_MAP
        assert SERIES_MAP["boj_total_assets"] == "JPNASSETS"

    def test_ecb_unit_mapping(self) -> None:
        """Verify ECBASSETSW unit is correctly mapped."""
        from liquidity.collectors.fred import UNIT_MAP

        assert "ECBASSETSW" in UNIT_MAP
        assert UNIT_MAP["ECBASSETSW"] == "millions_eur"

    def test_boj_unit_mapping(self) -> None:
        """Verify JPNASSETS unit is correctly mapped (100 million JPY)."""
        from liquidity.collectors.fred import UNIT_MAP

        assert "JPNASSETS" in UNIT_MAP
        assert UNIT_MAP["JPNASSETS"] == "100_millions_jpy"


@requires_fred_api
class TestECBCollector:
    """Integration tests for ECB total assets collection via FRED."""

    @pytest.mark.asyncio
    async def test_fetch_ecb_assets_series(self, fred_collector: FredCollector) -> None:
        """Test fetching ECB total assets series (ECBASSETSW)."""
        df = await fred_collector.collect(["ECBASSETSW"])

        # Verify DataFrame structure
        assert not df.empty, "DataFrame should not be empty"
        assert set(df.columns) == {"timestamp", "series_id", "source", "value", "unit"}

        # Verify series is present
        assert "ECBASSETSW" in df["series_id"].unique()

        # Verify source is 'fred'
        assert df["source"].unique().tolist() == ["fred"]

        # Verify unit metadata
        ecb_data = df[df["series_id"] == "ECBASSETSW"]
        assert ecb_data["unit"].iloc[0] == "millions_eur"

        # Verify values are reasonable
        # ECB balance sheet ~5-10 trillion EUR = 5,000,000-10,000,000 millions
        values = ecb_data["value"]
        assert values.min() > 1_000_000, (
            f"ECB assets too low: {values.min()} (expected > 1 trillion EUR)"
        )
        assert values.max() < 15_000_000, (
            f"ECB assets too high: {values.max()} (expected < 15 trillion EUR)"
        )

        print(f"\nECB Total Assets (latest): {values.iloc[-1]:,.0f} million EUR")
        print(f"  = {values.iloc[-1] / 1_000_000:.2f} trillion EUR")

    @pytest.mark.asyncio
    async def test_collect_ecb_assets_convenience_method(
        self, fred_collector: FredCollector
    ) -> None:
        """Test the collect_ecb_assets convenience method."""
        df = await fred_collector.collect_ecb_assets()

        assert not df.empty, "DataFrame should not be empty"
        assert "ECBASSETSW" in df["series_id"].unique()
        assert df["unit"].iloc[0] == "millions_eur"


@requires_fred_api
class TestBoJCollector:
    """Integration tests for BoJ total assets collection via FRED."""

    @pytest.mark.asyncio
    async def test_fetch_boj_assets_series(self, fred_collector: FredCollector) -> None:
        """Test fetching BoJ total assets series (JPNASSETS)."""
        df = await fred_collector.collect(["JPNASSETS"])

        # Verify DataFrame structure
        assert not df.empty, "DataFrame should not be empty"
        assert set(df.columns) == {"timestamp", "series_id", "source", "value", "unit"}

        # Verify series is present
        assert "JPNASSETS" in df["series_id"].unique()

        # Verify source is 'fred'
        assert df["source"].unique().tolist() == ["fred"]

        # Verify unit metadata
        boj_data = df[df["series_id"] == "JPNASSETS"]
        assert boj_data["unit"].iloc[0] == "100_millions_jpy"

        # Verify values are reasonable
        # BoJ balance sheet ~700+ trillion JPY
        # In FRED units (100 million JPY): 700 trillion = 7,000,000 units
        values = boj_data["value"]
        assert values.min() > 3_000_000, (
            f"BoJ assets too low: {values.min()} (expected > 300 trillion JPY)"
        )
        assert values.max() < 15_000_000, (
            f"BoJ assets too high: {values.max()} (expected < 1500 trillion JPY)"
        )

        latest = values.iloc[-1]
        print(f"\nBoJ Total Assets (latest): {latest:,.0f} (100 million JPY)")
        print(f"  = {latest * 100 / 1_000_000:.2f} trillion JPY")

    @pytest.mark.asyncio
    async def test_collect_boj_assets_convenience_method(
        self, fred_collector: FredCollector
    ) -> None:
        """Test the collect_boj_assets convenience method."""
        df = await fred_collector.collect_boj_assets()

        assert not df.empty, "DataFrame should not be empty"
        assert "JPNASSETS" in df["series_id"].unique()
        assert df["unit"].iloc[0] == "100_millions_jpy"


@requires_fred_api
class TestGlobalCBTotals:
    """Integration tests for combined global CB totals collection."""

    @pytest.mark.asyncio
    async def test_collect_global_cb_totals(
        self, fred_collector: FredCollector
    ) -> None:
        """Test fetching all CB totals (Fed, ECB, BoJ)."""
        df = await fred_collector.collect_global_cb_totals()

        # Verify DataFrame structure
        assert not df.empty, "DataFrame should not be empty"
        assert set(df.columns) == {"timestamp", "series_id", "source", "value", "unit"}

        # Verify all series are present
        series_present = set(df["series_id"].unique())
        expected_series = {"WALCL", "ECBASSETSW", "JPNASSETS"}
        assert expected_series.issubset(series_present), (
            f"Missing series: {expected_series - series_present}"
        )

        # Verify unit metadata is correct for each series
        for series_id, expected_unit in [
            ("WALCL", "millions_usd"),
            ("ECBASSETSW", "millions_eur"),
            ("JPNASSETS", "100_millions_jpy"),
        ]:
            series_data = df[df["series_id"] == series_id]
            if not series_data.empty:
                assert series_data["unit"].iloc[0] == expected_unit, (
                    f"{series_id} has wrong unit: {series_data['unit'].iloc[0]}"
                )

        print("\nGlobal CB Totals fetched:")
        for series_id in expected_series:
            series_data = df[df["series_id"] == series_id]
            if not series_data.empty:
                latest = series_data["value"].iloc[-1]
                unit = series_data["unit"].iloc[0]
                print(f"  {series_id}: {latest:,.0f} ({unit})")


@requires_fred_api
class TestGlobalCBQuestDBIntegration:
    """Integration tests for Global CB data with QuestDB storage."""

    @pytest.mark.asyncio
    async def test_store_and_query_ecb_boj_data(
        self,
        fred_collector: FredCollector,
        questdb_storage: QuestDBStorage,
    ) -> None:
        """Test storing ECB/BoJ data in QuestDB and querying back with units preserved."""
        import asyncio

        # Skip if QuestDB is not available
        if not questdb_storage.health_check():
            pytest.skip("QuestDB not available")

        # Create tables
        questdb_storage.create_tables()

        # Fetch ECB and BoJ data
        df = await fred_collector.collect(["ECBASSETSW", "JPNASSETS"])

        assert not df.empty, "No data fetched from FRED"

        # Store in QuestDB
        rows_ingested = questdb_storage.ingest_dataframe("raw_data", df)
        assert rows_ingested > 0, "No rows ingested"

        # Wait for QuestDB to flush (ILP is async)
        await asyncio.sleep(1)

        # Query back ECB data and verify unit is preserved
        ecb_result = questdb_storage.query(
            "SELECT * FROM raw_data WHERE series_id = 'ECBASSETSW' "
            "ORDER BY timestamp DESC LIMIT 5"
        )

        if ecb_result:
            assert ecb_result[0]["series_id"] == "ECBASSETSW"
            assert ecb_result[0]["source"] == "fred"
            assert ecb_result[0]["unit"] == "millions_eur"
            print(
                f"\nECB data from QuestDB: {ecb_result[0]['value']:,.0f} "
                f"{ecb_result[0]['unit']}"
            )

        # Query back BoJ data and verify unit is preserved
        boj_result = questdb_storage.query(
            "SELECT * FROM raw_data WHERE series_id = 'JPNASSETS' "
            "ORDER BY timestamp DESC LIMIT 5"
        )

        if boj_result:
            assert boj_result[0]["series_id"] == "JPNASSETS"
            assert boj_result[0]["source"] == "fred"
            assert boj_result[0]["unit"] == "100_millions_jpy"
            print(
                f"BoJ data from QuestDB: {boj_result[0]['value']:,.0f} "
                f"{boj_result[0]['unit']}"
            )

    @pytest.mark.asyncio
    async def test_store_global_cb_totals(
        self,
        fred_collector: FredCollector,
        questdb_storage: QuestDBStorage,
    ) -> None:
        """Test full pipeline: fetch all CB totals, store in QuestDB, query back."""
        import asyncio

        # Skip if QuestDB is not available
        if not questdb_storage.health_check():
            pytest.skip("QuestDB not available")

        # Create tables
        questdb_storage.create_tables()

        # Fetch all CB totals
        df = await fred_collector.collect_global_cb_totals()

        assert not df.empty, "No data fetched from FRED"

        # Store in QuestDB
        rows_ingested = questdb_storage.ingest_dataframe("raw_data", df)
        assert rows_ingested > 0, "No rows ingested"

        # Wait for QuestDB to flush
        await asyncio.sleep(1)

        # Query back and verify all series are stored with correct units
        for series_id, expected_unit in [
            ("WALCL", "millions_usd"),
            ("ECBASSETSW", "millions_eur"),
            ("JPNASSETS", "100_millions_jpy"),
        ]:
            result = questdb_storage.query(
                f"SELECT * FROM raw_data WHERE series_id = '{series_id}' "
                "ORDER BY timestamp DESC LIMIT 1"
            )

            if result:
                assert result[0]["unit"] == expected_unit, (
                    f"{series_id} unit not preserved: expected {expected_unit}, "
                    f"got {result[0]['unit']}"
                )
                print(f"{series_id}: {result[0]['value']:,.0f} {result[0]['unit']}")
