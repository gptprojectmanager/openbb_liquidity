# Phase 2: Robust Fallback Strategies

## Problem Statement

Two collectors have fragile primary data sources (HTML scraping):
1. **BoE (02-03)**: Database API returns 403, must scrape weekly report HTML
2. **PBoC (02-05)**: No API, must scrape official website HTM/XLS files

## Solution: Multi-Tier Fallback Architecture

### Strategy Pattern

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Primary    │────►│  Fallback 1 │────►│  Fallback 2 │────►│  Fallback 3 │
│  (Scraping) │     │  (Alt API)  │     │  (FRED)     │     │  (Cache)    │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
     ↓ fail              ↓ fail              ↓ fail              ↓ success
   log warning        log warning         log warning       return cached
```

---

## BoE Collector (02-03) - Robust Strategy

### Tier 1: Weekly Report Scraping (Primary)
- **URL**: `https://www.bankofengland.co.uk/weekly-report/YYYY/DD-month-YYYY`
- **Method**: BeautifulSoup + regex extraction
- **Reliability**: LOW (HTML structure may change)
- **Data**: Sum asset components → total assets (~£790-850bn)

### Tier 2: BoE XML API (Fallback 1)
- **URL**: `https://www.bankofengland.co.uk/boeapps/database/_iadb-fromshowcolumns.asp?xml.x=yes&...`
- **Series**: Need to discover current codes (RPWB75A discontinued 2014)
- **Reliability**: MEDIUM (if series codes found)
- **Note**: The XML API exists and works, but current series codes are unknown

### Tier 3: FRED UK Broad Money (Fallback 2)
- **Series**: `MABMM401GBM189S` (UK M4 Broad Money, % of GDP)
- **Alternative**: `MYAGM4GBM189N` (UK M4, level)
- **Reliability**: HIGH (FRED is reliable)
- **Caveat**: M4 ≠ CB balance sheet, but correlates with BoE expansion/contraction
- **Usage**: Scale by known baseline to estimate total assets

### Tier 4: Cached/Baseline (Fallback 3)
- **Baseline**: £848 billion (November 2025)
- **Reliability**: GUARANTEED (always returns a value)
- **Usage**: Return baseline with `stale=True` flag, log warning

### Implementation Pattern

```python
class BOECollector(BaseCollector[pd.DataFrame]):
    BASELINE_VALUE = 848_000  # millions GBP (Nov 2025)
    BASELINE_DATE = "2025-11-26"

    async def collect(self, ...) -> pd.DataFrame:
        # Tier 1: Try scraping
        try:
            return await self._collect_via_scraping()
        except Exception as e:
            logger.warning(f"BoE scraping failed: {e}")

        # Tier 2: Try XML API (if series codes discovered)
        try:
            return await self._collect_via_xml_api()
        except Exception as e:
            logger.warning(f"BoE XML API failed: {e}")

        # Tier 3: Try FRED M4 proxy
        try:
            return await self._collect_via_fred_proxy()
        except Exception as e:
            logger.warning(f"BoE FRED proxy failed: {e}")

        # Tier 4: Return cached baseline
        logger.warning(f"All BoE sources failed, returning cached baseline")
        return self._get_cached_baseline()
```

---

## PBoC Collector (02-05) - Robust Strategy

### Tier 1: Official Website Scraping (Primary)
- **URL**: `http://www.pbc.gov.cn/en/3688247/3688975/3718249/4503799/index.html`
- **Method**: BeautifulSoup, download HTM/XLS files
- **Reliability**: LOW (Chinese gov websites change frequently)
- **Data**: Total assets in 100 million CNY (亿元)

### Tier 2: FRED China Foreign Reserves (Fallback - **ROBUST**)
- **Series**: `TRESEGCNM052N`
- **Reliability**: HIGH (FRED is reliable, same as Apps Script v3.4.1)
- **Data**: Monthly, millions USD
- **Caveat**: Foreign reserves ≠ full balance sheet, but major component

### Tier 3: Cached/Baseline (Fallback 2)
- **Baseline**: 47,296,970 (100 million CNY = ~47.3 trillion CNY, Nov 2025)
- **Reliability**: GUARANTEED
- **Usage**: Return baseline with `stale=True` flag

### Implementation Pattern

```python
class PBOCCollector(BaseCollector[pd.DataFrame]):
    BASELINE_VALUE = 47_296_970  # 100 million CNY units
    BASELINE_DATE = "2025-11-30"

    async def collect(self, ...) -> pd.DataFrame:
        # Tier 1: Try scraping
        try:
            return await self._collect_via_scraping()
        except Exception as e:
            logger.warning(f"PBoC scraping failed: {e}")

        # Tier 2: FRED foreign reserves (reliable!)
        try:
            return await self._collect_via_fred(...)
        except Exception as e:
            logger.warning(f"PBoC FRED fallback failed: {e}")

        # Tier 3: Return cached baseline
        logger.warning(f"All PBoC sources failed, returning cached baseline")
        return self._get_cached_baseline()
```

---

## Key Insights

1. **PBoC is already robust** - FRED TRESEGCNM052N fallback is the same approach Apps Script v3.4.1 used. Foreign reserves are a reasonable proxy for CB liquidity impact.

2. **BoE needs work** - The database API is blocked (403), and the FRED series (BOEBSTAUKA) is discontinued. The multi-tier fallback with cached baseline ensures we always return a value.

3. **Cached baselines are acceptable** - For liquidity analysis, direction/magnitude of changes matter more than exact values. Returning a stale value with warning is better than failing.

4. **Logging is critical** - Each fallback tier must log warnings so we can monitor which sources are failing and prioritize fixes.

---

## Confidence Scores After Robust Strategy

| Collector | Primary | Fallback | Overall Confidence |
|-----------|---------|----------|-------------------|
| BoE | LOW (scraping) | MEDIUM (cached) | 🟡 **MEDIUM** |
| PBoC | LOW (scraping) | HIGH (FRED) | 🟢 **HIGH** |

---

## Action Items

1. **02-03 (BoE)**: Update plan to implement multi-tier fallback with cached baseline
2. **02-05 (PBoC)**: Already robust, just ensure FRED fallback is prominent
3. **Monitoring**: Add metrics for fallback tier usage in production
