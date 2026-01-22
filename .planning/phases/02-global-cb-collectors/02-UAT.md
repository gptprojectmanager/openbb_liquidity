---
status: testing
phase: 02-global-cb-collectors
source: test_global_cb_collectors.py (tests as spec)
started: 2026-01-22T14:30:00Z
updated: 2026-01-22T14:30:00Z
---

## Current Test

number: 1
name: SNB Collector Fetches Data
expected: |
  Run: `uv run python -c "import asyncio; from liquidity.collectors.snb import SNBCollector; c = SNBCollector(); df = asyncio.run(c.collect()); print(f'SNB: {len(df)} rows, latest: {df[\"value\"].iloc[-1]:,.0f} million CHF')"`

  Should show: ~300+ rows of data, latest value around 800,000-900,000 million CHF (~800-900 billion CHF)
awaiting: user response

## Tests

### 1. SNB Collector Fetches Data
expected: Run SNB collector, get data with ~800-900 billion CHF total assets
result: [pending]

### 2. BoC Collector Fetches Data
expected: Run BoC collector, get data with ~300-400 billion CAD total assets
result: [pending]

### 3. BoE Collector Returns Data (Fallback)
expected: Run BoE collector, ALWAYS returns data (may be from fallback/cached baseline)
result: [pending]

### 4. PBoC Collector Returns Data (Fallback)
expected: Run PBoC collector, ALWAYS returns data (may be from fallback/cached baseline)
result: [pending]

### 5. All Collectors Registered
expected: Registry lists: fred, boc, boe, snb, pboc, yahoo (6 collectors)
result: [pending]

### 6. ECB/BoJ Series in FRED Collector
expected: FredCollector.SERIES_MAP contains ecb_total_assets and boj_total_assets
result: [pending]

## Summary

total: 6
passed: 0
issues: 0
pending: 6
skipped: 0

## Issues for /gsd:plan-fix

[none yet]
