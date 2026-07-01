# FundBot AI — LLM Fund Manager System Design

> 讓每個 LLM 充當專業基金經理，為客戶量身定制投資組合，目標是持續擊敗 SPY（S&P 500 ETF）回報率。

## Documents Index

| Document | Description |
|---|---|
| [01-vision-and-architecture.md](01-vision-and-architecture.md) | System vision, architecture overview, and component diagram |
| [02-client-questionnaire.md](02-client-questionnaire.md) | KYC questionnaire design — 20 questions across 4 sections |
| [03-llm-inputs-and-rag.md](03-llm-inputs-and-rag.md) | Complete data input catalog and RAG pipeline architecture |
| [04-decision-engine.md](04-decision-engine.md) | AI decision-making logic, scoring models, and prompt templates |
| [05-multi-llm-ensemble.md](05-multi-llm-ensemble.md) | Multi-LLM portfolio management strategy and ensemble methods |
| [06-data-pipeline.md](06-data-pipeline.md) | Market data pipeline, ETL, and external data source integration |
| [07-risk-management.md](07-risk-management.md) | Risk management framework, VaR, drawdown controls |
| [08-performance-evaluation.md](08-performance-evaluation.md) | Performance evaluation, benchmark comparison, and reporting |
| [09-implementation-roadmap.md](09-implementation-roadmap.md) | Phased implementation plan with timeline estimates |
| [10-rag-strategy.md](10-rag-strategy.md) | RAG strategy — why it's needed, how it works, open-source tool selection |

## Core Concept

```
                    ┌─────────────────────────────┐
                    │      LLM Fund Manager        │
                    │  (DeepSeek / GPT-4o / Claude)│
                    └─────────────┬───────────────┘
                                  │
          ┌───────────────────────┼───────────────────────┐
          │                       │                       │
          ▼                       ▼                       ▼
   ┌─────────────┐       ┌───────────────┐       ┌───────────────┐
   │  分析師      │       │  策略師        │       │  風控官        │
   │ (Analyst)    │       │ (Strategist)  │       │ (Risk Officer) │
   └─────────────┘       └───────────────┘       └───────────────┘
```

## Quick Start

1. Read [01-vision-and-architecture.md](01-vision-and-architecture.md) for the big picture
2. Follow [09-implementation-roadmap.md](09-implementation-roadmap.md) for phased delivery
