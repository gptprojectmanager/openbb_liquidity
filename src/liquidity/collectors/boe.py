"""Bank of England collector with multi-tier fallback.

FRED series BOEBSTAUKA discontinued 2016. BoE database API returns 403.
Implements ROBUST fallback: scraping -> FRED proxy -> cached baseline.
"""

import logging
import re
from datetime import datetime
from typing import Any

import httpx
import pandas as pd
from bs4 import BeautifulSoup

from liquidity.collectors.base import BaseCollector, CollectorFetchError
from liquidity.collectors.registry import registry
from liquidity.config import Settings, get_settings

logger = logging.getLogger(__name__)

# Weekly report base URL
BOE_WEEKLY_REPORT_BASE = "https://www.bankofengland.co.uk/weekly-report"

UNIT_MAP: dict[str, str] = {
    "BOE_TOTAL_ASSETS": "millions_gbp",
}


class BOECollector(BaseCollector[pd.DataFrame]):
    """Bank of England collector with ROBUST multi-tier fallback."""

    # Cached baseline for guaranteed fallback
    BASELINE_VALUE = 848_000  # millions GBP (Nov 2025)
    BASELINE_DATE = "2025-11-26"

    SERIES_MAP: dict[str, str] = {
        "boe_total_assets": "BOE_TOTAL_ASSETS",
    }

    def __init__(
        self,
        name: str = "boe",
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
        """Collect BoE data with multi-tier fallback (ALWAYS returns data)."""
        # Tier 1: Try scraping weekly report
        try:
            logger.info("BoE: Attempting Tier 1 (weekly report scraping)")
            return await self._collect_via_scraping()
        except Exception as e:
            logger.warning("BoE Tier 1 (scraping) failed: %s", e)

        # Tier 2: Try FRED UK M4 proxy
        try:
            logger.info("BoE: Attempting Tier 2 (FRED M4 proxy)")
            return await self._collect_via_fred_proxy(start_date, end_date)
        except Exception as e:
            logger.warning("BoE Tier 2 (FRED proxy) failed: %s", e)

        # Tier 3: Return cached baseline (GUARANTEED)
        logger.warning("All BoE sources failed, returning cached baseline")
        return self._get_cached_baseline()

    async def _collect_via_scraping(self) -> pd.DataFrame:
        """Tier 1: Scrape weekly report HTML."""
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            # Fetch the balance sheet and weekly report index page
            index_url = f"{BOE_WEEKLY_REPORT_BASE}/balance-sheet-and-weekly-report"
            response = await client.get(index_url)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "lxml")

            # Find links to weekly reports
            report_links = soup.find_all("a", href=re.compile(r"/weekly-report/\d{4}/"))

            if not report_links:
                raise CollectorFetchError("No weekly report links found")

            # Get the latest report URL
            latest_href = report_links[0].get("href", "")
            if not latest_href.startswith("http"):
                latest_url = f"https://www.bankofengland.co.uk{latest_href}"
            else:
                latest_url = str(latest_href)

            # Fetch the latest weekly report
            report_response = await client.get(latest_url)
            report_response.raise_for_status()

            return self._parse_weekly_report(report_response.text, latest_url)

    def _parse_weekly_report(self, html: str, url: str) -> pd.DataFrame:
        """Parse weekly report HTML and extract total assets."""
        soup = BeautifulSoup(html, "lxml")

        # Extract date from URL (format: /weekly-report/2025/26-november-2025)
        date_match = re.search(r"/weekly-report/(\d{4})/(\d{1,2})-(\w+)-(\d{4})", url)
        if date_match:
            day, month_name, year = (
                date_match.group(2),
                date_match.group(3),
                date_match.group(4),
            )
            # Parse the date
            try:
                report_date = pd.to_datetime(
                    f"{day} {month_name} {year}", format="%d %B %Y"
                )
            except Exception:
                report_date = pd.Timestamp.now()
        else:
            report_date = pd.Timestamp.now()

        # Try to find total assets in the page
        # Look for tables or specific text patterns
        total_assets = None

        # Look for total in tables
        tables = soup.find_all("table")
        for table in tables:
            table_text = table.get_text().lower()
            if "total" in table_text and (
                "asset" in table_text or "sterling" in table_text
            ):
                # Try to find numeric value
                cells = table.find_all(["td", "th"])
                for cell in cells:
                    cell_text = cell.get_text().strip()
                    # Look for large numbers (6+ digits, possibly with commas)
                    num_match = re.search(
                        r"[\d,]+(?:\.\d+)?", cell_text.replace(" ", "")
                    )
                    if num_match:
                        try:
                            value = float(num_match.group().replace(",", ""))
                            # Sanity check: BoE total assets should be 500-1000 billion GBP
                            if 500_000 < value < 1_500_000:
                                total_assets = value
                                break
                        except ValueError:
                            continue
                if total_assets:
                    break

        if total_assets is None:
            raise CollectorFetchError("Could not parse total assets from weekly report")

        return pd.DataFrame(
            {
                "timestamp": [report_date],
                "series_id": ["BOE_TOTAL_ASSETS"],
                "source": ["boe_scraping"],
                "value": [total_assets],
                "unit": ["millions_gbp"],
            }
        )

    async def _collect_via_fred_proxy(
        self, start_date: datetime | None, end_date: datetime | None
    ) -> pd.DataFrame:
        """Tier 2: Use FRED UK M4 as correlation proxy."""
        from liquidity.collectors.fred import FredCollector

        fred = FredCollector()
        # MYAGM4GBM189N = UK M4 money supply
        df = await fred.collect(["MYAGM4GBM189N"], start_date, end_date)

        if df.empty:
            raise CollectorFetchError("FRED UK M4 returned no data")

        # Scale M4 to estimate BoE total assets
        # M4 ~3 trillion GBP, BoE assets ~850 billion = ~28% ratio
        df = df.copy()
        df["value"] = df["value"] * 0.28
        df["series_id"] = "BOE_TOTAL_ASSETS"
        df["source"] = "fred_proxy"
        df["unit"] = "millions_gbp"

        logger.info("Using FRED UK M4 as BoE proxy (correlation-based)")
        return df[["timestamp", "series_id", "source", "value", "unit"]]

    def _get_cached_baseline(self) -> pd.DataFrame:
        """Tier 3: Return cached baseline (GUARANTEED)."""
        return pd.DataFrame(
            {
                "timestamp": [pd.to_datetime(self.BASELINE_DATE)],
                "series_id": ["BOE_TOTAL_ASSETS"],
                "source": ["cached_baseline"],
                "value": [float(self.BASELINE_VALUE)],
                "unit": ["millions_gbp"],
                "stale": [True],
            }
        )


# Register collector
registry.register("boe", BOECollector)
