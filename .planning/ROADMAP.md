# ROADMAP: Global Liquidity Monitor

> **Version**: 1.0
> **Last Updated**: 2026-01-21
> **Total Phases**: 19 (grouped into 5 milestones)

---

## Milestone Overview

| Milestone | Phases | Description | Priority |
|-----------|--------|-------------|----------|
| **M1: MVP Foundation** | 1-4 | Core collectors, overnight, bonds | P0 - Critical |
| **M2: Scoring & Integration** | 5-7 | Stealth QE, API, NautilusTrader | P0 - Critical |
| **M3: Global Coverage** | 8-12 | CB Tier 1b/2, Money Managers, Validation | P1 - High |
| **M4: Quant Infrastructure** | 13-16 | Network, Early Warning, Stress Test | P2 - Medium |
| **M5: ML & Trading** | 17-19 | ML Regime, Edge Detection, Dashboard | P2 - Medium |

---

## M1: MVP Foundation

> **Goal**: Working system with Fed/ECB/BoJ data, overnight rates, bonds/volatility
> **Exit Criteria**: Net Liquidity Index matches Apps Script ±5%

### Phase 1: Foundation & Template Setup
- [ ] Setup repo with Claude + Backstage template
- [ ] `.claude/CLAUDE.md`, `.specify/constitution.md`, `catalog-info.yaml`
- [ ] Implement FRED collector base (Fed + ECB + BoJ)
- [ ] Implement Net Liquidity calculation (Hayes formula)
- [ ] Basic CLI tool for testing
- [ ] Unit tests for collectors

### Phase 2: Global Aggregation + BIS
- [ ] ECB SDW API integration
- [ ] BIS SDMX API integration (GLI, CBTA)
- [ ] PBoC scraper (fallback sources)
- [ ] FX conversion module
- [ ] Global Liquidity Index calculation
- [ ] Integration tests

### Phase 3: Overnight & Stress Indicators
- [ ] SOFR/€STR/SONIA collectors
- [ ] Swap lines monitoring (SWPT series)
- [ ] RMP tracking (NY Fed schedule)
- [ ] Cross-currency basis (research/proxy)
- [ ] Repo market stress indicators
- [ ] `overnight/` module unit tests

### Phase 4: Bonds & Volatility
- [ ] Treasury yields (yield curve)
- [ ] MOVE index (Yahoo Finance)
- [ ] VIX family (VIX, VIX3M, VIX9D)
- [ ] Credit spreads (IG, HY, EM)
- [ ] `bonds/` module unit tests

---

## M2: Scoring & Integration

> **Goal**: Stealth QE Score, Regime Classification, API, NautilusTrader integration
> **Exit Criteria**: E2E validation passes, API serves regime data

### Phase 5: Score & Regime
- [ ] Port Stealth QE Score from Apps Script
- [ ] Implement Regime Classifier (Expansionary/Neutral/Contractionary)
- [ ] Historical backtest validation
- [ ] Compare with Apps Script output
- [ ] E2E tests vs Apps Script

### Phase 6: API & Alerts
- [ ] FastAPI REST server
- [ ] Discord webhook integration
- [ ] Real-time regime alerts
- [ ] Plotly dashboards (HTML export)

### Phase 7: Integration & Deprecation
- [ ] NautilusTrader macro filter
- [ ] QuestDB ingestion pipeline
- [ ] MCP server for Claude (optional)

---

## M3: Global Coverage

> **Goal**: Expand to >85% global coverage with validation layer
> **Exit Criteria**: All Tier 1+2 CB collectors working, double-entry validation passing

### Phase 8: Additional CB Collectors (Tier 1b)
- [ ] Bank of Canada (BoC) Valet API collector
- [ ] CORRA overnight rate integration
- [ ] Bank of England (BoE) API collector
- [ ] Swiss National Bank (SNB) API collector
- [ ] Unit tests for all Tier 1 CB collectors

### Phase 9: CB Tier 2
- [ ] Reserve Bank of India (RBI) DBIE collector
- [ ] Reserve Bank of Australia (RBA) collector
- [ ] Bank of Korea (BoK) ECOS API collector
- [ ] Central Bank of Brazil (BCB) SGS collector
- [ ] Unit tests for Tier 2 collectors
- [ ] FX conversion for all currencies (INR, AUD, KRW, BRL)

### Phase 10: Money Managers & Institutional Flows
- [ ] Fed Flow of Funds (Z.1) collector
- [ ] CFTC Commitments of Traders collector
- [ ] ICI fund flows collector
- [ ] SEC 13F parser (top institutions)
- [ ] ETF flows via OpenBB
- [ ] `flows/` module unit tests

### Phase 11: Double-Entry Validation
- [ ] Implement DoubleEntryValidator class
- [ ] CB balance sheet validation checks
- [ ] Swap lines cross-validation
- [ ] Net liquidity decomposition check
- [ ] Cross-source consistency checks
- [ ] Daily reconciliation job (cron)
- [ ] Discord alerts for validation failures
- [ ] Validation dashboard panel

### Phase 12: Coverage Optimization
- [ ] Verify >85% coverage target achieved
- [ ] Implement missing gap mitigations (BIS FSB, SWFs)
- [ ] Data freshness monitoring
- [ ] Automated data quality scoring
- [ ] Documentation and runbooks
- [ ] Deprecate Apps Script (migration script)
- [ ] Full E2E validation

---

## M4: Quant Infrastructure

> **Goal**: Network analysis, early warning, stress testing
> **Exit Criteria**: EWS alerts validated against 2020-03, 2022-09 events

### Phase 13: Network Analysis Module
- [ ] Implement EntityRegistry with CB, bank, money manager entities
- [ ] Define relationship types (LENDER_OF_LAST_RESORT, SWAP_LINE, etc.)
- [ ] Build DependencyGraph class with NetworkX integration
- [ ] Implement centrality metrics (PageRank, betweenness, closeness)
- [ ] Build ContagionSimulator with cascade modeling
- [ ] Network visualization export (Plotly network graph)
- [ ] Unit tests for graph algorithms

### Phase 14: Early Warning System
- [ ] Implement EarlyWarningSystem class
- [ ] Define 4-tier alert levels (GREEN/YELLOW/ORANGE/RED)
- [ ] Configure lead indicators (SOFR-EFFR spread, RRP velocity, etc.)
- [ ] Historical threshold calibration (percentile-based)
- [ ] Implement alerting pipeline (Discord + Email)
- [ ] Build alert dashboard panel
- [ ] Backtesting: validate alerts for 2020-03, 2022-09 events

### Phase 15: Lead/Lag Analysis
- [ ] Implement LeadLagAnalyzer class
- [ ] Granger causality test implementation
- [ ] Cross-correlation analysis with variable lags (1-90 days)
- [ ] Rolling correlation matrix calculation
- [ ] Lead indicator composite scoring
- [ ] Historical pattern matching
- [ ] CLI command: `analyze lead-lag --indicator SOFR`

### Phase 16: Stress Testing & Scenarios
- [ ] Implement StressTestEngine class
- [ ] Define 6 predefined scenarios (Lehman, COVID, China Deval, etc.)
- [ ] Monte Carlo simulation (10,000 runs)
- [ ] Shock propagation through dependency network
- [ ] Portfolio impact estimation
- [ ] Confidence interval calculation (5th/50th/95th percentiles)
- [ ] Stress test report generation (PDF/HTML)

---

## M5: ML & Trading

> **Goal**: ML regime detection, edge detection, real-time trading dashboard
> **Exit Criteria**: ML ensemble accuracy >70%, dashboard live

### Phase 17: ML Regime Detection
- [ ] Implement MLRegimeDetector ensemble class
- [ ] Hidden Markov Model (HMM) implementation
- [ ] Gaussian Mixture Model (GMM) implementation
- [ ] LSTM neural network for sequence modeling
- [ ] Random Forest for regime classification
- [ ] Ensemble voting mechanism (weighted average)
- [ ] Feature engineering pipeline (Z-scores, momentum, volatility)
- [ ] Model training/retraining pipeline
- [ ] Backtesting with walk-forward validation
- [ ] Regime transition probability matrix

### Phase 18: Edge Detection Framework
- [ ] Implement EdgeDetector class
- [ ] Pattern recognition: Fed Pivot, Liquidity Squeeze, Stealth QE, etc.
- [ ] Confidence scoring for each edge
- [ ] Historical success rate tracking
- [ ] Trade suggestion generation (long/short/neutral)
- [ ] Position sizing recommendations (Kelly criterion)
- [ ] Risk/reward calculation
- [ ] CLI command: `detect edges --lookback 30d`
- [ ] Backtesting module for edge performance

### Phase 19: Real-Time Trading Dashboard
- [ ] Set up Plotly Dash application structure
- [ ] FastAPI WebSocket backend for live updates
- [ ] Dashboard tab: Executive Summary (key metrics cards)
- [ ] Dashboard tab: Network Visualization (interactive graph)
- [ ] Dashboard tab: Early Warning (alert timeline)
- [ ] Dashboard tab: Regime Analysis (ML outputs + transitions)
- [ ] Dashboard tab: Trading Signals (edges + recommendations)
- [ ] Dashboard tab: Stress Test Results (scenario comparison)
- [ ] Mobile responsive design
- [ ] Docker compose for deployment

---

## Progress Tracking

| Milestone | Phases | Status | Progress |
|-----------|--------|--------|----------|
| M1 | 1-4 | Not Started | 0/4 |
| M2 | 5-7 | Not Started | 0/3 |
| M3 | 8-12 | Not Started | 0/5 |
| M4 | 13-16 | Not Started | 0/4 |
| M5 | 17-19 | Not Started | 0/3 |

**Total**: 0/19 phases complete
