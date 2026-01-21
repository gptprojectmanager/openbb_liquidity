# Phase 1: Foundation & Core Data - Context

**Gathered:** 2026-01-21
**Status:** Ready for planning

<vision>
## How This Should Work

A solid, production-grade foundation that all future phases build upon. Structure first, then data. When complete, I can see Net Liquidity (WALCL - TGA - RRP) calculating end-to-end: data flowing into QuestDB, calculations running, results visible via CLI/API.

The system serves two purposes equally: real-time trading signals (regime awareness for position sizing) and deep research/analysis (backtesting, historical correlations). It needs to handle both use cases well.

**Hybrid architecture approach:**
- OpenBB for data fetching (battle-tested, community-proven)
- Apps Script v3.4.1 logic for calculations (proven Hayes formulas)
- Custom async orchestration tying it together

Updates should be real-time where the APIs allow — poll frequently, push to QuestDB as soon as new data lands. Eventually feeds NautilusTrader via Redis pub/sub.

</vision>

<essential>
## What Must Be Nailed

All pieces are equally important — no shortcuts on foundation:

- **Clean collector pattern** — Reusable pattern for all future collectors (ECB, BoJ, etc.). Get it right once.
- **QuestDB schema** — Time-series storage that handles multi-source data, currencies, different frequencies. Hybrid design: wide tables for core metrics (fast trading queries), normalized for raw data (research flexibility).
- **OpenBB integration** — Leverage existing infrastructure properly, don't reinvent.
- **Data reliability** — Handle API failures, stale data, missing values gracefully.
- **Future extensibility** — Phase 2-10 collectors slot in cleanly without refactoring.
- **Performance at scale** — Years of historical data, multiple sources, real-time updates.

</essential>

<specifics>
## Specific Ideas

**Data & Validation:**
- All historical data available from FRED — as far back as possible
- Comprehensive validation: cross-source verification, historical consistency checks, freshness monitoring
- Configurable validation severity — critical issues block, minor issues flag
- Keep all data forever, no downsampling (CB data is small, backtesting needs full resolution)

**Resilience:**
- Exponential backoff + circuit breaker for API failures (enterprise-grade, Netflix/Google pattern)
- Graceful degradation with alerts — system keeps running, but I know when something's off
- Scheduled + on-demand backfill — daily gap detection, manual trigger when needed

**Observability:**
- Full stack: Prometheus + Grafana + QuestDB
- Store metrics in QuestDB, visualize in Grafana
- Prometheus for app metrics (collector success/failure, latency, etc.)

**Testing:**
- Comprehensive: Apps Script comparison (manual spot checks), historical validation, unit tests, integration tests
- Verify calculations match v3.4.1 outputs on same dates

**Configuration:**
- SOPS+age for secrets (per existing CLAUDE.md pattern)
- Pydantic Settings for typed config with validation

**Deployment:**
- Docker Compose for everything (QuestDB, Redis, Prometheus, Grafana, app)
- Portable — runs on home server, VPS, or cloud

**NautilusTrader Integration:**
- Redis pub/sub for pushing liquidity updates
- NautilusTrader subscribes to channels
- API needs to be Nautilus-compatible (Phase 9 detail, but keep in mind)

</specifics>

<notes>
## Additional Context

User wants "FAANG-grade" / "enterprise production ready" quality throughout. This is not a prototype — it's meant to be robust, reliable, and maintainable long-term.

The Hayes formula (Net Liquidity = WALCL - TGA - RRP) is the core calculation. Apps Script v3.4.1 in `.planning/reference/` is the source of truth for formulas and thresholds.

Phase 1 deliverables from roadmap:
- 01-01: Project scaffolding (uv, OpenBB, QuestDB, structure)
- 01-02: FRED API collector base + Fed balance sheet (WALCL, TGA, RRP)
- 01-03: MOVE, VIX, yield curve, credit spreads collectors

</notes>

---

*Phase: 01-foundation-core-data*
*Context gathered: 2026-01-21*
