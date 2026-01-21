"""QuestDB table schemas for liquidity data.

Defines table schemas using SQL DDL statements for:
- RAW_DATA: Raw series data from various sources (FRED, ECB, etc.)
- LIQUIDITY_INDEXES: Calculated liquidity metrics (Net Liquidity, Global Liquidity)

Schema design follows QuestDB best practices:
- MONTH partitioning for macro data (daily/weekly updates)
- SYMBOL columns for series_id, source, unit (dictionary-encoded)
- WAL + DEDUP UPSERT KEYS for exactly-once semantics
"""

# Table name constants
RAW_DATA_TABLE = "raw_data"
LIQUIDITY_INDEXES_TABLE = "liquidity_indexes"

# SQL DDL for raw data table
RAW_DATA_SCHEMA = """
CREATE TABLE IF NOT EXISTS raw_data (
    timestamp TIMESTAMP,
    series_id SYMBOL CAPACITY 100,
    source SYMBOL CAPACITY 10,
    value DOUBLE,
    unit SYMBOL CAPACITY 20
) TIMESTAMP(timestamp)
  PARTITION BY MONTH
  WAL
  DEDUP UPSERT KEYS(timestamp, series_id);
"""

# SQL DDL for liquidity indexes table
LIQUIDITY_INDEXES_SCHEMA = """
CREATE TABLE IF NOT EXISTS liquidity_indexes (
    timestamp TIMESTAMP,
    index_name SYMBOL CAPACITY 20,
    value DOUBLE,
    regime SYMBOL CAPACITY 10
) TIMESTAMP(timestamp)
  PARTITION BY MONTH
  WAL
  DEDUP UPSERT KEYS(timestamp, index_name);
"""

# All schemas for initialization
ALL_SCHEMAS = [RAW_DATA_SCHEMA, LIQUIDITY_INDEXES_SCHEMA]

# Symbol columns per table (for ILP ingestion)
RAW_DATA_SYMBOLS = ["series_id", "source", "unit"]
LIQUIDITY_INDEXES_SYMBOLS = ["index_name", "regime"]
