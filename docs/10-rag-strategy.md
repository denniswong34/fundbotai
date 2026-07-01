# 10 — RAG Strategy for LLM Fund Manager

> Why RAG, how it works, and what open-source tools we use.

## 1. Why RAG? (The Core Problem)

LLM Fund Managers face a fundamental contradiction:

> **LLMs' knowledge is frozen at training cutoff, but the stock market updates every second.**

### Without RAG = Blind Fund Manager

Using a raw LLM (e.g. deepseek-v4-flash) to manage portfolios has these problems:

| Problem | Consequence | Example |
|---|---|---|
| **Knowledge Cutoff** | Doesn't know recent events | An LLM trained in 2025 doesn't know NVDA's 2026 Q2 earnings |
| **No Real-Time Data** | Can't see current prices | LLM doesn't know today's SPY move |
| **Hallucination** | Fabricates nonexistent data | Claims "AAPL revenue was $150B last quarter" when it was $120B |
| **Look-Ahead Bias** | Uses future data for "predictions" | LLM sees 2025 data and says "2024 was great for NVDA" |
| **No Market Context** | Can't sense market sentiment | Doesn't know Reddit is pumping a stock |

### With RAG

```
Without RAG:
  ┌─────────┐
  │  LLM    │ ← Only old training data
  │         │     "NVDA up to 2024-12..."
  └────┬────┘
       ▼
  [Stale or wrong decision]

With RAG:
         ┌──────────────────┐
         │  📰 Live news    │
         │  📊 Current price│
         │  🏢 SEC filings  │
         │  📈 Economic data│
         └────────┬─────────┘
                  │
                  ▼
  ┌─────────┐   ┌──────────────┐
  │  LLM    │ ← │ RAG Results  │ ← Knowledge cutoff → SOLVED
  │         │   │ (Fresh info) │ ← Hallucination → ANCHORED
  └────┬────┘   └──────────────┘ ← Real-time data → PROVIDED
       ▼
  [Fact-based investment decision]
```

---

## 2. How RAG Works (Technical Flow)

### Phase 1: Offline Indexing

```
Every hour / day
═══════════════════════════════════════════════════════

Crawl raw data
  │
  ▼
Step 1: Data Ingestion
──────────────────────

  📰 Financial News:   Bloomberg → REST API → raw JSON
  🏢 SEC Filings:      EDGAR    → sec-api   → raw text
  📊 Economic Data:    FRED API → REST      → raw JSON
  💬 Market Sentiment: Reddit   → API       → raw JSON

  Output: Raw documents
  │
  ▼
Step 2: Document Chunking
─────────────────────────

  Split long docs into LLM-friendly pieces.

  📰 News (512 chars, 50 overlap):
     "Fed signals Sep rate cut, markets rally..."
     → Chunk 1: "Fed signals Sep rate cut..."
     → Chunk 2: "...markets rally on rate cut hopes..."

  🏢 SEC 10-K/10-Q (semantic — by Item section):
     → Item 1: Business
     → Item 1A: Risk Factors
     → Item 7: Management Discussion

  │
  ▼
Step 3: Generate Embeddings
───────────────────────────

  "Fed signals Sep rate cut..."
       │
       ▼
  Embedding Model (text-embedding-3-small)
       │
       ▼
  [0.023, -0.145, 0.567, ..., 0.089]  ← 1536-dimensional vector

  Semantically similar text → nearby vectors
  "FOMC likely to ease" → close to above vector
  "I like pizza" → far from above vector
  │
  ▼
Step 4: Store in Vector DB (Qdrant)
────────────────────────────────────

  Point {
    id: "news_20260701_001",
    vector: [0.023, -0.145, ..., 0.089],
    payload: {
      source: "Bloomberg",
      title: "Fed Signals Sep Rate Cut",
      published_at: "2026-07-01T14:30:00Z",
      symbols: ["SPY", "QQQ", "TLT"],
      sentiment: 0.75,
      content: "Fed暗示9月可能降息..."
    }
  }
```

### Phase 2: Real-Time Retrieval

```
When the LLM needs to make a decision
═══════════════════════════════════════════════════════

LLM asks: "Should I buy or sell NVDA right now?"
  │
  ▼
Step 5: Query Embedding
───────────────────────

  Query: "NVDA recent performance and market sentiment?"

  Same embedding model →
  query_vector: [0.156, -0.089, ..., 0.345]
  │
  ▼
Step 6: Similarity Search (Vector + Keyword Hybrid)
────────────────────────────────────────────────────

  Cosine Similarity = cos(θ) = (A·B) / (||A|| × ||B||)

  Top-K Results (K=5, with metadata filter):
  ┌──────┬─────────────────────────────────┬────────┬────────┐
  │ Rank │ Content                         │ Score  │ Date   │
  ├──────┼─────────────────────────────────┼────────┼────────┤
  │ 1    │ NVDA Q2 revenue beats 15%       │ 0.92 ✅│ Jun 25 │
  │ 2    │ Analysts raise NVDA PT to $250  │ 0.87   │ Jun 28 │
  │ 3    │ CEO sells 50K shares of NVDA    │ 0.81 ⚠️│ Jun 30 │
  │ 4    │ AI chip demand remains strong   │ 0.76   │ Jun 27 │
  │ 5    │ NVDA RSI breaks above 70        │ 0.72 ⚠️│ Jul 1  │
  └──────┴─────────────────────────────────┴────────┴────────┘

  Hybrid Search = 0.7 × vector_similarity + 0.3 × recency_boost
  │
  ▼
Step 7: Augment the Prompt
───────────────────────────

  Original Prompt (no RAG):
  ┌─────────────────────────────────────┐
  │ "Is NVDA a buy right now?"          │
  │ LLM guesses from old training → ❌  │
  └─────────────────────────────────────┘

  Augmented Prompt (with RAG):
  ┌─────────────────────────────────────┐
  │ "Latest info about NVDA:            │
  │                                     │
  │  📰 1. NVDA Q2 revenue beats 15%   │
  │     (Bloomberg, Jun 25)             │
  │                                     │
  │  📰 2. Analysts raise NVDA PT $250  │
  │     (JP Morgan, Jun 28)            │
  │                                     │
  │  ⚠️ 3. CEO sells 50K shares NVDA   │
  │     (SEC Filing, Jun 30)            │
  │                                     │
  │  ⚠️ 4. NVDA RSI(14)=72 — overbought │
  │     (Technical, real-time)          │
  │                                     │
  │  Based on this info, is NVDA a buy?"│
  │                                     │
  │ LLM has facts → accurate answer ✅  │
  └─────────────────────────────────────┘
  │
  ▼
Step 8: Generate Decision (JSON)
─────────────────────────────────

  LLM now has:
  ✓ Financial knowledge from training (what is PE, RSI, MACD)
  ✓ Real-time info from RAG (NVDA recent news)
  ✓ Live prices from API ($198.50, VIX 14.32)
  ✓ Portfolio state from DB

  → JSON decision output:
  {
    "action": "sell",
    "symbol": "NVDA",
    "qty": 2,
    "reasoning": "Strong revenue but CEO insider selling + RSI
                   overbought suggests profit-taking.",
    "risk_note": "76% realized profit taken so far"
  }
```

---

## 3. Open-Source Tool Selection

### Vector Database: Qdrant

| Tool | Pros | Cons | Verdict |
|---|---|---|---|
| **Qdrant** 🏆 | • One-command Docker deploy<br>• Excellent Python SDK<br>• Built-in filtering + payload<br>• Fast HNSW index<br>• REST + gRPC API | • Need extra Docker service | **✅ Chosen** |
| Chroma | • Simplest (pip install)<br>• No Docker needed | • Unstable in production<br>• No filtering | ❌ Dev only |
| PGVector | • Works with PostgreSQL | • We use MariaDB (no support)<br>• Would need extra PostgreSQL<br>• Slower than Qdrant | ❌ Wrong stack |
| Milvus | • Most powerful, billion-scale | • Too heavy (needs etcd, minio)<br>• Overkill for our scale | ❌ Too heavy |
| Pinecone | • Managed SaaS, zero ops | • $$$<br>• Data leaves our infra | ❌ Self-hosted needed |

### Embedding Model: text-embedding-3-small

| Model | Dims | Cost | Quality | Verdict |
|---|---|---|---|---|
| **text-embedding-3-small** 🏆 | 1536 | $0.02/1M tokens | Very good | **✅ Best cost/quality** |
| text-embedding-3-large | 3076 | $0.13/1M tokens | Best | 6x cost, marginal gain |
| BGE-M3 (open-source) | 1024 | Free (self-host) | Good | If offline is needed |
| intfloat/e5-mistral-7b | 4096 | Free but needs GPU | Best OSS | Too heavy |

### RAG Orchestration: LlamaIndex

| Approach | Framework | Suited For | Verdict |
|---|---|---|---|
| **Heavy integration** | LangChain + LangGraph | Complex workflows, multi-step agents | ❌ Overkill |
| **Lightweight + flexible** 🏆 | **LlamaIndex** + Qdrant | Financial RAG, structured + unstructured | **✅ Chosen** |
| Build from scratch | Custom Retriever class + Qdrant client | Simple scenarios, full control | ❌ Miss ecosystem |

**Why LlamaIndex over LangChain:**

```
✅ Native structured data support (Pandas DataFrames — feed portfolio holdings directly)
✅ Native unstructured data support (News, SEC filings)
✅ 40+ built-in chunking strategies
✅ Built-in query transformation
✅ Built-in reranking (Cohere / BGE)
✅ Pythonic, non-opinionated API
✅ Can use only its retrieval — not forced into full agent

❌ LangChain has too many breaking changes
```

### Complete Tool Stack

| Function | Open-Source Project | Version | Reason |
|---|---|---|---|
| **RAG Framework** | **LlamaIndex** | 0.12+ | Most flexible indexing/retrieval, no agent lock-in |
| **Vector DB** | **Qdrant** | latest | One-command Docker, pure Rust, high perf |
| **Embedding** | **text-embedding-3-small** | via OpenAI API | Best cost/benefit, via opencode-go gateway |
| **Reranking** | **BAAI/bge-reranker-v2-m3** | HuggingFace | Best open-source reranker, +10-15% accuracy |
| **Chunking** | **LlamaIndex built-in** | — | Semantic + Recursive splitters |
| **Document Parsing** | **Unstructured** | 0.16+ | PDF/HTML/SEC filing parsing |
| **ETL Scheduling** | **APScheduler** (existing) | — | Already in our stack |
| **Hybrid Search** | **Qdrant built-in** | — | vector + full-text keyword |
| **Caching** | **Redis** (existing) | — | Live quotes, sentiment cache |

### What We DON'T Build Ourselves

```
❌ Vector DB queries — Qdrant handles this
❌ Embedding generation — LlamaIndex/OpenAI handles this
❌ Document chunking — LlamaIndex has 40+ strategies
❌ Reranking — BGE-reranker handles this
❌ Hybrid search — Qdrant built-in sparse + dense
❌ Metadata filtering — Qdrant/LlamaIndex built-in
```

### What We DO Build Ourselves

```
✅ Decision Engine — our PortfolioManager + ArenaService
✅ Risk Enforcer — our Risk Management module
✅ Prompt Assembly — combine portfolio state + market data + RAG
✅ Client Questionnaire Analysis — LLM + scoring formula
✅ Performance Tracking — our PerformanceCalculator
✅ Broker Integration — existing 11 broker adapters
```

---

## 4. Qdrant Docker Setup

```yaml
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: fundbotai-qdrant
    ports:
      - "6333:6333"   # REST API
      - "6334:6334"   # gRPC (faster)
    volumes:
      - ./qdrant_storage:/qdrant/storage
    environment:
      - QDRANT__SERVICE__GRPC_PORT=6334
    restart: unless-stopped
```

---

## 5. Implementation Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                     FundBot AI RAG Pipeline                              │
│                                                                         │
│  Scheduler (APScheduler)                                                 │
│  ┌─────────────────────────────────────────────────────────────┐      │
│  │  • Every hour: Fetch news + sentiment → chunk → embed → Qdrant │      │
│  │  • Daily:     SEC filings + economic data → chunk → embed    │      │
│  │  • Weekly:    Cleanup stale data (>90 day old news)          │      │
│  └─────────────────────────────────────────────────────────────┘      │
│                                                                         │
│  Vector DB (Qdrant)                                                      │
│  ┌─────────────────────────────────────────────────────────────┐      │
│  │  Collections:                                                    │      │
│  │  ┌──────────┬──────────┬──────────┬──────────┬──────────┐     │      │
│  │  │financial_│earnings_ │macro_    │sentiment_│sec_filings│     │      │
│  │  │news      │reports   │indicators│scores    │           │     │      │
│  │  ├──────────┼──────────┼──────────┼──────────┼──────────┤     │      │
│  │  │~500K pts │~10K pts  │~500 pts  │~100K pts │~5K pts   │     │      │
│  │  │TTL: 90d  │TTL: 365d │TTL: 730d │TTL: 30d  │TTL: 365d │     │      │
│  │  └──────────┴──────────┴──────────┴──────────┴──────────┘     │      │
│  └─────────────────────────────────────────────────────────────┘      │
│                                                                         │
│  Retrieval Service                                                       │
│  ┌─────────────────────────────────────────────────────────────┐      │
│  │  class FinancialRAG:                                          │      │
│  │                                                               │      │
│  │  async def retrieve(                                          │      │
│  │      query: str,           # LLM's question                  │      │
│  │      symbols: list[str],   # Filter by stock symbols         │      │
│  │      days_back: int = 30,  # Recency filter                  │      │
│  │      top_k: int = 5,      # Results count                   │      │
│  │  ) -> list[dict]:                                            │      │
│  │                                                               │      │
│  │  1. embed query → query_vector                                │      │
│  │  2. Qdrant search with filter:                                │      │
│  │     - must: symbols contains ANY query_symbols                │      │
│  │     - must: published_at > now - days_back                    │      │
│  │  3. Score = 0.7×cosine_sim + 0.3×recency_boost               │      │
│  │  4. Rerank with BGE-reranker-v2-m3                            │      │
│  └─────────────────────────────────────────────────────────────┘      │
│                                                                         │
│  Prompt Assembly                                                         │
│  ┌─────────────────────────────────────────────────────────────┐      │
│  │  RAG Results (from Qdrant)    Live API Data (from Redis)     │      │
│  │  ┌─────────────────────┐     ┌──────────────────────┐      │      │
│  │  │ 📰 News Top 5      │     │ 📊 SPY: $556.30      │      │      │
│  │  │ 🏢 SEC filings     │     │ 📊 VIX: 14.32        │      │      │
│  │  │ 📈 Analyst reports │     │ 📊 CPI: +3.2%        │      │      │
│  │  │ 💬 Market sentiment│     │ 📊 NVDA: $198.50     │      │      │
│  │  └─────────────────────┘     └──────────────────────┘      │      │
│  │                          ↓                                    │      │
│  │  ┌──────────────────────────────────────────────────────┐   │      │
│  │  │  Final Prompt:                                       │   │      │
│  │  │  System + Client Profile + Portfolio State +         │   │      │
│  │  │  RAG Context + Live Data + Risk Limits +             │   │      │
│  │  │  Previous Decision                                  │   │      │
│  │  └──────────────────────────────────────────────────────┘   │      │
│  │                          ↓                                    │      │
│  │              ┌──────────────────────┐                       │      │
│  │              │ LLM (opencode-go)    │                       │      │
│  │              └──────────────────────┘                       │      │
│  │                          ↓                                    │      │
│  │              ┌──────────────────────┐                       │      │
│  │              │ JSON Decision        │                       │      │
│  │              └──────────────────────┘                       │      │
│  └─────────────────────────────────────────────────────────────┘      │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Core Code Example

```python
# ── Using LlamaIndex ONLY for indexing + retrieval ──
# Decision engine stays in our PortfolioManager/ArenaService

from llama_index.core import VectorStoreIndex, Document, StorageContext
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.postprocessor import SentenceTransformerRerank
from llama_index.core.vector_stores import MetadataFilters, MetadataFilter, FilterOperator


class FinancialRAG:
    """
    Lightweight RAG layer using LlamaIndex for indexing + retrieval only.
    No agent, no query engine — just retrieval augmentation.
    """

    def __init__(self, qdrant_client, embed_model="text-embedding-3-small"):
        self.vector_store = QdrantVectorStore(
            client=qdrant_client,
            collection_name="financial_news",
        )
        self.embed_model = OpenAIEmbedding(model=embed_model)
        self.storage_context = StorageContext.from_defaults(
            vector_store=self.vector_store
        )

    def index_documents(self, documents: list[dict]):
        """LlamaIndex auto-chunks, embeds, and stores."""
        docs = [
            Document(
                text=doc["content"],
                metadata={
                    "source": doc["source"],
                    "published_at": doc["published_at"],
                    "symbols": doc.get("symbols", []),
                    "sentiment": doc.get("sentiment"),
                }
            )
            for doc in documents
        ]
        index = VectorStoreIndex.from_documents(
            documents=docs,
            embed_model=self.embed_model,
            storage_context=self.storage_context,
            show_progress=True,
        )
        return index

    async def retrieve(
        self,
        query: str,
        symbols: list[str] = None,
        days_back: int = 30,
        top_k: int = 5,
    ) -> list[dict]:
        """Hybrid vector + keyword retrieval with reranking."""

        filters = None
        if symbols:
            filters = MetadataFilters(
                filters=[
                    MetadataFilter(
                        key="symbols",
                        operator=FilterOperator.ANY,
                        value=symbols,
                    ),
                    MetadataFilter(
                        key="published_at",
                        operator=FilterOperator.GTE,
                        value=(
                            datetime.now() - timedelta(days=days_back)
                        ).isoformat(),
                    ),
                ]
            )

        retriever = VectorIndexRetriever(
            index=self.index,
            similarity_top_k=top_k * 2,  # Fetch more, then rerank
            filters=filters,
        )

        nodes = await retriever.aretrieve(query)

        # Rerank with cross-encoder model
        reranker = SentenceTransformerRerank(
            model="BAAI/bge-reranker-v2-m3",
            top_n=top_k,
        )
        nodes = reranker.postprocess_nodes(nodes)

        return [
            {
                "content": node.node.text,
                "score": node.score,
                "metadata": node.node.metadata,
            }
            for node in nodes
        ]
```

---

## 7. Summary

### Without RAG → LLM Fund Manager is UNWORKABLE

| Scenario | Without RAG | With RAG |
|---|---|---|
| "Is NVDA a buy today?" | Only knows price up to training cutoff | Knows yesterday's earnings + CEO selling + today's price |
| "What did the Fed say?" | May hallucinate FOMC statement | Retrieves actual statement from FRED + news |
| "What's market sentiment?" | Vague memory from training | Real-time Reddit/Twitter sentiment analysis |
| "Similar historical period?" | Wrong reference period | Vector search finds most similar macro regime |

### Infrastructure Needed

| Component | Technology | Deployment |
|---|---|---|
| Vector DB | Qdrant | Docker (single container) |
| Embedding | text-embedding-3-small | Via opencode-go API |
| RAG Framework | LlamaIndex | pip install |
| Reranking | BAAI/bge-reranker-v2-m3 | HuggingFace |
| ETL | APScheduler (existing) | Python cron |
| Cache | Redis (existing) | Already in stack |

**Everything is Python + Docker — fully compatible with our existing stack.**
