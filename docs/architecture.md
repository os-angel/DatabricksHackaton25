# DecisionMakingArena - Architecture Documentation

## 🏗️ System Architecture Overview

DecisionMakingArena is an AI-powered executive decision support system built on Databricks. It combines multiple foundation models, Genie spaces, Vector Search, and Unity Catalog Functions to provide comprehensive business intelligence.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    DATABRICKS APP (Single)                       │
│                  "DecisionMakingArena"                          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     GRADIO INTERFACE                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │CEO Chat  │  │Simulation│  │Dashboard │  │Analytics │       │
│  │Interface │  │  Panel   │  │   Live   │  │ History  │       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│            MASTER ORCHESTRATOR (Cerebro Principal)               │
│                                                                  │
│  Model: databricks-meta-llama-3-1-405b-instruct                │
│                                                                  │
│  Responsibilities:                                              │
│  1. Receive questions from CEO                                 │
│  2. Decompose complex queries into sub-tasks                   │
│  3. Decide which Genie(s) to consult                           │
│  4. Enrich responses with RAG Vector Search                    │
│  5. Synthesize final executive response                        │
│                                                                  │
│  ┌────────────────────────────────────────────────────┐        │
│  │     MOSAIC AI VECTOR SEARCH (Knowledge Base)       │        │
│  │                                                     │        │
│  │  Indexed Content:                                  │        │
│  │  - Historical CEO reports                          │        │
│  │  - Industry benchmarks                             │        │
│  │  - Best practices documentation                    │        │
│  │  - Previous analysis results                       │        │
│  │  - Business context & definitions                  │        │
│  └────────────────────────────────────────────────────┘        │
└────────────────┬───────────────────────────────────────────────┘
                 │
      ┌──────────┴──────────┬─────────────────┬──────────────┐
      ▼                     ▼                 ▼              ▼
┌──────────┐         ┌──────────┐      ┌──────────┐   ┌──────────┐
│ Intent   │         │ Multi-   │      │Simulation│   │Response  │
│Classifier│         │  Agent   │      │ Engine   │   │Synthesizer│
│(70b)     │         │Coordinator│      │(Unity Cat│   │  (405b)  │
└──────────┘         └──────────┘      │Functions)│   └──────────┘
                                        └──────────┘
```

## Components

### 1. Master Orchestrator
**Model**: `databricks-meta-llama-3-1-405b-instruct`

**Purpose**: The brain of the system that coordinates all other components.

**Responsibilities**:
- Strategic planning of complex queries
- Multi-source information synthesis
- Executive narrative generation
- High-level routing decisions

### 2. Intent Classifier
**Model**: `databricks-meta-llama-3-1-70b-instruct`

**Purpose**: Fast, lightweight classification of incoming queries.

**Outputs**:
- Query type (single_domain, multi_domain, simulation, etc.)
- Relevant domains (sales, finance, strategic)
- Required Genies
- Visualization requirements
- Complexity score

### 3. Genie Clients
**Platform**: Databricks Genie Spaces

**Available Genies**:
- **Sales Genie**: Sales data, products, customers, revenue
- **Finance Genie**: Financial data, margins, costs, ROI
- **Strategic Genie**: Strategy, market positioning, competition

**Integration**: REST API via Databricks SDK

### 4. Vector Search RAG
**Platform**: Mosaic AI Vector Search

**Purpose**: Enrich responses with historical context and benchmarks.

**Knowledge Base Contents**:
- Historical CEO reports and board presentations
- Industry benchmarks and competitor analysis
- Best practices frameworks
- Previous analysis results
- Business glossary and KPI definitions

### 5. Simulation Engine
**Platform**: Unity Catalog Functions

**Capabilities**:
- ROI calculations for new investments
- Revenue forecasting with confidence intervals
- Scenario comparison analysis
- Sensitivity analysis (tornado charts)

**Functions**:
- `calculate_roi_new_stores()`
- `forecast_revenue()`
- `compare_scenarios()`
- `sensitivity_analysis()`

### 6. Visualization Engine
**Library**: Plotly

**Chart Types**:
- Line charts (trends, forecasts)
- Bar charts (comparisons)
- Pie charts (distributions)
- Waterfall charts (P&L breakdown)
- ROI timelines (cumulative profit)
- Tornado charts (sensitivity)

## Data Flow

### Simple Query Flow
```
User Question
    ↓
Intent Classifier (70b)
    ↓
Single Genie Query
    ↓
Vector Search Enhancement
    ↓
Master Orchestrator Synthesis (405b)
    ↓
Response + Visualization
```

### Complex Multi-Domain Query Flow
```
User Question
    ↓
Intent Classifier (70b)
    ↓
Master Orchestrator Planning (405b)
    ↓
Parallel Genie Queries (Sales + Finance + Strategic)
    ↓
Vector Search Context Gathering
    ↓
Master Orchestrator Synthesis (405b)
    ↓
Response + Multiple Visualizations
```

### Simulation Flow
```
User Scenario Request
    ↓
Intent Classifier (70b)
    ↓
Parameter Extraction
    ↓
Genie Data Gathering
    ↓
Unity Catalog Function Execution
    ↓
Vector Search for Benchmarks
    ↓
Master Orchestrator Analysis (405b)
    ↓
Response + Interactive Charts + Sensitivity Analysis
```

## Technology Stack

**Core Platform**: Databricks
- Foundation Models (LLaMA 3.1 405B, 70B)
- Genie Spaces
- Mosaic AI Vector Search
- Unity Catalog Functions

**Application Framework**: Gradio
- Multi-tab interface
- Real-time chat
- Interactive simulations
- Live dashboards

**Visualization**: Plotly
- Interactive charts
- Executive-level graphics

**Data Processing**:
- Pandas
- NumPy

**APIs**:
- Databricks SDK
- Vector Search Client
- Genie Conversation API

## Scalability Considerations

### Free Edition Optimizations
1. **Compute Quota Management**
   - Query caching (5-minute TTL)
   - Batch similar requests
   - Lazy load visualizations

2. **Response Time Optimization**
   - 70B for quick classifications (<2s)
   - 405B for complex reasoning (<10s)
   - Parallel Genie calls when possible

3. **Token Usage Optimization**
   - Context compression
   - Structured outputs (JSON)
   - Conversation history windowing

## Security & Access Control

- All Databricks credentials via environment variables
- Token-based authentication
- No hardcoded secrets
- Unity Catalog access controls respected

## Monitoring & Logging

- Structured logging throughout
- Component-level loggers:
  - `orchestrator_logger`
  - `genie_logger`
  - `rag_logger`
  - `simulation_logger`
  - `ui_logger`

## Future Enhancements

1. **Additional Genies**: Operations, HR, Marketing
2. **Real-time Alerts**: Anomaly detection on dashboards
3. **Multi-modal**: Image analysis for charts/documents
4. **Collaborative**: Multi-user sessions
5. **Mobile**: Responsive design optimization
6. **Export**: PDF report generation
7. **Integrations**: Slack, Teams, Email notifications

## References

- [Databricks Foundation Models](https://docs.databricks.com/machine-learning/foundation-models/index.html)
- [Databricks Genie](https://docs.databricks.com/genie/index.html)
- [Mosaic AI Vector Search](https://docs.databricks.com/vector-search/index.html)
- [Unity Catalog Functions](https://docs.databricks.com/udf/unity-catalog.html)
