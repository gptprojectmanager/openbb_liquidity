# Requirements: Global Liquidity Monitor (OpenBB)

**Defined:** 2026-01-21
**Core Value:** Real-time regime classification — Know instantly whether we're in Expansionary, Neutral, or Contractionary liquidity regime to inform trading decisions.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Data Collection

- [ ] **DATA-01**: Collector retrieves Fed balance sheet data (WALCL, TGA, RRP) from FRED API
- [ ] **DATA-02**: Collector retrieves ECB balance sheet data from ECB SDW API
- [ ] **DATA-03**: Collector retrieves BoJ balance sheet data from FRED/BoJ API
- [ ] **DATA-04**: Collector retrieves PBoC balance sheet data (monthly lag accepted)
- [ ] **DATA-05**: Collector retrieves BoE balance sheet data from FRED API
- [ ] **DATA-06**: Collector retrieves SNB balance sheet data from SNB/FRED API
- [ ] **DATA-07**: Collector retrieves BoC balance sheet data from BoC/FRED API
- [ ] **DATA-08**: Collector retrieves SOFR rate from NY Fed Data Hub
- [ ] **DATA-09**: Collector retrieves €STR rate from ECB SDW API
- [ ] **DATA-10**: Collector retrieves SONIA rate from BoE API
- [ ] **DATA-11**: Collector retrieves CORRA rate from BoC API
- [ ] **DATA-12**: Collector retrieves MOVE index from Yahoo Finance
- [ ] **DATA-13**: Collector retrieves VIX index from Yahoo Finance
- [ ] **DATA-14**: Collector retrieves US Treasury yield curve from FRED API
- [ ] **DATA-15**: Collector retrieves credit spreads (IG, HY) from FRED API

### Liquidity Calculation

- [ ] **CALC-01**: System calculates Net Liquidity Index using Hayes formula (WALCL - TGA - RRP)
- [ ] **CALC-02**: System calculates Global Liquidity Index (Fed + ECB + BoJ + PBoC in USD)
- [ ] **CALC-03**: System calculates Stealth QE Score (port from Apps Script v3.4.1)
- [ ] **CALC-04**: System validates data consistency via double-entry accounting checks

### Analysis & Classification

- [ ] **ANLYS-01**: Regime classifier outputs Expansionary/Neutral/Contractionary state
- [ ] **ANLYS-02**: System tracks >85% of global monetary flows via Tier 1 CB coverage

### API & Integration

- [ ] **API-01**: FastAPI server exposes GET /liquidity/net endpoint
- [ ] **API-02**: FastAPI server exposes GET /liquidity/global endpoint
- [ ] **API-03**: FastAPI server exposes GET /regime/current endpoint
- [ ] **API-04**: FastAPI server exposes GET /metrics/stealth-qe endpoint
- [ ] **API-05**: NautilusTrader macro filter queries regime via REST API

### Alerting & Visualization

- [ ] **VIZ-01**: Plotly dashboard displays Net Liquidity Index time series
- [ ] **VIZ-02**: Plotly dashboard displays Global Liquidity Index time series
- [ ] **VIZ-03**: Plotly dashboard displays regime classification with color coding
- [ ] **VIZ-04**: Plotly dashboard exportable to standalone HTML
- [ ] **ALERT-01**: Discord webhook fires on regime state change
- [ ] **ALERT-02**: Discord webhook includes previous/current regime and key metrics

### Quality & Validation

- [ ] **QA-01**: System detects stale data (>24h for daily feeds, >48h for CBs)
- [ ] **QA-02**: System detects missing values and gaps in time series
- [ ] **QA-03**: System cross-validates data between sources (FRED vs direct API)
- [ ] **QA-04**: System flags anomalies (>3 std dev moves, sudden jumps)
- [ ] **QA-05**: Unit tests validate Hayes formula against known historical values
- [ ] **QA-06**: System cross-validates results vs Apps Script v3.4.1 output
- [ ] **QA-07**: Regression tests run on each data refresh
- [ ] **QA-08**: Dashboard shows data freshness indicator per source
- [ ] **QA-09**: Dashboard shows data quality score (completeness %)
- [ ] **QA-10**: Charts include sanity bounds (historical min/max ranges)

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Advanced Analysis

- **ADV-01**: RMP (Reserve Management Purchases) tracking as new Fed mechanism
- **ADV-02**: Swap lines stress indicator between Fed and 5 major CBs
- **ADV-03**: Gold flows tracking (Switzerland → China/India) for de-dollarization signal

### Crypto Integration

- **CRYPTO-01**: Crypto flow tracking (stablecoin supply, exchange flows)
- **CRYPTO-02**: BTC/Liquidity correlation dashboard

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Real-time intraday updates | Daily/weekly sufficient for macro analysis |
| Bloomberg Terminal integration | Too expensive ($24k/year), use free APIs |
| Shadow banking tracking | Opaque, unreliable data |
| Grafana dashboards | Plotly simpler, HTML export, no extra service |
| Historical backfill >5 years | MVP focus, can add later |

## Traceability

Which phases cover which requirements. Updated by create-roadmap.

| Requirement | Phase | Status |
|-------------|-------|--------|
| DATA-01 | - | Pending |
| DATA-02 | - | Pending |
| DATA-03 | - | Pending |
| DATA-04 | - | Pending |
| DATA-05 | - | Pending |
| DATA-06 | - | Pending |
| DATA-07 | - | Pending |
| DATA-08 | - | Pending |
| DATA-09 | - | Pending |
| DATA-10 | - | Pending |
| DATA-11 | - | Pending |
| DATA-12 | - | Pending |
| DATA-13 | - | Pending |
| DATA-14 | - | Pending |
| DATA-15 | - | Pending |
| CALC-01 | - | Pending |
| CALC-02 | - | Pending |
| CALC-03 | - | Pending |
| CALC-04 | - | Pending |
| ANLYS-01 | - | Pending |
| ANLYS-02 | - | Pending |
| API-01 | - | Pending |
| API-02 | - | Pending |
| API-03 | - | Pending |
| API-04 | - | Pending |
| API-05 | - | Pending |
| VIZ-01 | - | Pending |
| VIZ-02 | - | Pending |
| VIZ-03 | - | Pending |
| VIZ-04 | - | Pending |
| ALERT-01 | - | Pending |
| ALERT-02 | - | Pending |
| QA-01 | - | Pending |
| QA-02 | - | Pending |
| QA-03 | - | Pending |
| QA-04 | - | Pending |
| QA-05 | - | Pending |
| QA-06 | - | Pending |
| QA-07 | - | Pending |
| QA-08 | - | Pending |
| QA-09 | - | Pending |
| QA-10 | - | Pending |

**Coverage:**
- v1 requirements: 42 total
- Mapped to phases: 0 (pending create-roadmap)
- Unmapped: 42 ⚠️

---
*Requirements defined: 2026-01-21*
*Last updated: 2026-01-21 after QA requirements added*
