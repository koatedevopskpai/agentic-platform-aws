# AgenticOps — Company Profile

## Overview

| Attribute | Detail |
|-----------|--------|
| **Name** | AgenticOps Inc. |
| **Tagline** | Precision brand intelligence at machine speed |
| **Founded** | 2023 |
| **Employees** | 40 |
| **Stage** | Series A ($12M led by Crestpoint Ventures) |
| **HQ** | San Francisco, CA |
| **Product** | AI-powered brand analytics platform that ingests unstructured brand mentions, social signals, news, and competitor data — then produces real-time sentiment analysis, positioning maps, and actionable intelligence |
| **Customers** | 15 enterprise brands (Nike, Unilever, LVMH, Samsung, Netflix, Toyota, P&G, Coca-Cola, Adidas, Spotify, Airbnb, Uber, Salesforce, Shopify, Stripe) |
| **Revenue** | $4.2M ARR, growing 18% MoM |

## Product Architecture (High-Level)

```
[Customer Data Sources] → [Ingestion Layer] → [Multi-Agent System] → [Brand Intelligence API]
                                ↓                        ↓
                         [S3 Data Lake]           [DynamoDB Sessions]
                                ↓                        ↓
                         [Athena Analytics]       [S3 Artifact Store]
```

The platform consists of:
1. **Ingestion Layer** — Webhooks, API connectors, scheduled scrapers → S3 data lake
2. **Orchestration Layer** — LangGraph-based multi-agent system (Scenario 01)
3. **Intelligence Pipeline** — Sentiment analysis, competitor positioning, trend detection
4. **API Layer** — REST + GraphQL endpoints serving brand analytics to customers
5. **Eval & Observability** — LLM-as-judge evaluation suite (Scenario 02)

## Key Business Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Agent response latency (p95) | 4.2s | <2.5s |
| Eval pass rate before deploy | 89% | >95% |
| Monthly LLM token consumption | 2.1B | Manage growth |
| Cost per analysis | $0.042 | <$0.03 |
| Uptime (agent API) | 99.7% | 99.95% |
| Audit coverage | 100% | 100% |
