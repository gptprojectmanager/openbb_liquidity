# Phase 1: Foundation & Core Data - Research

**Researched:** 2026-01-21
**Domain:** Python data collection infrastructure (OpenBB, FRED, QuestDB, async patterns)
**Confidence:** HIGH

<research_summary>
## Summary

Researched the Python ecosystem for building a production-grade liquidity data collection system. The standard approach uses OpenBB SDK for unified data access (including FRED), QuestDB for time-series storage with ILP ingestion, and async Python patterns with httpx + tenacity for resilience.

Key finding: OpenBB already has a working USD Liquidity Index example in their repo that uses exactly the Hayes formula (WALCL - WLRRAL - WDTGAL). This validates the approach and provides reference implementation.

**Primary recommendation:** Use OpenBB SDK for FRED data fetching (unified API, handles credentials), QuestDB with Python ILP client for storage (28-92x faster than row-by-row), tenacity for retries with exponential backoff, and purgatory-circuitbreaker for circuit breaker pattern (actively maintained, supports async).

</research_summary>

<standard_stack>
## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| openbb | 4.x | Unified data fetching | 100+ data sources, FRED built-in, handles credentials |
| questdb | 2.x | Time-series ingestion | ILP protocol, 92x faster DataFrame ingestion |
| httpx | 0.27+ | Async HTTP client | Modern async, connection pooling, timeout control |
| pydantic-settings | 2.x | Configuration management | Type-safe config, env vars, secrets directory |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| tenacity | 9.x | Retry logic | All API calls, exponential backoff |
| purgatory-circuitbreaker | 1.x | Circuit breaker | Sustained API failures, Redis state sharing |
| redis[hiredis] | 5.x | Pub/sub + caching | NautilusTrader integration, shared state |
| prometheus-client | 0.21+ | Metrics exposition | Collector health, data freshness metrics |
| pydantic-settings-sops | 0.x | SOPS secrets integration | Loading encrypted credentials |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| OpenBB | fredapi directly | OpenBB provides unified API for 100+ sources, easier extension |
| purgatory | aiobreaker/pybreaker | aiobreaker inactive, pybreaker Tornado-based, purgatory async-native |
| QuestDB ILP | PGWire/SQL INSERT | ILP is insert-only but 92x faster for bulk data |
| httpx | aiohttp | httpx has better API, built-in timeout/retry transport |

**Installation:**
```bash
uv add openbb questdb httpx tenacity purgatory-circuitbreaker "redis[hiredis]" prometheus-client pydantic-settings pydantic-settings-sops
```

</standard_stack>

<architecture_patterns>
## Architecture Patterns

### Recommended Project Structure
```
src/
├── liquidity/
│   ├── __init__.py
│   ├── config.py           # Pydantic Settings
│   ├── collectors/
│   │   ├── __init__.py
│   │   ├── base.py         # Abstract collector with retry/circuit breaker
│   │   ├── fred.py         # FRED collector via OpenBB
│   │   ├── yahoo.py        # MOVE, VIX via OpenBB
│   │   └── registry.py     # Collector discovery/registration
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── questdb.py      # QuestDB ILP client wrapper
│   │   └── schemas.py      # Table schemas
│   ├── metrics/
│   │   ├── __init__.py
│   │   └── prometheus.py   # Custom collectors
│   ├── pubsub/
│   │   ├── __init__.py
│   │   └── redis.py        # Redis pub/sub wrapper
│   └── cli.py              # CLI entry point
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
└── docker-compose.yml
```

### Pattern 1: Base Collector with Resilience
**What:** Abstract base class with tenacity retry + circuit breaker built-in
**When to use:** All data collectors
**Example:**
```python
# Source: tenacity docs + purgatory docs
from abc import ABC, abstractmethod
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from purgatory import AsyncCircuitBreakerFactory
import httpx

class BaseCollector(ABC):
    def __init__(self, circuit_breaker_factory: AsyncCircuitBreakerFactory):
        self.cb_factory = circuit_breaker_factory

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=1, max=60),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError)),
        reraise=True
    )
    async def fetch_with_retry(self, fetch_fn):
        """Wrapper with exponential backoff retry."""
        async with self.cb_factory.get_breaker("external_api"):
            return await fetch_fn()

    @abstractmethod
    async def collect(self) -> list[dict]:
        """Implement in subclass."""
        pass
```

### Pattern 2: OpenBB FRED Data Fetching
**What:** Use OpenBB SDK to fetch FRED series with credential management
**When to use:** All FRED data (WALCL, TGA, RRP, yields, spreads)
**Example:**
```python
# Source: OpenBB usdLiquidityIndex.ipynb example
from openbb import obb
from pandas import DataFrame

class FredCollector(BaseCollector):
    SERIES_MAP = {
        "fed_total_assets": "WALCL",      # Fed balance sheet
        "rrp": "WLRRAL",                   # Reverse repo
        "tga": "WDTGAL",                   # Treasury General Account
        "move": "MOVE",                    # MOVE volatility index
        "dgs10": "DGS10",                  # 10Y Treasury
        "dgs2": "DGS2",                    # 2Y Treasury
        "bamlh0a0hym2": "BAMLH0A0HYM2",   # HY OAS spread
    }

    async def collect(self, symbols: list[str]) -> DataFrame:
        # OpenBB handles FRED API key from ~/.openbb_platform/user_settings.json
        # or obb.user.credentials.fred_api_key = "..."
        data = obb.economy.fred_series(symbols, provider="fred")
        return data.to_df().dropna()
```

### Pattern 3: QuestDB ILP Ingestion
**What:** Use ILP Sender with DataFrame API for bulk ingestion
**When to use:** All time-series data storage
**Example:**
```python
# Source: QuestDB Python client docs
from questdb.ingress import Sender, TimestampNanos
from pandas import DataFrame
import pandas as pd

class QuestDBStorage:
    def __init__(self, host: str = "localhost", port: int = 9009):
        self.host = host
        self.port = port

    def ingest_dataframe(self, table: str, df: DataFrame, timestamp_col: str = "date"):
        """Ingest DataFrame using ILP - 28-92x faster than row-by-row."""
        with Sender(self.host, self.port) as sender:
            # Convert timestamp column to nanoseconds
            df[timestamp_col] = pd.to_datetime(df[timestamp_col])
            sender.dataframe(
                df,
                table_name=table,
                at=timestamp_col,
                symbols=["source", "series_id"],  # Symbol columns for partitioning
            )
```

### Pattern 4: Prometheus Custom Collector for Data Freshness
**What:** Custom collector that reports data staleness metrics
**When to use:** Monitoring data quality
**Example:**
```python
# Source: prometheus_client custom collectors docs
from prometheus_client.core import GaugeMetricFamily, REGISTRY
from prometheus_client.registry import Collector
from datetime import datetime, timezone

class DataFreshnessCollector(Collector):
    def __init__(self, storage):
        self.storage = storage

    def collect(self):
        freshness = GaugeMetricFamily(
            'liquidity_data_age_seconds',
            'Age of most recent data point in seconds',
            labels=['source', 'series']
        )

        for source, series, last_ts in self.storage.get_latest_timestamps():
            age = (datetime.now(timezone.utc) - last_ts).total_seconds()
            freshness.add_metric([source, series], age)

        yield freshness

REGISTRY.register(DataFreshnessCollector(storage))
```

### Anti-Patterns to Avoid
- **Creating new OpenBB client per request:** Instantiate once, reuse for all fetches
- **Row-by-row QuestDB inserts:** Always use DataFrame API or batch with Sender
- **Synchronous FRED calls:** Use async httpx with tenacity for concurrent fetches
- **Hardcoded API keys:** Use SOPS+age + pydantic-settings-sops integration
- **Ignoring circuit breaker state:** Share state via Redis for multi-process deployments

</architecture_patterns>

<dont_hand_roll>
## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Retry logic | Custom while loops | tenacity | Handles backoff, jitter, async, callbacks |
| Circuit breaker | Custom state machine | purgatory-circuitbreaker | Async-native, Redis state sharing, battle-tested |
| FRED API client | Direct requests | OpenBB SDK | Unified API, credential management, rate limiting |
| Time-series storage | SQLite/PostgreSQL | QuestDB | Purpose-built, ILP ingestion, columnar storage |
| DataFrame ingestion | Row-by-row inserts | QuestDB sender.dataframe() | 28-92x performance improvement |
| Configuration | Manual env parsing | pydantic-settings | Type validation, nested models, secrets support |
| Secrets decryption | Manual SOPS calls | pydantic-settings-sops | Integrates with Pydantic settings source chain |
| HTTP client | requests (sync) | httpx (async) | Connection pooling, timeout control, transport retries |

**Key insight:** The Python ecosystem has mature solutions for every resilience pattern. tenacity is the de-facto standard for retries (used by OpenAI, Anthropic SDKs). purgatory is the only actively maintained async circuit breaker. QuestDB's ILP protocol is specifically designed for high-throughput time-series ingestion.

</dont_hand_roll>

<common_pitfalls>
## Common Pitfalls

### Pitfall 1: FRED API Rate Limiting
**What goes wrong:** 429 errors when fetching multiple series rapidly
**Why it happens:** FRED has ~120 requests/minute limit
**How to avoid:** Batch series in single OpenBB call (`obb.economy.fred_series(["WALCL", "TGA", "RRP"])`) or add delays
**Warning signs:** Intermittent 429 errors, exponential backoff kicking in frequently

### Pitfall 2: QuestDB Timestamp Handling
**What goes wrong:** Data overwrites or duplicates, deduplication fails
**Why it happens:** Using server-assigned timestamps instead of user-assigned
**How to avoid:** Always pass explicit timestamps via `at=` parameter; QuestDB recommends user-assigned timestamps for exactly-once processing
**Warning signs:** Duplicate rows for same timestamp, deduplication queries return unexpected results

### Pitfall 3: Redis PubSub Reconnection
**What goes wrong:** Subscriber stops receiving messages after network blip
**Why it happens:** redis.asyncio PubSub doesn't auto-reconnect on disconnect (only on TimeoutError)
**How to avoid:** Implement manual reconnection logic or use a wrapper that handles disconnect events
**Warning signs:** Subscriber hangs silently, no error but no messages

### Pitfall 4: Circuit Breaker State Isolation
**What goes wrong:** Circuit breaker in one process is open, others keep hammering failing API
**Why it happens:** Default in-memory state not shared across processes
**How to avoid:** Use purgatory with Redis backend for shared state
**Warning signs:** One worker stops calling API, others continue failing

### Pitfall 5: OpenBB Credential Scope
**What goes wrong:** API key not found errors despite setting credentials
**Why it happens:** Credentials set in wrong scope (session vs persistent)
**How to avoid:** For persistent: use `~/.openbb_platform/user_settings.json`. For session: `obb.user.credentials.fred_api_key = "..."`
**Warning signs:** "No API key found" errors, works in one script but not another

### Pitfall 6: Prometheus Multiprocess Mode
**What goes wrong:** Custom collectors don't work in Gunicorn/multiple workers
**Why it happens:** Custom collectors not supported in multiprocess mode
**How to avoid:** Run metrics collection in sidecar process, or use single-process deployment for collector service
**Warning signs:** Metrics endpoint returns empty/partial data with multiple workers

</common_pitfalls>

<code_examples>
## Code Examples

### OpenBB USD Liquidity Index (Verified)
```python
# Source: https://github.com/OpenBB-finance/OpenBB/blob/develop/examples/usdLiquidityIndex.ipynb
from openbb import obb
from pandas import DataFrame

# Fetch all series in single call (batched, respects rate limits)
data = obb.economy.fred_series(["WALCL", "WLRRAL", "WDTGAL"])
liquidity_index = DataFrame(data.to_df().dropna())

# Calculate Net Liquidity (Hayes formula)
liquidity_index["USD Liquidity Index"] = (
    liquidity_index["WALCL"]      # Fed Total Assets
    - liquidity_index["WLRRAL"]   # Reverse Repo (RRP)
    - liquidity_index["WDTGAL"]   # Treasury General Account (TGA)
)
```

### Tenacity Async Retry with Logging
```python
# Source: tenacity docs
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    before_sleep_log,
    retry_if_exception_type,
)
import logging
import httpx

logger = logging.getLogger(__name__)

@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=1, max=60),
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError)),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)
async def fetch_with_retry(client: httpx.AsyncClient, url: str) -> dict:
    response = await client.get(url, timeout=10.0)
    response.raise_for_status()
    return response.json()
```

### Purgatory Circuit Breaker with Redis
```python
# Source: purgatory docs
from purgatory import AsyncCircuitBreakerFactory
from purgatory.state import RedisState
import redis.asyncio as redis

# Shared state across processes
redis_client = redis.from_url("redis://localhost:6379")
state = RedisState(redis_client)

cb_factory = AsyncCircuitBreakerFactory(
    default_threshold=5,        # failures before opening
    default_ttl=60,             # seconds before half-open
    state=state,
)

async def call_external_api():
    async with cb_factory.get_breaker("fred_api"):
        # If circuit is open, raises CircuitBreakerError immediately
        return await fetch_data()
```

### QuestDB DataFrame Ingestion
```python
# Source: QuestDB Python client docs
from questdb.ingress import Sender
import pandas as pd

def ingest_fed_data(df: pd.DataFrame):
    """Ingest Fed balance sheet data to QuestDB."""
    # Ensure timestamp is datetime
    df["date"] = pd.to_datetime(df["date"])

    with Sender("localhost", 9009) as sender:
        sender.dataframe(
            df,
            table_name="fed_balance_sheet",
            at="date",
            symbols=["series_id"],  # Indexed for fast lookups
        )
        # Auto-flush on context exit
```

### Pydantic Settings with SOPS
```python
# Source: pydantic-settings + pydantic-settings-sops docs
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic_settings_sops import SOPSConfigSettingsSource

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        sops_files=["/media/sam/1TB/.env.enc"],
    )

    # From SOPS encrypted file
    fred_api_key: str
    discord_webhook_url: str

    # From env or defaults
    questdb_host: str = "localhost"
    questdb_port: int = 9009
    redis_url: str = "redis://localhost:6379"

    @classmethod
    def settings_customise_sources(cls, settings_cls, init_settings, env_settings, dotenv_settings, file_secret_settings):
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            SOPSConfigSettingsSource(settings_cls),
            file_secret_settings,
        )

settings = Settings()
```

</code_examples>

<sota_updates>
## State of the Art (2025-2026)

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| fredapi library | OpenBB SDK | 2024 | Unified API for 100+ sources, not just FRED |
| aiobreaker | purgatory-circuitbreaker | 2023 | aiobreaker inactive, purgatory actively maintained |
| QuestDB PGWire inserts | QuestDB ILP + DataFrame API | 2023 | 28-92x performance improvement |
| pydantic v1 settings | pydantic-settings v2 | 2023 | Separate package, better secrets handling |
| Manual SOPS decryption | pydantic-settings-sops | 2024 | Native integration with settings chain |

**New tools/patterns to consider:**
- **FedFred**: Modern FRED client with async support, rate limiting, caching — alternative if OpenBB feels heavy
- **QuestDB 9.0**: Array support for multi-value columns (useful for yield curves)
- **aioprometheus**: Alternative to prometheus_client for pure async applications

**Deprecated/outdated:**
- **aiobreaker**: Last release 2021, no longer maintained
- **pybreaker**: Tornado-based, not asyncio-native
- **fredapi**: Still works but limited to FRED only, OpenBB is superset

</sota_updates>

<open_questions>
## Open Questions

1. **OpenBB Async Support**
   - What we know: OpenBB provides sync API via `obb.economy.fred_series()`
   - What's unclear: Whether OpenBB supports async natively or requires wrapping in `asyncio.to_thread()`
   - Recommendation: Test in implementation; wrap sync calls in executor if needed

2. **QuestDB Partitioning Strategy**
   - What we know: QuestDB auto-partitions by timestamp, supports symbol columns
   - What's unclear: Optimal partition granularity for macro data (daily/weekly updates)
   - Recommendation: Start with DAY partitioning, benchmark and adjust

3. **Redis PubSub vs Streams for NautilusTrader**
   - What we know: Both patterns work; PubSub is simpler, Streams have persistence
   - What's unclear: What NautilusTrader expects/prefers for macro data integration
   - Recommendation: Start with PubSub (simpler), migrate to Streams if persistence needed

</open_questions>

<sources>
## Sources

### Primary (HIGH confidence)
- [OpenBB USD Liquidity Index Example](https://github.com/OpenBB-finance/OpenBB/blob/develop/examples/usdLiquidityIndex.ipynb) - Verified Hayes formula implementation
- [OpenBB Documentation](https://docs.openbb.co/) - SDK usage, credentials, FRED access
- [QuestDB Python Client Docs](https://questdb.com/docs/clients/ingest-python/) - ILP ingestion patterns
- [Tenacity Documentation](https://tenacity.readthedocs.io/) - Retry patterns, async support
- [prometheus_client Documentation](https://prometheus.github.io/client_python/) - Custom collectors

### Secondary (MEDIUM confidence)
- [purgatory-circuitbreaker PyPI](https://pypi.org/project/purgatory-circuitbreaker/) - Circuit breaker patterns
- [pydantic-settings-sops GitHub](https://github.com/pavelzw/pydantic-settings-sops) - SOPS integration
- [redis-py GitHub](https://github.com/redis/redis-py) - Async pub/sub patterns

### Tertiary (LOW confidence - needs validation)
- FedFred as alternative to fredapi — need to validate API completeness
- QuestDB array support in 9.0 — need to confirm availability and client support

</sources>

<metadata>
## Metadata

**Research scope:**
- Core technology: OpenBB SDK, QuestDB, async Python
- Ecosystem: tenacity, purgatory, redis-py, prometheus_client, pydantic-settings
- Patterns: Collector architecture, retry/circuit breaker, ILP ingestion
- Pitfalls: Rate limiting, timestamp handling, reconnection, multiprocess

**Confidence breakdown:**
- Standard stack: HIGH - all libraries verified in official docs
- Architecture: HIGH - patterns from official examples and docs
- Pitfalls: HIGH - documented in GitHub issues and official docs
- Code examples: HIGH - from official repos and documentation

**Research date:** 2026-01-21
**Valid until:** 2026-02-21 (30 days - ecosystem is stable)

</metadata>

---

*Phase: 01-foundation-core-data*
*Research completed: 2026-01-21*
*Ready for planning: yes*
