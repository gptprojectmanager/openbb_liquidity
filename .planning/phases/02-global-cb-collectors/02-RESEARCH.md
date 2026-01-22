# Phase 2: Global CB Collectors - Research

**Researched:** 2026-01-22
**Domain:** Central bank balance sheet data collectors (ECB, BoJ, PBoC, BoE, SNB, BoC)
**Confidence:** HIGH

<reference_implementation>
## Reference: Apps Script v3.4.1

See: `.planning/reference/appscript_v3.4.1.md`

The existing Apps Script implementation provides the baseline for global CB data:

**FRED Series Used:**
- `ECBASSETSW`: ECB Total Assets (EUR millions) — converted to USD
- `JPNASSETS`: BoJ Total Assets (JPY 100 million) — converted to USD
- `TRESEGCNM052N`: China Foreign Reserves (USD millions) — proxy for PBoC

**Unit Conversions Applied:**
- ECB: `ECBASSETSW / 1000` → billions EUR, then `* EURUSD` → billions USD
- BoJ: `JPNASSETS / 10000` → trillions JPY, then `* 1000 / JPYUSD` → billions USD
- China: Foreign reserves used as proxy (not full balance sheet)

**Global Liquidity Formula:**
```
globalLiquidity = fedNetLiq + ecbUSD + bojUSD + chinaUSD
```

**Key Insight:** Apps Script uses FRED for ECB and BoJ (via `ECBASSETSW`, `JPNASSETS`), but uses foreign reserves for China as a proxy — not actual PBoC balance sheet. Phase 2 should improve on this by attempting to get actual PBoC total assets.
</reference_implementation>

<research_summary>
## Summary

Researched data access strategies for 6 central banks beyond the Fed. The landscape divides into three tiers:

1. **FRED-available** (simplest): ECB, BoJ, BoE have total assets series on FRED — use existing FredCollector pattern
2. **Official API**: ECB SDW, BoC Valet have well-documented REST APIs with Python wrappers
3. **Scraping required**: PBoC has no API — requires HTML/PDF scraping or paid data providers (CEIC, Trading Economics)

Key finding: FRED hosts ECB (ECBASSETSW), BoJ (JPNASSETS), and BoE (BOEBSTAUKA) total assets series. This means 3 of 6 CBs can reuse the existing FredCollector with just new series IDs. For granular breakdowns, go to source APIs.

**Primary recommendation:** Use FRED for totals (reuse FredCollector), build source API collectors for breakdowns and CBs not on FRED (PBoC, SNB, BoC).
</research_summary>

<standard_stack>
## Standard Stack

### Core (Already in Project)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| fredapi | 0.5.2 | FRED API access | OpenBB uses it internally, well-maintained |
| httpx | 0.27+ | Async HTTP client | Already in base collector for requests |
| pandas | 2.0+ | Data manipulation | Already used for DataFrame handling |
| tenacity | 8.0+ | Retry logic | Already in BaseCollector |

### New for Phase 2
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pandasdmx/sdmx1 | 1.10+ | SDMX protocol (ECB, BIS) | ISO 17369 standard, handles SDMX complexity |
| pyvalet | 0.2+ | Bank of Canada Valet API | Official wrapper, pandas-integrated |
| bojpy | 0.1+ | Bank of Japan time-series | Direct BoJ portal access |
| beautifulsoup4 | 4.12+ | HTML parsing (PBoC) | Standard for web scraping |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| pandasdmx | sdmx1 fork | sdmx1 is actively maintained, pandasdmx dormant |
| Direct API calls | ecbdata library | ecbdata is simpler but less flexible |
| Scraping PBoC | CEIC/Trading Economics API | Paid services ($$$) but more reliable |

**Installation:**
```bash
uv add sdmx1 pyvalet bojpy beautifulsoup4 lxml
```
</standard_stack>

<data_sources>
## Data Sources by Central Bank

### ECB (European Central Bank)
**Primary:** ECB Data Portal API (replaced SDW)
- **Base URL:** `https://data-api.ecb.europa.eu`
- **Format:** SDMX 2.1 RESTful
- **Auth:** None required (public)
- **Rate limits:** Not documented, be respectful
- **Key series:** `ILM.W.U2.C.T000000.Z5.Z01` (Total assets/liabilities, weekly, EUR millions)
- **FRED fallback:** `ECBASSETSW` (weekly, millions EUR)

**Python access:**
```python
# Via sdmx1
import sdmx
ecb = sdmx.Client('ECB')
data = ecb.data('ILM', key={'ITEM': 'T000000', 'REF_AREA': 'U2'})
```

### BoJ (Bank of Japan)
**Primary:** FRED (simplest)
- **FRED series:** `JPNASSETS` (monthly, millions JPY)
- **Update frequency:** Monthly

**Alternative:** BoJ Time-Series Data Search
- **Portal:** https://www.stat-search.boj.or.jp/index_en.html
- **Updates:** 3x daily (9:00, 12:00, 15:00 JST)
- **Python:** bojpy wrapper or direct HTTP

**Python access:**
```python
# Via FRED (recommended for totals)
fred = Fred(api_key='...')
boj_assets = fred.get_series('JPNASSETS')

# Via bojpy (for breakdowns)
from bojpy import boj
df = boj.get_data_series(series="BS01'MABJMTA")
```

### PBoC (People's Bank of China)
**Primary:** Official website + scraping (no API)
- **Source:** http://www.pbc.gov.cn/en/3688247/3688975/index.html
- **Update frequency:** Monthly (with ~1 month lag)
- **Format:** HTML tables, PDF reports

**Alternative:** Paid data providers
- CEIC Data (comprehensive, API available)
- Trading Economics (API available)
- MacroMicro (charts, limited API)

**Python access:**
```python
# Scraping approach
import httpx
from bs4 import BeautifulSoup

async def fetch_pboc_balance_sheet():
    url = "http://www.pbc.gov.cn/en/3688247/3688975/3718249/4503799/index.html"
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        soup = BeautifulSoup(response.text, 'lxml')
        # Parse table for total assets
```

### BoE (Bank of England)
**Primary:** FRED
- **FRED series:** `BOEBSTAUKA` (quarterly, GBP millions) — **DISCONTINUED as of 2016**
- **Note:** FRED series ends at 2016, need alternative

**Alternative:** BoE Database
- **Portal:** https://www.bankofengland.co.uk/boeapps/database/
- **Weekly report:** https://www.bankofengland.co.uk/weekly-report/balance-sheet-and-weekly-report
- **Last updated:** 21 January 2026

**Python access:**
```python
# BoE publishes downloadable data
# Use httpx to fetch CSV from their database
```

### SNB (Swiss National Bank)
**Primary:** SNB Data Portal
- **Portal:** https://data.snb.ch/en
- **Format:** CSV, Excel downloads
- **Key identifier:** `BIL.AKT` prefix for balance sheet assets

**FRED series:** `SNBREMBALPOS` and 10 other SNB series (less useful for total assets)

**Python access:**
```python
# SNB data portal allows direct CSV download
# Parse with pandas
import pandas as pd
url = "https://data.snb.ch/api/cube/snbbipo/data/csv/en"
df = pd.read_csv(url)
```

### BoC (Bank of Canada)
**Primary:** Valet API (excellent, no auth required)
- **Base URL:** https://www.bankofcanada.ca/valet
- **Docs:** https://www.bankofcanada.ca/valet/docs
- **Auth:** None required
- **Formats:** JSON, CSV, XML
- **Cost:** Free

**Python access:**
```python
from pyvalet import ValetInterpreter
vi = ValetInterpreter()

# Get available series
series = vi.get_all_series()

# Fetch balance sheet data
obs = vi.get_series_observations('BOC_BALANCE_SHEET_SERIES_ID')
```
</data_sources>

<architecture_patterns>
## Architecture Patterns

### Recommended Project Structure
```
src/liquidity/collectors/
├── base.py              # BaseCollector (existing)
├── registry.py          # Collector registry (existing)
├── fred.py              # FredCollector (existing, extend with ECB/BoJ series)
├── ecb.py               # ECBCollector (SDMX for breakdowns)
├── boj.py               # BOJCollector (bojpy for breakdowns)
├── pboc.py              # PBOCCollector (scraping)
├── boe.py               # BOECollector (BoE database)
├── snb.py               # SNBCollector (SNB data portal)
└── boc.py               # BOCCollector (Valet API)
```

### Pattern 1: FRED Extension for Totals
**What:** Add ECB/BoJ/BoE series to existing FredCollector
**When to use:** For total assets when FRED has the series
**Example:**
```python
# Extend SERIES_MAP in fred.py
SERIES_MAP.update({
    # Global CB totals (Phase 2)
    "ecb_total_assets": "ECBASSETSW",  # Weekly, millions EUR
    "boj_total_assets": "JPNASSETS",   # Monthly, millions JPY
    # Note: BOEBSTAUKA discontinued, use direct BoE source
})

UNIT_MAP.update({
    "ECBASSETSW": "millions_eur",
    "JPNASSETS": "millions_jpy",
})
```

### Pattern 2: Source API Collector
**What:** Dedicated collector for official CB API
**When to use:** For breakdowns or CBs without FRED coverage
**Example:**
```python
class ECBCollector(BaseCollector[pd.DataFrame]):
    """ECB collector using SDMX API for detailed balance sheet."""

    def __init__(self, name: str = "ecb", **kwargs):
        super().__init__(name=name, **kwargs)
        self._client = sdmx.Client('ECB')

    async def collect(
        self,
        breakdown: bool = False,
        start_date: datetime | None = None,
    ) -> pd.DataFrame:
        async def _fetch():
            return await asyncio.to_thread(self._fetch_sync, breakdown)
        return await self.fetch_with_retry(_fetch)

    def _fetch_sync(self, breakdown: bool) -> pd.DataFrame:
        key = {'REF_AREA': 'U2', 'ITEM': 'T000000'}
        data = self._client.data('ILM', key=key)
        df = sdmx.to_pandas(data)
        # Normalize to standard format
        return self._normalize(df)
```

### Pattern 3: Scraping Collector with Caching
**What:** Collector for sites without API (PBoC)
**When to use:** When only HTML/PDF data available
**Example:**
```python
class PBOCCollector(BaseCollector[pd.DataFrame]):
    """PBoC collector via web scraping (monthly lag)."""

    BALANCE_SHEET_URL = "http://www.pbc.gov.cn/en/3688247/3688975/3718249/4503799/index.html"

    async def collect(self) -> pd.DataFrame:
        async def _fetch():
            async with httpx.AsyncClient() as client:
                response = await client.get(self.BALANCE_SHEET_URL)
                response.raise_for_status()
                return self._parse_html(response.text)
        return await self.fetch_with_retry(_fetch)

    def _parse_html(self, html: str) -> pd.DataFrame:
        soup = BeautifulSoup(html, 'lxml')
        # Find balance sheet table
        table = soup.find('table', class_='balance-sheet')
        # Parse rows for total assets
        ...
```

### Anti-Patterns to Avoid
- **Hardcoding URLs:** Use constants or config, sources may change
- **Ignoring rate limits:** Add delays between requests, even if undocumented
- **Sync blocking:** Always use `asyncio.to_thread()` for sync libraries
- **Assuming data format stability:** PBoC HTML may change, add parsing tests
</architecture_patterns>

<dont_hand_roll>
## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| SDMX parsing | Custom XML parser | sdmx1/pandasdmx | SDMX is complex, many edge cases |
| FRED API wrapper | httpx + manual parsing | fredapi or OpenBB | Rate limits, pagination handled |
| BoC data fetch | httpx + JSON parsing | pyvalet | Pandas integration, series discovery |
| Retry + backoff | Custom retry loops | tenacity (already using) | Battle-tested, configurable |
| Circuit breaker | Custom state machine | purgatory (already using) | Handles edge cases correctly |
| HTML table parsing | Regex | BeautifulSoup + pandas.read_html | Robust to whitespace, encoding |

**Key insight:** Central bank APIs vary wildly — SDMX (ECB), REST (BoC), flat files (BoJ), HTML (PBoC). Using existing wrappers saves massive debugging time. The sdmx1 library alone saves weeks of SDMX spec reading.
</dont_hand_roll>

<common_pitfalls>
## Common Pitfalls

### Pitfall 1: Currency Confusion
**What goes wrong:** Mixing EUR, JPY, CNY, GBP, CHF, CAD values without conversion
**Why it happens:** Each CB reports in native currency
**How to avoid:** Store original currency + explicit unit field, convert to USD only in Phase 7 when FX data available
**Warning signs:** Numbers off by orders of magnitude

### Pitfall 2: FRED Series Discontinuation
**What goes wrong:** Using discontinued FRED series (e.g., ECBASSETS → ECBASSETSW, BOEBSTAUKA discontinued 2016)
**Why it happens:** FRED sometimes replaces series without clear deprecation
**How to avoid:** Check FRED page for "DISCONTINUED" label, use weekly series over annual when available
**Warning signs:** Data stops at old date, missing recent observations

### Pitfall 3: PBoC Data Lag
**What goes wrong:** Assuming all CBs have same freshness
**Why it happens:** PBoC publishes with ~1 month lag
**How to avoid:** Track `last_updated` timestamp per source, don't fail on stale data
**Warning signs:** PBoC data always seems old

### Pitfall 4: SDMX Complexity
**What goes wrong:** Spending days debugging SDMX queries
**Why it happens:** SDMX has dimensions, attributes, codelists — not intuitive
**How to avoid:** Use sdmx1 library, start with ECB data browser to find series keys
**Warning signs:** Getting empty results, cryptic error messages

### Pitfall 5: Rate Limiting (Silent)
**What goes wrong:** Collector works in tests, fails in prod under load
**Why it happens:** Most CBs don't document rate limits but will block aggressive requests
**How to avoid:** Add 1s delay between requests, implement backoff on 429/503
**Warning signs:** Random failures, HTTP 429/503 errors

### Pitfall 6: BoE Data Access
**What goes wrong:** Assuming BoE works like ECB or Fed
**Why it happens:** BoE database is different — weekly report format, no standard API
**How to avoid:** Use BoE weekly balance sheet CSV download, not FRED (discontinued)
**Warning signs:** BOEBSTAUKA data ends at 2016
</common_pitfalls>

<code_examples>
## Code Examples

### FRED Extension for Global CBs
```python
# Source: Existing fred.py pattern
# Add to SERIES_MAP
SERIES_MAP.update({
    # Phase 2: Global CB totals via FRED
    "ecb_total_assets": "ECBASSETSW",  # Weekly, millions EUR
    "boj_total_assets": "JPNASSETS",   # Monthly, millions JPY
})

UNIT_MAP.update({
    "ECBASSETSW": "millions_eur",
    "JPNASSETS": "millions_jpy",
})
```

### ECB SDMX Collector
```python
# Source: sdmx1 documentation + ECB Data Portal
import sdmx

def fetch_ecb_balance_sheet() -> pd.DataFrame:
    ecb = sdmx.Client('ECB')

    # ILM = Internal Liquidity Management dataset
    # T000000 = Total assets/liabilities
    # U2 = Euro area
    msg = ecb.data(
        'ILM',
        key={'REF_AREA': 'U2', 'BS_ITEM': 'T000000'}
    )

    df = sdmx.to_pandas(msg)
    df = df.reset_index()
    df.columns = ['timestamp', 'value']
    df['series_id'] = 'ECB_TOTAL_ASSETS'
    df['source'] = 'ecb_sdw'
    df['unit'] = 'millions_eur'

    return df[['timestamp', 'series_id', 'source', 'value', 'unit']]
```

### BoC Valet Collector
```python
# Source: pyvalet documentation
from pyvalet import ValetInterpreter

def fetch_boc_balance_sheet() -> pd.DataFrame:
    vi = ValetInterpreter()

    # Discover available series
    # series = vi.get_all_series()

    # Fetch balance sheet (need to find exact series ID)
    obs = vi.get_series_observations('BALANCE_SHEET_SERIES_ID')

    df = obs.copy()
    df['series_id'] = 'BOC_TOTAL_ASSETS'
    df['source'] = 'boc_valet'
    df['unit'] = 'millions_cad'

    return df
```

### PBoC Scraping Pattern
```python
# Source: Community pattern for Chinese CB data
import httpx
from bs4 import BeautifulSoup
import pandas as pd

async def fetch_pboc_balance_sheet() -> pd.DataFrame:
    """Fetch PBoC balance sheet via web scraping.

    Note: HTML structure may change. Add tests for parsing logic.
    """
    url = "http://www.pbc.gov.cn/en/3688247/3688975/3718249/4503799/index.html"

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url)
        response.raise_for_status()

    soup = BeautifulSoup(response.text, 'lxml')

    # PBoC tables have class "data_table" or similar
    tables = soup.find_all('table')

    for table in tables:
        # Look for "Total Assets" row
        if 'Total Assets' in table.get_text():
            df = pd.read_html(str(table))[0]
            # Parse and normalize...
            break

    # Normalize to standard format
    result = pd.DataFrame({
        'timestamp': [...],
        'series_id': 'PBOC_TOTAL_ASSETS',
        'source': 'pboc_website',
        'value': [...],
        'unit': 'hundreds_millions_cny',  # PBoC reports in 100 million CNY
    })

    return result
```
</code_examples>

<sota_updates>
## State of the Art (2025-2026)

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| ECB SDW (sdw-wsrest.ecb.europa.eu) | ECB Data Portal (data-api.ecb.europa.eu) | Oct 2025 | Old URLs redirect for 1 year, then break |
| FRED ECBASSETS (monthly) | FRED ECBASSETSW (weekly) | 2024 | Higher frequency available |
| FRED BOEBSTAUKA | BoE Database direct | 2016 | FRED series discontinued |
| pandasdmx | sdmx1 | 2023+ | pandasdmx dormant, sdmx1 actively maintained |

**New tools/patterns to consider:**
- **ecbdata library**: Simpler than sdmx1 for basic ECB queries, pandas-native
- **SDW → EDP migration**: ECB completed transition Jan 2026, use new URLs

**Deprecated/outdated:**
- **sdw-wsrest.ecb.europa.eu**: Redirects to data-api.ecb.europa.eu, will stop Oct 2026
- **pandasdmx**: Last release 12+ months ago, use sdmx1 fork instead
- **BOEBSTAUKA FRED series**: Discontinued 2016, use BoE weekly report
</sota_updates>

<open_questions>
## Open Questions

1. **PBoC Scraping Reliability**
   - What we know: PBoC website publishes monthly balance sheet data
   - What's unclear: HTML structure stability, handling of Chinese language pages
   - Recommendation: Build scraper with robust parsing tests, consider paid fallback (CEIC/Trading Economics)

2. **BoE Data Format**
   - What we know: BoE publishes weekly balance sheet, FRED series discontinued
   - What's unclear: Exact download URL and CSV format
   - Recommendation: Research BoE database API during implementation

3. **SNB Total Assets Series**
   - What we know: SNB data portal exists with CSV downloads
   - What's unclear: Which series ID maps to total assets
   - Recommendation: Explore SNB data portal to find exact series before implementation

4. **Unit Standardization**
   - What we know: Each CB uses different units (millions, billions, hundreds of millions)
   - What's unclear: Exact multipliers for each
   - Recommendation: Document units in UNIT_MAP, convert to common base (USD millions) in Phase 7
</open_questions>

<sources>
## Sources

### Primary (HIGH confidence)
- [ECB Data Portal API](https://data.ecb.europa.eu/help/api/overview) - Official API docs
- [FRED ECBASSETSW](https://fred.stlouisfed.org/series/ECBASSETSW) - ECB total assets weekly
- [FRED JPNASSETS](https://fred.stlouisfed.org/series/JPNASSETS) - BoJ total assets monthly
- [Bank of Canada Valet API](https://www.bankofcanada.ca/valet/docs) - Official API docs
- [SNB Data Portal](https://data.snb.ch/en) - Official data portal

### Secondary (MEDIUM confidence)
- [sdmx1 GitHub](https://github.com/dr-leo/pandaSDMX) - SDMX library docs
- [pyvalet PyPI](https://pypi.org/project/pyvalet/) - BoC API wrapper
- [bojpy GitHub](https://github.com/philsv/bojpy) - BoJ data wrapper
- [fredapi PyPI](https://pypi.org/project/fredapi/) - FRED API wrapper

### Tertiary (LOW confidence - needs validation)
- PBoC website structure - needs verification during implementation
- BoE weekly report format - needs verification during implementation
- SNB total assets series ID - needs verification during implementation
</sources>

<metadata>
## Metadata

**Research scope:**
- Core technology: Central bank REST/SDMX APIs, web scraping
- Ecosystem: fredapi, sdmx1, pyvalet, bojpy, beautifulsoup4
- Patterns: FRED extension, source API collectors, scraping with caching
- Pitfalls: Currency confusion, discontinued series, rate limiting, SDMX complexity

**Confidence breakdown:**
- Standard stack: HIGH - fredapi, sdmx1, pyvalet are well-documented
- Architecture: HIGH - Extends existing BaseCollector pattern
- Pitfalls: HIGH - Based on FRED documentation, ECB migration notices
- Code examples: MEDIUM - Need validation for PBoC, BoE, SNB specifics

**Research date:** 2026-01-22
**Valid until:** 2026-02-22 (30 days - CB APIs relatively stable)
</metadata>

---

*Phase: 02-global-cb-collectors*
*Research completed: 2026-01-22*
*Ready for planning: yes*
