# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-01-22)

**Core value:** Real-time regime classification — Know instantly whether we're in Expansionary, Neutral, or Contractionary liquidity regime to inform trading decisions.
**Current focus:** Phase 3 — Overnight Rates & FX (next)

## Current Position

Phase: 2 of 10 (Global CB Collectors) ✓ COMPLETE
Plan: All 5 plans executed (17/25 tests passed, 8 skipped without API keys)
Status: Ready for Phase 3 planning
Last activity: 2026-01-22 — Phase 2 complete, all global CB collectors implemented

Progress: ████░░░░░░ 20%

## Performance Metrics

**Velocity:**
- Total plans completed: 8
- Average duration: ~8 min
- Total execution time: ~1 hour

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1 | 3/3 | 29 min | 9.7 min |
| 2 | 5/5 | ~35 min | ~7 min |

**Recent Trend:**
- Phase 2 plans executed in parallel (5 concurrent agents)
- Trend: Accelerating via parallelization

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

| Plan | Decision | Rationale |
|------|----------|-----------|
| 01-01 | purgatory 0.7.x not 1.x | Version 1.0+ doesn't exist yet |
| 01-01 | Added setuptools runtime dep | Required by purgatory for pkg_resources |
| 01-01 | Generic[T] for BaseCollector | Type-safe collector implementations |
| 01-02 | psycopg2-binary for PGWire | Standard PostgreSQL driver for QuestDB |
| 01-02 | MONTH partitioning | Optimal for macro data (daily/weekly) |
| 01-02 | asyncio.to_thread() for OpenBB | OpenBB SDK is sync-only |
| 01-03 | MOVE via Yahoo Finance | Not available in FRED, used OpenBB yfinance |
| 01-03 | Credit spreads in bps | Matches ICE BofA OAS index conventions |
| 02-01 | ECB/BoJ via FRED | ECBASSETSW and JPNASSETS available on FRED |
| 02-02 | BoC Valet API direct | pyvalet wrapper less reliable than direct HTTP |
| 02-03 | BoE multi-tier fallback | Scraping + FRED proxy + cached baseline |
| 02-04 | SNB CSV direct download | No auth required, semicolon-separated CSV |
| 02-05 | PBoC FRED fallback | TRESEGCNM052N as proxy (same as Apps Script) |

### Pending Todos

- Configure FRED API key (LIQUIDITY_FRED_API_KEY) to run integration tests

### Blockers/Concerns

- purgatory shows deprecation warning for pkg_resources (library issue, not ours)
- FRED API key not yet configured (tests skip gracefully)
- BoE scraping returns 403 (fallback working)
- PBoC scraping fragile (FRED fallback reliable)

## Session Continuity

Last session: 2026-01-22
Stopped at: Phase 2 complete. All global CB collectors implemented.
Resume command: `/gsd:plan-phase 3`

### Resume Context
- Phase 1 Foundation complete: uv project, collectors, QuestDB storage
- Phase 2 Global CB complete: ECB, BoJ, PBoC, BoE, SNB, BoC collectors
- GitHub: https://github.com/gptprojectmanager/openbb_liquidity
- Next: Plan Phase 3 (SOFR, €STR, SONIA, CORRA, FX collectors)
- Collectors with robust fallbacks: BoE (3-tier), PBoC (3-tier)
