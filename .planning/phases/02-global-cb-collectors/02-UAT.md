---
status: complete
phase: 02-global-cb-collectors
source: test_global_cb_collectors.py (tests as spec)
started: 2026-01-22T14:30:00Z
updated: 2026-01-22T14:35:00Z
---

## Current Test

[testing complete]

## Tests

### 1. SNB Collector Fetches Data
expected: Run SNB collector, get data with ~800-900 billion CHF total assets
result: pass
output: "SNB: 348 rows, latest: 896,722 million CHF"

### 2. BoC Collector Fetches Data
expected: Run BoC collector, get data with ~200-400 billion CAD total assets
result: pass
output: "BoC: 2352 rows, latest: 251,446 million CAD"

### 3. BoE Collector Returns Data (Fallback)
expected: Run BoE collector, ALWAYS returns data (may be from fallback/cached baseline)
result: pass
output: "BoE: 1 rows, source: cached_baseline, value: 848,000 million GBP"
note: Tier 1 (scraping) got 403, Tier 2 (FRED) needs API key, Tier 3 (cached) worked as designed

### 4. PBoC Collector Returns Data (Fallback)
expected: Run PBoC collector, ALWAYS returns data (may be from fallback/cached baseline)
result: pass
output: "PBoC: 1 rows, source: cached_baseline, value: 47,296,970"
note: Tier 1 (scraping) got 403, Tier 2 (FRED) needs API key, Tier 3 (cached) worked as designed

### 5. All Collectors Registered
expected: Registry lists: fred, boc, boe, snb, pboc, yahoo (6 collectors)
result: pass
output: "Registered collectors (6): ['boc', 'boe', 'fred', 'pboc', 'snb', 'yahoo']"

### 6. ECB/BoJ Series in FRED Collector
expected: FredCollector.SERIES_MAP contains ecb_total_assets and boj_total_assets
result: pass
output: "ECB: ECBASSETSW, BoJ: JPNASSETS"

## Summary

total: 6
passed: 6
issues: 0
pending: 0
skipped: 0

## Issues for /gsd:plan-fix

[none]
