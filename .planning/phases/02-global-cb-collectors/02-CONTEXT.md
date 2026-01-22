# Phase 2: Global CB Collectors - Context

**Gathered:** 2026-01-22
**Status:** Ready for research

<vision>
## How This Should Work

Each central bank gets its own collector class, mirroring the Fed approach from Phase 1. This keeps implementations isolated — one CB's quirky API doesn't affect the others.

When done, we can pull balance sheet data from ECB, BoJ, PBoC, BoE, SNB, and BoC. Each collector goes to the official source API (ECB SDW, BoJ API, etc.) rather than relying on FRED proxies. The data feeds into QuestDB just like the Fed data.

Data is stored in native currency for now — USD conversion comes in Phase 3 when FX collectors are ready. This decoupling is intentional: store accurate source data first, transform later.

</vision>

<essential>
## What Must Be Nailed

- **Data accuracy** — Balance sheet totals must match official CB publications
- **USD conversion ready** — All values stored for later conversion when FX data is available
- **Freshness tracking** — Know exactly how stale each CB's data is (ECB weekly, PBoC monthly lag)
- **Reliability** — Robust error handling, retries, graceful degradation when APIs fail
- **Consistency** — All collectors follow the same patterns as Phase 1 (FredCollector, YahooCollector)
- **Testability** — Easy to mock responses, solid unit/integration test coverage

</essential>

<specifics>
## Specific Ideas

**Data sources:** Go to official CB APIs directly (ECB SDW, BoJ API) — not FRED proxies. Most authoritative data at the source.

**Data lag handling:** Accept the lag. PBoC is ~1 month behind — use latest available data and track staleness metadata. Don't interpolate or estimate.

**Data granularity:** Store both totals (for formulas) and component breakdown (bonds, loans, etc.) for future deep-dive analysis.

**Validation:** Cross-reference values against official CB publications for initial setup. Range checks for ongoing monitoring (alert on suspicious jumps).

**Reference implementation:** Improve on Apps Script v3.4.1 — it was a prototype. This should be better engineered with proper async patterns, error handling, and testing.

</specifics>

<notes>
## Additional Context

**Research needed** (user flagged):
- PBoC access — Chinese data can be tricky, research scraping vs API options
- API authentication — What credentials/keys are needed for ECB SDW, BoJ, etc.
- Data coverage — Which series map to "total assets" for each CB

**Success criteria feel:**
- Global coverage: "We can now track all major CBs"
- Hayes formula ready: "Global Liquidity calculation is unlocked"
- Production quality: "These collectors could run in prod today"

**The win:** Seeing Fed + ECB + BoJ + PBoC together for the first time. That's the Hayes thesis — it's the global liquidity tide that moves markets.

**Timeline:** Ship when ready. Quality over speed.

</notes>

---

*Phase: 02-global-cb-collectors*
*Context gathered: 2026-01-22*
