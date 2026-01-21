# PROJECT: Global Liquidity Monitor (OpenBB)

> **Status**: Planning
> **Created**: 2026-01-21
> **Owner**: gptcompany

## Vision

Build a **FAANG-grade global liquidity monitoring system** based on Arthur Hayes' framework, using OpenBB as the unified data platform. Track >85% of global monetary flows from central banks, overnight markets, and institutional investors.

## Problem Statement

Current liquidity monitoring relies on fragmented Google Apps Script with:
- Limited backtest capability
- No integration with trading systems
- Google quota/timeout limitations
- No real-time alerting

## Solution

Python-native system with:
- 100+ data providers via OpenBB
- NautilusTrader integration for macro-filtered strategies
- Real-time Discord alerts
- Interactive Plotly dashboards
- Double-entry validation for data quality

## Core Metrics

### Hayes Net Liquidity Formula
```
Net Liquidity = Fed Total Assets (WALCL) - TGA - RRP
```

### Global Liquidity Index
```
Global = Fed + ECB + BoJ + PBoC (USD converted)
```

### Coverage Target
- **Tier 1 CB**: Fed, ECB, BoJ, PBoC, BoE, SNB, BoC (~68.6% GDP)
- **Tier 2 CB**: RBI, RBA, BoK, BCB (~9% GDP)
- **BIS Aggregates**: GLI, CBTA (+5%)
- **Money Managers**: Z.1, CFTC, 13F (+5%)
- **Total**: ~87% global monetary flows

## Technical Stack

| Component | Technology |
|-----------|------------|
| Data Platform | OpenBB SDK |
| Language | Python 3.11+ |
| Storage | QuestDB (time-series) |
| Visualization | Plotly Dash |
| Alerts | Discord webhooks |
| Integration | NautilusTrader |
| API | FastAPI |

## Repository

- **Location**: `/media/sam/1TB/openbb_liquidity`
- **GitHub**: `gptcompany/openbb_liquidity`
- **Template**: Claude + Backstage standard

## Key Stakeholders

- Trading systems (NautilusTrader macro filter)
- Research (regime analysis, backtesting)
- Monitoring (real-time alerts)

## Success Criteria

1. [ ] >85% global liquidity coverage
2. [ ] <5% deviation from Apps Script baseline
3. [ ] <1 day data lag for Tier 1 CB
4. [ ] Real-time regime classification
5. [ ] NautilusTrader integration working

## References

- Arthur Hayes "Frowny Cloud" article
- Original plan: `~/.claude/plans/central_banks_openBB.md`
- OpenBB SDK docs: https://docs.openbb.co/
