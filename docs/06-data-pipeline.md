# 06 — Data Pipeline

## 6.1 Data Sources

| Source | Data Type | API | Frequency | Cost |
|---|---|---|---|---|
| Financial Modeling Prep | Quotes, fundamentals, SEC filings, insider trades | REST | Real-time / Daily | $49/mo (Premium) |
| FRED (St. Louis Fed) | Macro indicators (CPI, GDP, unemployment, M2) | REST | Monthly/Quarterly | Free |
| Yahoo Finance | Historical prices, technical indicators | yfinance (Python) | On-demand | Free |
| Reddit API | WallStreetBets posts/comments | Reddit JSON API | Streaming / Daily | Free |
| Twitter/X API | Financial tweets/sentiment | Twitter API v2 | Streaming | Free tier |
| SEC EDGAR | 10-Q, 10-K filings | SEC EDGAR Full-Text | Quarterly | Free |
| Alpha Vantage | Technical indicators, FX, crypto | REST | Daily | Free tier |
| CBOE | VIX index | Web scrape | Real-time | Free |

## 6.2 ETL Pipeline

```
┌─────────────────────────────────────────────────────────┐
│  Scheduler (APScheduler / cron)                         │
│                                                         │
│  Every hour:                                            │
│  ├── fetch_quotes()         → Cache in Redis (30min TTL) │
│  ├── fetch_sector_flows()   → Cache in Redis (1hr TTL)  │
│  │                                                       │
│  Every day (market close):                               │
│  ├── fetch_macro_data()     → Store in MariaDB           │
│  ├── fetch_sentiment()      → Embed → Vector DB          │
│  ├── fetch_news()           → Embed → Vector DB          │
│  ├── fetch_sec_filings()    → Embed → Vector DB          │
│  ├── update_portfolio_snapshots() → MariaDB              │
│  │                                                       │
│  Every week:                                             │
│  ├── fetch_analyst_reports()→ Embed → Vector DB          │
│  ├── cleanup_stale_vectors()→ Prune vector DB            │
│  └── recalc_performance_metrics() → MariaDB              │
└─────────────────────────────────────────────────────────┘
```

## 6.3 Vector Database Schema (PGVector)

```sql
-- Collections stored as separate tables with vector embeddings

CREATE TABLE vec_news (
    id SERIAL PRIMARY KEY,
    source VARCHAR(50),          -- bloomberg, cnbc, reuters, etc.
    title TEXT,
    content TEXT,
    url TEXT,
    published_at TIMESTAMPTZ,
    symbols TEXT[],              -- Related stock symbols
    sentiment_score DECIMAL(5,4),
    embedding vector(1536),      -- OpenAI text-embedding-3-large
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE vec_earnings (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10),
    filing_type VARCHAR(20),     -- 10-K, 10-Q, 8-K
    filing_date DATE,
    content TEXT,
    summary TEXT,
    embedding vector(1536),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE vec_macro (
    id SERIAL PRIMARY KEY,
    indicator VARCHAR(50),
    value DECIMAL(15,4),
    context TEXT,                -- Description of what this means
    published_at DATE,
    embedding vector(1536),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_vec_news_embedding ON vec_news
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

CREATE INDEX idx_vec_news_symbols ON vec_news USING GIN (symbols);
```

## 6.4 Data Pipeline Implementation

```python
class DataPipeline:
    """
    Orchestrates all data ingestion, processing, and storage.
    Runs on APScheduler schedule.
    """

    def __init__(self, db: AsyncSession, redis_client, vector_client):
        self.db = db
        self.redis = redis_client
        self.vector = vector_client  # PGVector or Qdrant client
        self.embedder = OpenAIEmbeddings(model="text-embedding-3-small")

    async def fetch_and_store_news(self):
        """Fetch financial news, classify sentiment, embed, store."""
        for source in ["bloomberg", "cnbc", "reuters", "yahoo"]:
            articles = await self._fetch_news_from_source(source)
            for article in articles:
                # Skip if already exists
                existing = await self.vector.search(
                    collection="news",
                    filter={"url": article["url"]},
                )
                if existing:
                    continue

                # Classify sentiment
                sentiment = await self._classify_sentiment(article["content"])

                # Generate embedding
                embedding = await self.embedder.aembed_query(
                    f"{article['title']}\n\n{article['content']}"
                )

                # Extract mentioned stock symbols
                symbols = self._extract_symbols(article["content"])

                # Store
                await self.vector.upsert(
                    collection="news",
                    points=[{
                        "id": str(uuid4()),
                        "vector": embedding,
                        "payload": {
                            "source": source,
                            "title": article["title"],
                            "url": article["url"],
                            "published_at": article["published_at"],
                            "symbols": symbols,
                            "sentiment_score": sentiment,
                        }
                    }]
                )
        logger.info("News pipeline complete")

    async def _classify_sentiment(self, text: str) -> float:
        """Returns -1.0 (very negative) to +1.0 (very positive)."""
        response = await self.llm_gateway.generate(
            model="gpt-4o-mini",
            messages=[{
                "role": "system",
                "content": "Classify the sentiment of this financial text. "
                           "Return a single float between -1.0 and 1.0. "
                           "Respond with JSON: {\"sentiment\": 0.25}"
            }, {
                "role": "user",
                "content": text[:2000]  # Truncate for speed
            }]
        )
        return float(json.loads(response)["sentiment"])

    async def fetch_macro_indicators(self):
        """Fetch and store macro indicators from FRED API."""
        indicators = [
            ("FEDFUNDS", "Fed Funds Rate"),
            ("CPIAUCSL", "CPI (YoY)"),
            ("UNRATE", "Unemployment Rate"),
            ("GDP", "GDP (Quarterly)"),
            ("M2SL", "M2 Money Supply"),
            ("T10Y2Y", "10Y-2Y Treasury Spread"),
        ]
        for series_id, name in indicators:
            value = await self._fetch_fred_series(series_id)
            # Store in vector DB for RAG retrieval
            context = f"{name}: {value} as of {datetime.now().strftime('%Y-%m-%d')}"
            embedding = await self.embedder.aembed_query(context)
            await self.vector.upsert(
                collection="macro",
                points=[{
                    "id": f"macro_{series_id}_{datetime.now().strftime('%Y%m%d')}",
                    "vector": embedding,
                    "payload": {
                        "indicator": name,
                        "value": value,
                        "context": context,
                        "published_at": datetime.now().isoformat(),
                    }
                }]
            )
        logger.info("Macro indicators updated")

    def _extract_symbols(self, text: str) -> list[str]:
        """Extract ticker symbols from text using regex."""
        # Match common stock symbols: 1-5 uppercase letters
        pattern = r'\b[A-Z]{1,5}\b'
        candidates = set(re.findall(pattern, text))
        # Filter against known tickers (from our database)
        known = self._get_known_tickers()
        return list(candidates & known)
```

## 6.5 Redis Caching Strategy

```python
class MarketDataCache:
    """
    Redis-backed cache for frequently accessed market data.
    Reduces API calls and speeds up prompt assembly.
    """

    TTL = {
        "live_quote": 30,        # 30 seconds for real-time prices
        "sector_flows": 3600,    # 1 hour
        "vix": 60,               # 1 minute
        "macro": 86400,          # 24 hours
        "sentiment": 3600,       # 1 hour
    }

    async def get_quote(self, symbol: str) -> dict | None:
        data = await self.redis.get(f"quote:{symbol}")
        if data:
            return json.loads(data)
        return None

    async def set_quote(self, symbol: str, quote: dict):
        await self.redis.setex(
            f"quote:{symbol}",
            self.TTL["live_quote"],
            json.dumps(quote)
        )

    async def get_market_context(self) -> dict:
        """Get all cached market data for prompt assembly."""
        return {
            "spy": await self.get_quote("SPY"),
            "vix": await self.get_quote("VIX"),
            "dxy": await self.get_quote("DXY"),
            "sectors": await self.get_sector_flows(),
            "macro": await self.get_macro_snapshot(),
            "sentiment": await self.get_sentiment_snapshot(),
        }
```
