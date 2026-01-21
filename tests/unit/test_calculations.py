"""Unit tests for liquidity calculations.

These tests use known inputs to verify calculation correctness without
requiring external API access.

Run with: uv run pytest tests/unit/test_calculations.py -v
"""

import pandas as pd
import pytest

from liquidity.collectors.fred import FredCollector


class TestNetLiquidityCalculation:
    """Unit tests for Net Liquidity calculation (Hayes formula)."""

    def test_net_liquidity_basic(self) -> None:
        """Test basic Net Liquidity calculation with known values."""
        # Create test data
        # WALCL: Fed Total Assets in millions (7 trillion = 7,000,000 millions)
        # WLRRAL: Reverse Repo in billions (500 billion = 500 billions)
        # WDTGAL: TGA in billions (750 billion = 750 billions)
        # Expected: 7,000,000 - 500,000 - 750,000 = 5,750,000 millions = $5.75 trillion
        data = {
            "timestamp": ["2024-01-01", "2024-01-01", "2024-01-01"],
            "series_id": ["WALCL", "WLRRAL", "WDTGAL"],
            "value": [7_000_000, 500, 750],  # WALCL in millions, RRP/TGA in billions
            "unit": ["millions_usd", "billions_usd", "billions_usd"],
        }
        df = pd.DataFrame(data)
        df["timestamp"] = pd.to_datetime(df["timestamp"])

        result = FredCollector.calculate_net_liquidity(df)

        assert len(result) == 1
        assert result["timestamp"].iloc[0] == pd.Timestamp("2024-01-01")
        # Expected: 7,000,000 - (500*1000) - (750*1000) = 5,750,000
        assert result["net_liquidity"].iloc[0] == 5_750_000
        assert result["unit"].iloc[0] == "millions_usd"

    def test_net_liquidity_historical_values(self) -> None:
        """Test Net Liquidity with approximate historical values from Apps Script."""
        # Approximate values from late 2024:
        # WALCL: ~$7.1 trillion = 7,100,000 millions
        # RRP: ~$400 billion = 400 billions
        # TGA: ~$800 billion = 800 billions
        # Expected Net Liquidity: ~$5.9 trillion
        data = {
            "timestamp": ["2024-12-01", "2024-12-01", "2024-12-01"],
            "series_id": ["WALCL", "WLRRAL", "WDTGAL"],
            "value": [7_100_000, 400, 800],
            "unit": ["millions_usd", "billions_usd", "billions_usd"],
        }
        df = pd.DataFrame(data)
        df["timestamp"] = pd.to_datetime(df["timestamp"])

        result = FredCollector.calculate_net_liquidity(df)

        # Expected: 7,100,000 - 400,000 - 800,000 = 5,900,000 (~$5.9T)
        assert result["net_liquidity"].iloc[0] == 5_900_000

        # Verify it's in the reasonable range ($3T to $10T)
        assert 3_000_000 < result["net_liquidity"].iloc[0] < 10_000_000

    def test_net_liquidity_multiple_timestamps(self) -> None:
        """Test Net Liquidity calculation with multiple timestamps."""
        data = {
            "timestamp": [
                "2024-01-01",
                "2024-01-01",
                "2024-01-01",
                "2024-01-08",
                "2024-01-08",
                "2024-01-08",
            ],
            "series_id": [
                "WALCL",
                "WLRRAL",
                "WDTGAL",
                "WALCL",
                "WLRRAL",
                "WDTGAL",
            ],
            "value": [7_000_000, 500, 750, 7_050_000, 480, 720],
            "unit": [
                "millions_usd",
                "billions_usd",
                "billions_usd",
                "millions_usd",
                "billions_usd",
                "billions_usd",
            ],
        }
        df = pd.DataFrame(data)
        df["timestamp"] = pd.to_datetime(df["timestamp"])

        result = FredCollector.calculate_net_liquidity(df)

        assert len(result) == 2
        # First: 7,000,000 - 500,000 - 750,000 = 5,750,000
        assert result["net_liquidity"].iloc[0] == 5_750_000
        # Second: 7,050,000 - 480,000 - 720,000 = 5,850,000
        assert result["net_liquidity"].iloc[1] == 5_850_000

    def test_net_liquidity_missing_series(self) -> None:
        """Test Net Liquidity raises error when series are missing."""
        data = {
            "timestamp": ["2024-01-01", "2024-01-01"],
            "series_id": ["WALCL", "WLRRAL"],  # Missing WDTGAL
            "value": [7_000_000, 500],
            "unit": ["millions_usd", "billions_usd"],
        }
        df = pd.DataFrame(data)
        df["timestamp"] = pd.to_datetime(df["timestamp"])

        with pytest.raises(ValueError, match="Missing required series"):
            FredCollector.calculate_net_liquidity(df)


class TestYieldSpreadCalculation:
    """Unit tests for yield spread calculation."""

    def test_yield_spread_basic(self) -> None:
        """Test basic yield spread calculation."""
        # 10Y at 4.5%, 2Y at 4.0% => spread = 0.5%
        data = {
            "timestamp": ["2024-01-01", "2024-01-01"],
            "series_id": ["DGS10", "DGS2"],
            "value": [4.5, 4.0],
            "unit": ["percent", "percent"],
        }
        df = pd.DataFrame(data)
        df["timestamp"] = pd.to_datetime(df["timestamp"])

        result = FredCollector.calculate_yield_spread(df)

        assert len(result) == 1
        assert result["yield_spread"].iloc[0] == pytest.approx(0.5, abs=0.001)
        assert result["unit"].iloc[0] == "percent"

    def test_yield_spread_inverted(self) -> None:
        """Test inverted yield curve (2Y > 10Y)."""
        # 10Y at 4.0%, 2Y at 4.5% => spread = -0.5%
        data = {
            "timestamp": ["2024-01-01", "2024-01-01"],
            "series_id": ["DGS10", "DGS2"],
            "value": [4.0, 4.5],
            "unit": ["percent", "percent"],
        }
        df = pd.DataFrame(data)
        df["timestamp"] = pd.to_datetime(df["timestamp"])

        result = FredCollector.calculate_yield_spread(df)

        assert result["yield_spread"].iloc[0] == pytest.approx(-0.5, abs=0.001)

    def test_yield_spread_historical_inversion(self) -> None:
        """Test yield spread with historical inversion values."""
        # 2022-2023 saw significant yield curve inversion
        # Approximate values: 10Y ~3.8%, 2Y ~4.5%
        data = {
            "timestamp": ["2023-01-01", "2023-01-01"],
            "series_id": ["DGS10", "DGS2"],
            "value": [3.8, 4.5],
            "unit": ["percent", "percent"],
        }
        df = pd.DataFrame(data)
        df["timestamp"] = pd.to_datetime(df["timestamp"])

        result = FredCollector.calculate_yield_spread(df)

        # Inverted: 3.8 - 4.5 = -0.7
        assert result["yield_spread"].iloc[0] == pytest.approx(-0.7, abs=0.01)
        # Negative spread indicates recession warning
        assert result["yield_spread"].iloc[0] < 0

    def test_yield_spread_multiple_timestamps(self) -> None:
        """Test yield spread with multiple timestamps."""
        data = {
            "timestamp": ["2024-01-01", "2024-01-01", "2024-01-02", "2024-01-02"],
            "series_id": ["DGS10", "DGS2", "DGS10", "DGS2"],
            "value": [4.5, 4.0, 4.6, 4.1],
            "unit": ["percent", "percent", "percent", "percent"],
        }
        df = pd.DataFrame(data)
        df["timestamp"] = pd.to_datetime(df["timestamp"])

        result = FredCollector.calculate_yield_spread(df)

        assert len(result) == 2
        assert result["yield_spread"].iloc[0] == pytest.approx(0.5, abs=0.001)
        assert result["yield_spread"].iloc[1] == pytest.approx(0.5, abs=0.001)

    def test_yield_spread_missing_series(self) -> None:
        """Test yield spread raises error when series are missing."""
        data = {
            "timestamp": ["2024-01-01"],
            "series_id": ["DGS10"],  # Missing DGS2
            "value": [4.5],
            "unit": ["percent"],
        }
        df = pd.DataFrame(data)
        df["timestamp"] = pd.to_datetime(df["timestamp"])

        with pytest.raises(ValueError, match="Missing required series"):
            FredCollector.calculate_yield_spread(df)


class TestSeriesMap:
    """Unit tests for series mapping constants."""

    def test_series_map_contains_required_fed_series(self) -> None:
        """Test SERIES_MAP contains all Fed balance sheet series."""
        from liquidity.collectors.fred import SERIES_MAP

        # Core Fed balance sheet
        assert "fed_total_assets" in SERIES_MAP
        assert SERIES_MAP["fed_total_assets"] == "WALCL"
        assert "rrp" in SERIES_MAP
        assert SERIES_MAP["rrp"] == "WLRRAL"
        assert "tga" in SERIES_MAP
        assert SERIES_MAP["tga"] == "WDTGAL"

    def test_series_map_contains_volatility_series(self) -> None:
        """Test SERIES_MAP contains volatility series."""
        from liquidity.collectors.fred import SERIES_MAP

        assert "vix" in SERIES_MAP
        assert SERIES_MAP["vix"] == "VIXCLS"
        assert "vix3m" in SERIES_MAP
        assert SERIES_MAP["vix3m"] == "VXVCLS"

    def test_series_map_contains_yield_series(self) -> None:
        """Test SERIES_MAP contains yield curve series."""
        from liquidity.collectors.fred import SERIES_MAP

        assert "dgs2" in SERIES_MAP
        assert SERIES_MAP["dgs2"] == "DGS2"
        assert "dgs10" in SERIES_MAP
        assert SERIES_MAP["dgs10"] == "DGS10"
        assert "t10y2y" in SERIES_MAP
        assert SERIES_MAP["t10y2y"] == "T10Y2Y"

    def test_series_map_contains_credit_series(self) -> None:
        """Test SERIES_MAP contains credit spread series."""
        from liquidity.collectors.fred import SERIES_MAP

        assert "hy_oas" in SERIES_MAP
        assert SERIES_MAP["hy_oas"] == "BAMLH0A0HYM2"
        assert "ig_oas" in SERIES_MAP
        assert SERIES_MAP["ig_oas"] == "BAMLC0A0CM"


class TestUnitMap:
    """Unit tests for unit mapping constants."""

    def test_unit_map_fed_series(self) -> None:
        """Test UNIT_MAP has correct units for Fed series."""
        from liquidity.collectors.fred import UNIT_MAP

        assert UNIT_MAP["WALCL"] == "millions_usd"
        assert UNIT_MAP["WLRRAL"] == "billions_usd"
        assert UNIT_MAP["WDTGAL"] == "billions_usd"

    def test_unit_map_volatility_series(self) -> None:
        """Test UNIT_MAP has correct units for volatility series."""
        from liquidity.collectors.fred import UNIT_MAP

        assert UNIT_MAP["VIXCLS"] == "percent"
        assert UNIT_MAP["VXVCLS"] == "percent"

    def test_unit_map_yield_series(self) -> None:
        """Test UNIT_MAP has correct units for yield series."""
        from liquidity.collectors.fred import UNIT_MAP

        assert UNIT_MAP["DGS2"] == "percent"
        assert UNIT_MAP["DGS10"] == "percent"
        assert UNIT_MAP["T10Y2Y"] == "percent"

    def test_unit_map_credit_series(self) -> None:
        """Test UNIT_MAP has correct units for credit spread series."""
        from liquidity.collectors.fred import UNIT_MAP

        assert UNIT_MAP["BAMLH0A0HYM2"] == "bps"
        assert UNIT_MAP["BAMLC0A0CM"] == "bps"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
