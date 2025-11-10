# 🎯 DecisionMakingArena

> **AI-Powered Executive Decision Support System**
> *Built for Databricks Hackathon 2025*

An intelligent command center for CEOs and executives that combines multiple AI agents, RAG, and what-if simulations to provide instant, data-driven insights for complex business decisions.

![Architecture](https://img.shields.io/badge/Architecture-Multi--Agent-blue)
![Platform](https://img.shields.io/badge/Platform-Databricks-orange)
![Models](https://img.shields.io/badge/LLMs-LLaMA%203.1-green)
![Status](https://img.shields.io/badge/Status-Hackathon%20Ready-success)

---

## 🌟 Overview

**DecisionMakingArena** is a groundbreaking AI-powered decision support system that democratizes access to executive intelligence. Instead of waiting hours or days for data teams to compile reports, CEOs can now:

- 💬 **Ask natural language questions** and get instant, contextual answers
- 🔬 **Run what-if simulations** to evaluate strategic decisions
- 📊 **Visualize complex data** with executive-level charts
- 🎯 **Access historical context** via RAG-enhanced responses
- 🤖 **Leverage multiple AI agents** that work together seamlessly

### Key Innovation

Unlike simple chatbots, DecisionMakingArena uses a **hierarchical multi-agent architecture** where:
- A **Master Orchestrator** (405B model) plans and coordinates complex queries
- An **Intent Classifier** (70B model) quickly routes requests
- **Multiple specialized Genies** provide domain-specific data
- **Vector Search RAG** enriches responses with business context
- **Unity Catalog Functions** power sophisticated simulations

---

## 🏗️ Architecture

### System Components

```
┌─────────────────────────────────────────────────────┐
│              GRADIO USER INTERFACE                   │
│   CEO Chat | Simulation Studio | Dashboard | History│
└─────────────────┬───────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────┐
│         MASTER ORCHESTRATOR (405B)                   │
│  • Query Planning  • Multi-Agent Coordination        │
│  • Context Enrichment  • Response Synthesis          │
└───────┬─────────────────────────────────────────────┘
        │
   ┌────┴────┬────────────┬──────────────┐
   ▼         ▼            ▼              ▼
┌─────┐  ┌─────┐  ┌──────────┐  ┌────────────┐
│Sales│  │Finance│ │Strategic │  │Vector      │
│Genie│  │Genie  │ │Genie     │  │Search RAG  │
└─────┘  └─────┘  └──────────┘  └────────────┘
                        │
                        ▼
              ┌─────────────────┐
              │Unity Catalog    │
              │Functions        │
              │(Simulations)    │
              └─────────────────┘
```

### Technology Stack

**Platform**: Databricks (Free Edition Compatible)
- **Foundation Models**: LLaMA 3.1 (405B for orchestration, 70B for classification)
- **Genie Spaces**: Sales, Finance, Strategic domain experts
- **Mosaic AI Vector Search**: Knowledge base with business context
- **Unity Catalog Functions**: ROI calculations, forecasting, simulations

**Application**:
- **Framework**: Gradio (multi-tab interface)
- **Visualization**: Plotly (interactive executive charts)
- **Data Processing**: Pandas, NumPy

---

## ✨ Features

### 1. 💬 CEO Chat Interface

Ask natural language questions and get instant insights:

**Example Questions**:
- "What were our Q3 sales and how do they compare to industry benchmarks?"
- "Which products are driving growth this quarter?"
- "Compare our profit margins to last year"

**Response includes**:
- Direct answer with executive summary
- Relevant visualizations
- Historical context from RAG
- Data sources cited

### 2. 🔬 Simulation Studio

Run what-if scenarios with real-time calculations:

**Simulation Types**:
- **ROI Analysis**: New store openings, product launches
- **Revenue Forecasting**: Time-series predictions with confidence intervals
- **Scenario Comparison**: Side-by-side evaluation
- **Sensitivity Analysis**: Identify key variables (tornado charts)

**Interactive Parameters**:
- Adjust sliders for investment amounts, timelines, growth rates
- See instant recalculation of ROI, payback period, NPV, IRR
- Export detailed reports

### 3. 📊 Live Dashboard

Real-time business metrics at a glance:
- Key KPI cards (Revenue, Margin, Customers)
- Trend charts (last 12 months)
- Product mix analysis
- Regional performance heatmaps

### 4. 📚 Analysis History

Track all queries and analyses:
- Searchable conversation history
- Bookmark important insights
- Export past reports

---

## 🚀 Getting Started

### Prerequisites

1. **Databricks Workspace** (Free Edition works!)
2. **Python 3.9+**
3. **Databricks Genies** (3 spaces: Sales, Finance, Strategic)
4. **Vector Search Endpoint** (optional, has fallback mock data)

### Installation

```bash
# Clone the repository
git clone https://github.com/your-username/DatabricksHackaton25.git
cd DatabricksHackaton25

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Edit .env with your Databricks credentials
nano .env
```

### Configuration

Edit `.env` with your Databricks credentials:

```env
DATABRICKS_WORKSPACE_URL=https://your-workspace.cloud.databricks.com
DATABRICKS_TOKEN=your_token_here

# Genie Space IDs (create these in Databricks)
SALES_GENIE_SPACE_ID=your_sales_space_id
FINANCE_GENIE_SPACE_ID=your_finance_space_id
STRATEGIC_GENIE_SPACE_ID=your_strategic_space_id
```

### Setting Up Genies

1. **Create Genie Spaces** in Databricks:
   ```
   - Sales Genie: Connect to sales tables
   - Finance Genie: Connect to financial tables
   - Strategic Genie: Connect to business intelligence tables
   ```

2. **Get Space IDs**: Copy from Genie UI → Settings → Space ID

3. **Update `.env`** with your Space IDs

### Running the Application

```bash
# Launch the Gradio app
python src/ui/app.py
```

The app will start on `http://localhost:7860`

---

## 📖 Usage Examples

### Example 1: Simple Sales Query

**User**: *"What were our sales in Q3?"*

**System**:
1. Intent Classifier → `single_domain, sales`
2. Calls Sales Genie → Gets Q3 sales data
3. Vector Search → Finds Q3 historical trends
4. Master Orchestrator → Synthesizes response:

*"Q3 2024 sales reached $5.2M, representing 19% growth vs Q3 2023. This exceeds the industry average of 12% and marks our strongest Q3 performance in 3 years. Growth was primarily driven by the Premium Widget line (+35%) in the North region."*

**Visualization**: Line chart showing Q3 trends over 3 years

---

### Example 2: Complex Multi-Domain Query

**User**: *"What's our net margin in B2B vs B2C and how does it compare to industry benchmarks?"*

**System**:
1. Intent Classifier → `multi_domain, sales + finance`
2. Parallel execution:
   - Sales Genie → Gets B2B/B2C revenue
   - Finance Genie → Calculates margins
   - Vector Search → Retrieves industry benchmarks
3. Master Orchestrator → Synthesizes:

*"B2B net margin: 15% | B2C net margin: 22%
Industry benchmarks: B2B 12%, B2C 18%
Analysis: We outperform industry by 3pp in B2B and 4pp in B2C, indicating strong operational efficiency and pricing power."*

**Visualization**: Grouped bar chart with benchmark overlay

---

### Example 3: ROI Simulation

**User**: *"If we open 5 new stores with $2M investment, what's the 18-month ROI?"*

**System**:
1. Intent Classifier → `simulation, roi_analysis`
2. Data gathering:
   - Sales Genie → Avg revenue per store
   - Finance Genie → Operating costs
   - Vector Search → Historical store launch performance
3. Unity Catalog Function → `calculate_roi_new_stores()`
4. Generates report:

*"Investment: $2M (5 stores × $400K)
ROI: 28.5% over 18 months
Payback Period: 14 months
Break-Even: Month 11
NPV: $570K | IRR: 22.3%
**Recommendation: ✅ APPROVED** - Strong positive NPV with acceptable risk"*

**Visualizations**:
- Cumulative cash flow timeline
- Sensitivity analysis (tornado chart)
- Scenario comparison

---

## 🛠️ Development

### Project Structure

```
DatabricksHackaton25/
├── config/                    # Configuration
│   ├── settings.py           # Pydantic settings
│   └── model_config.py       # LLM model configs
├── src/
│   ├── orchestrator/         # Core orchestration logic
│   │   ├── intent_classifier.py      # 70B classifier
│   │   ├── master_orchestrator.py    # 405B orchestrator
│   │   └── response_synthesizer.py
│   ├── genies/               # Genie client integrations
│   │   ├── genie_client.py   # Base client
│   │   └── sales_genie.py    # Domain-specific
│   ├── rag/                  # Vector Search RAG
│   │   └── vector_search.py
│   ├── simulations/          # Business logic
│   │   └── unity_catalog_functions.py
│   ├── ui/                   # Gradio interface
│   │   └── app.py            # Main app
│   ├── visualizations/       # Plotly charts
│   │   └── chart_generator.py
│   └── utils/
│       └── logger.py
├── data/                     # Sample datasets
├── notebooks/                # Setup notebooks
├── docs/                     # Documentation
└── tests/                    # Unit tests
```

### Adding New Features

#### Adding a New Genie

1. Create Genie Space in Databricks
2. Add Space ID to `.env`
3. Update `config/settings.py`:
   ```python
   operations_genie_space_id: str = Field(...)
   ```
4. Update Intent Classifier domains

#### Adding a New Simulation

1. Add function to `unity_catalog_functions.py`:
   ```python
   @staticmethod
   def calculate_market_share(...):
       # Your logic here
       return result
   ```
2. Add chart type to `chart_generator.py`
3. Add UI controls in `app.py`

---

## 📊 Supported Chart Types

- **Line Charts**: Trends, forecasts with confidence intervals
- **Bar Charts**: Comparisons, regional performance
- **Pie Charts**: Product mix, market share
- **Waterfall Charts**: P&L breakdown, cash flow
- **ROI Timelines**: Cumulative profit over time
- **Tornado Charts**: Sensitivity analysis
- **Heatmaps**: Regional performance, correlation matrices
- **Scatter Plots**: ROI vs investment, risk/return

---

## 🔧 Configuration

### Model Configuration

Customize LLM behavior in `config/settings.py`:

```python
class ModelConfig(BaseModel):
    # Master Orchestrator
    orchestrator_model: str = "databricks-meta-llama-3-1-405b-instruct"
    orchestrator_temperature: float = 0.7
    orchestrator_max_tokens: int = 2000

    # Intent Classifier
    classifier_model: str = "databricks-meta-llama-3-1-70b-instruct"
    classifier_temperature: float = 0.3
    classifier_max_tokens: int = 500
```

### Performance Tuning

For **Free Edition** optimization:

```python
class AppConfig(BaseModel):
    max_conversation_history: int = 10  # Reduce for lower token usage
    enable_caching: bool = True         # Cache frequent queries
    cache_ttl_seconds: int = 300        # 5-minute cache
```

---

## 🎥 Demo Video Script

**Duration**: 5 minutes

### [00:00-00:30] The Problem
*"CEOs spend 40% of their time asking for data, waiting on reports, and making decisions with incomplete information..."*

### [00:30-01:00] Our Solution
*"DecisionMakingArena: An AI command center that answers complex questions instantly using multiple specialized agents..."*

### [01:00-02:00] Demo 1: Simple Query
- Show chat interface
- Ask: "What were top 3 products in Q3?"
- Highlight: Intent classification → Genie call → RAG enrichment → Response in <5s

### [02:00-03:30] Demo 2: Complex Simulation
- Show simulation studio
- Configure: 5 stores, $2M investment
- Show: ROI timeline, sensitivity analysis, interactive sliders

### [03:30-04:30] Technical Highlights
- Architecture diagram
- Multi-model strategy (405B + 70B)
- Genie integration
- Vector Search RAG
- All in Free Edition!

### [04:30-05:00] Impact & CTA
- "Democratizing executive intelligence"
- GitHub link, try it yourself

---

## 🏆 Why This Wins

### Innovation
✅ **First hierarchical multi-agent system** on Databricks Genies
✅ **Combines 4 Databricks services** in one cohesive application
✅ **Production-ready architecture** with proper orchestration

### Technical Excellence
✅ **Multi-model strategy** (405B for reasoning, 70B for speed)
✅ **RAG enhancement** with Vector Search
✅ **Real simulations** using Unity Catalog Functions
✅ **Professional UI** with Gradio multi-tab interface

### Business Impact
✅ **Saves executive time** - instant vs hours/days
✅ **Better decisions** - context-aware, data-driven insights
✅ **Democratizes BI** - natural language, no SQL needed
✅ **Scalable** - works on Free Edition, ready for Enterprise

### Completeness
✅ **Full implementation** - not a prototype
✅ **Comprehensive docs** - architecture, usage, setup
✅ **Sample data** - ready to run
✅ **Extensible** - easy to add new Genies, simulations

---

## 🚧 Roadmap

### Phase 1: Core ✅ (Complete)
- [x] Master Orchestrator
- [x] Intent Classifier
- [x] Genie integrations
- [x] Vector Search RAG
- [x] Unity Catalog simulations
- [x] Gradio UI

### Phase 2: Enhancements
- [ ] Real-time alerting (anomaly detection)
- [ ] Multi-user collaboration
- [ ] Mobile-responsive design
- [ ] PDF report export
- [ ] Email notifications

### Phase 3: Integrations
- [ ] Slack bot integration
- [ ] Microsoft Teams connector
- [ ] Calendar integration for scheduled reports
- [ ] API for programmatic access

---

## 📚 Documentation

- [Architecture Details](docs/architecture.md)
- [Setup Guide](docs/setup_guide.md) *(coming soon)*
- [API Reference](docs/api_reference.md) *(coming soon)*
- [Deployment Guide](docs/deployment.md) *(coming soon)*

---

## 🤝 Contributing

Built for **Databricks Hackathon 2025** by [@os-angel](https://github.com/os-angel)

Contributions welcome! Please:
1. Fork the repo
2. Create a feature branch
3. Submit a PR with detailed description

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details

---

## 🙏 Acknowledgments

- **Databricks** for the amazing platform and hackathon
- **Meta** for LLaMA 3.1 models
- **Gradio** for the fantastic UI framework
- **Plotly** for beautiful visualizations

---

## 📧 Contact

**Angel** - [@os-angel](https://github.com/os-angel)

**Project Link**: [https://github.com/os-angel/DatabricksHackaton25](https://github.com/os-angel/DatabricksHackaton25)

---

<div align="center">

**⭐ Star this repo if you find it useful!**

Built with ❤️ using Databricks

</div>
