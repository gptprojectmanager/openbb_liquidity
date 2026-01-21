# Global Liquidity Monitor (OpenBB)

## What This Is

A FAANG-grade global liquidity monitoring system based on Arthur Hayes' framework. Tracks >85% of global monetary flows from central banks, overnight markets, and institutional investors using OpenBB as unified data platform. Integrates with NautilusTrader for macro-filtered trading strategies.

## Core Value

**Real-time regime classification** — Know instantly whether we're in Expansionary, Neutral, or Contractionary liquidity regime to inform trading decisions.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Net Liquidity Index (Hayes formula: WALCL - TGA - RRP)
- [ ] Global Liquidity Index (Fed + ECB + BoJ + PBoC in USD)
- [ ] Tier 1 CB collectors (Fed, ECB, BoJ, PBoC, BoE, SNB, BoC)
- [ ] Overnight rates monitoring (SOFR, €STR, SONIA, CORRA)
- [ ] Bonds & volatility tracking (MOVE, VIX, yield curve, credit spreads)
- [ ] Stealth QE Score calculation (port from Apps Script)
- [ ] Regime classifier (Expansionary/Neutral/Contractionary)
- [ ] FastAPI REST server for data access
- [ ] Discord webhook alerts for regime changes
- [ ] Plotly dashboards (HTML exportable)
- [ ] NautilusTrader macro filter integration
- [ ] Double-entry validation for data consistency
- [ ] >85% global monetary flow coverage

### Out of Scope

- Real-time intraday updates — daily/weekly sufficient for macro analysis
- Bloomberg Terminal integration — too expensive ($24k/year), use free APIs
- Shadow banking tracking — opaque, unreliable data
- Crypto flow tracking — future phase, not MVP

## Context

**Reference implementation:** `.planning/reference/appscript_v3.4.1.md` — Apps Script da portare (Stealth QE formula, thresholds, FRED series codes)

**Origin:** Arthur Hayes "Frowny Cloud" article analysis showing Bitcoin correlation with dollar liquidity (0.7-0.8).

**Current state:** Google Apps Script v3.4.1 exists with basic Fed/ECB/BoJ tracking but has:
- Limited backtest capability
- No trading system integration
- Google quota/timeout limitations
- No real-time alerting

**Key insight from Hayes:**
- RMP (Reserve Management Purchases) is new Fed mechanism (Dec 2025) for liquidity injection
- Swap lines between Fed and 5 major CBs are critical stress indicators
- Gold flows (via Switzerland to China/India) indicate de-dollarization

**Data sources confirmed:**
- FRED API (Fed, ECB, BoJ, rates, bonds) — free, reliable
- ECB SDW API — free, reliable
- BIS SDMX API — free, quarterly lag
- Yahoo Finance (MOVE, VIX) — free
- NY Fed Data Hub (RMP, repo) — free
- PBoC — monthly lag, scraping required

## Constraints

- **Tech stack**: Python 3.11+, OpenBB SDK, uv package manager — standard for trading systems
- **Storage**: QuestDB for time-series — already in use for NautilusTrader
- **Visualization**: Plotly Dash — no Grafana dependency for this project
- **Integration**: Must work with NautilusTrader nightly (v1.222.0+)
- **Data lag**: Accept 1-day lag for Tier 1 CB, 10-15 days for PBoC
- **Coverage target**: >85% global monetary flows

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Standalone repo `/media/sam/1TB/openbb_liquidity` | Separation of concerns (macro ≠ trading) | — Pending |
| OpenBB as data platform | 100+ providers, Python native, LLM-ready | — Pending |
| Plotly over Grafana | Simpler deployment, HTML export, no extra service | — Pending |
| Port Apps Script to Python | Remove Google limitations, enable backtest/integration | — Pending |
| Double-entry validation | Ensure data consistency via accounting checks | — Pending |
| 5 milestone structure | Balance between granularity and manageability | — Pending |

---
*Last updated: 2026-01-21 after initialization from ~/.claude/plans/central_banks_openBB.md*
