# 🧬 BIOLABS - Multi-Agent Business Intelligence System

![Databricks](https://img.shields.io/badge/Databricks-Free%20Edition-orange)
![Python](https://img.shields.io/badge/Python-3.10+-blue)
![License](https://img.shields.io/badge/License-MIT-green)

## 📋 Overview

**BIOLABS** is an innovative Multi-Agent Business Intelligence System built entirely on **Databricks Free Edition**. It enables a CEO to consult 4 specialized AI agents (Operations, Marketing, Finance, and Scientific) that synthesize transactional data with scientific knowledge for strategic decision-making.

### 🎯 Key Features

- **4 Specialized Agents**: Operations, Marketing, Finance, Scientific Advisor
- **Genie Spaces Integration**: 3 business agents with curated data access
- **Multimodal RAG**: Scientific papers with chart interpretation using vision models
- **MCP Server**: 12 business simulation and calculation tools
- **CEO Orchestrator**: Intelligent query routing and response synthesis
- **Real-time Simulations**: What-if scenarios for business decisions

### 🏆 What Makes This Unique

1. **Only project** combining Genie Spaces + Multimodal RAG + MCP
2. **Scientific knowledge integration** with real research papers and vision-based chart interpretation
3. **CEO-level orchestration** pattern for executive decision support
4. **100% Databricks Free Edition** - no custom clusters or GPUs needed

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  PRESENTATION LAYER                     │
│              Gradio App (Databricks App)                │
│  • CEO Command Center Interface                         │
│  • 4-tab layout: Strategy | Science | Simulation        │
│  • Real-time chat + visualizations                      │
└───────────────────────┬─────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────┐
│                 ORCHESTRATION LAYER                     │
│              CEO Orchestrator Agent                      │
│  • Query decomposition                                  │
│  • Agent routing                                        │
│  • Response synthesis                                   │
└───────────────────────┬─────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┬─────────────┐
        │               │               │             │
┌───────▼────┐  ┌──────▼──────┐  ┌────▼─────┐  ┌───▼──────┐
│  GENIE     │  │   GENIE     │  │  GENIE   │  │   RAG    │
│ Operations │  │  Marketing  │  │ Finance  │  │Scientific│
└───────┬────┘  └──────┬──────┘  └────┬─────┘  └───┬──────┘
        │               │               │             │
        └───────────────┴───────────────┴─────────────┘
                        │
┌───────────────────────▼─────────────────────────────────┐
│                   TOOLS LAYER                           │
│                   MCP Server                            │
│  • 4 Simulation tools                                   │
│  • 4 Calculation tools                                  │
│  • 4 Data aggregation tools                             │
└───────────────────────┬─────────────────────────────────┘
                        │
        ┌───────────────┼────────────────┬──────────────┐
        │               │                │              │
┌───────▼────┐  ┌──────▼──────┐  ┌─────▼──────┐  ┌────▼─────┐
│   VECTOR   │  │    UNITY    │  │  EXTERNAL  │  │ VOLUMES  │
│   SEARCH   │  │   CATALOG   │  │    APIs    │  │  (PDFs)  │
└────────────┘  └─────────────┘  └────────────┘  └──────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- Databricks Free Edition account
- Python 3.10+
- [uv](https://github.com/astral-sh/uv) package manager
- Databricks CLI configured

### Installation

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone repository
git clone https://github.com/os-angel/DatabricksHackaton25.git
cd DatabricksHackaton25

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
uv pip install -e .

# Configure environment
cp .env.example .env
# Edit .env with your Databricks credentials
```

### Setup Steps

1. **Generate Synthetic Data**
```bash
python data_generation/generate_synthetic_data.py
```

2. **Setup Unity Catalog**
```bash
databricks workspace import databricks/unity_catalog_setup.sql
```

3. **Process Scientific PDFs**
```bash
# Upload PDFs to Databricks workspace, then run:
databricks workspace import databricks/notebooks/01_pdf_processing_pipeline.py
```

4. **Deploy MCP Server**
```bash
cd mcp_server
python server.py
```

5. **Launch Gradio App**
```bash
cd gradio_app
python app.py
```

For detailed setup instructions, see [SETUP_GUIDE.md](docs/SETUP_GUIDE.md)

---

## 📊 Business Context: BioLabs

**BioLabs** is a fictional company manufacturing 3 innovative sugar substitutes:

### Products

- **Tagatose**: Premium natural sweetener for health-conscious consumers
  - COGS: $8/kg, Retail: $24/kg
  - 24-month shelf life
  - Slower turnover, premium positioning

- **Allulose**: Science-backed, zero-net-carb solution
  - COGS: $12/kg, Retail: $36/kg
  - 18-month shelf life
  - Fast mover in keto/diabetic segments

- **Trehalose**: Sustained energy for athletes
  - COGS: $6/kg, Retail: $18/kg
  - 36-month shelf life
  - Steady in athletic/hospital channels

### Distribution Channels

1. **Pharmacies**: High margin (45%), educational sales
2. **Specialty Groceries**: Medium margin (35%), fast adoption
3. **Gyms**: High margin (40%), demo-intensive
4. **Hospitals**: Low margin (25%), long sales cycle

---

## 🎯 Agent Capabilities

### 1. Operations Specialist (Genie Space)

**Data Access:**
- Sales transactions (100K+ rows)
- Inventory levels
- POS master data
- Distribution routes
- Production batches

**Expertise:**
- Inventory management (days on hand, fill rates)
- Distribution feasibility
- Production capacity planning
- Channel performance analysis

### 2. Marketing Specialist (Genie Space)

**Data Access:**
- Campaign performance
- Customer segments
- Competitor intelligence
- Social sentiment
- Channel economics

**Expertise:**
- Customer acquisition cost (CAC) analysis
- Lifetime value (LTV) projections
- Market sizing
- Competitive positioning
- Channel strategy

### 3. Finance Analyst (Genie Space)

**Data Access:**
- Product costs (COGS)
- Revenue by channel
- Budget tracking
- Pricing history
- Margin analysis

**Expertise:**
- ROI calculations
- Break-even analysis
- NPV projections
- Margin optimization
- Financial scenario modeling

### 4. Scientific Advisor (RAG Agent)

**Knowledge Base:**
- 15+ clinical trial papers
- Regulatory documents (FDA GRAS, EFSA opinions)
- Patent filings
- Meta-analyses and reviews

**Capabilities:**
- Multimodal understanding (text + charts)
- Vision-based graph interpretation
- Citation tracking
- Evidence synthesis
- Regulatory status checking

---

## 🛠️ MCP Tools (12)

### Simulation Tools (4)

1. **simulate_price_change**: Model price elasticity and revenue impact
2. **simulate_campaign_roi**: Project marketing campaign returns
3. **simulate_channel_expansion**: Forecast new channel launch outcomes
4. **simulate_production_capacity**: Assess manufacturing constraints

### Calculation Tools (4)

5. **calculate_product_margin**: Compute margins by product/channel
6. **calculate_inventory_turnover**: Analyze inventory efficiency
7. **calculate_customer_ltv**: Project customer lifetime value
8. **calculate_break_even**: Determine break-even points

### Data Tools (4)

9. **get_sales_summary**: Aggregate sales data by dimensions
10. **get_inventory_status**: Check current inventory health
11. **get_competitor_intel**: Retrieve competitive landscape data
12. **get_customer_segments**: Access customer segmentation analysis

---

## 💡 Example CEO Queries

### Strategy Question
```
"Should we launch Allulose in specialty gyms?"
```

**System Response:**
- **Scientific Advisor**: "3 clinical trials show 18% glycogen preservation in athletes..."
- **Marketing**: "Market size 3.2M athletes, CAC $450, LTV $1,260..."
- **Operations**: "Distribution feasible, 90% coverage achievable in 4 months..."
- **Finance**: "ROI 28%, payback 3.9 months, NPV $2.4M..."
- **Synthesis**: "PROCEED with pilot in 50 locations. Conservative scenario: $800K revenue Y1..."

### Scientific Question
```
"What evidence exists for Allulose reducing post-exercise inflammation?"
```

**System Response:**
- Retrieves relevant papers from Vector Search
- Interprets charts showing cytokine levels
- Synthesizes findings with citations
- Notes gaps in literature
- Provides regulatory status

### Operational Question
```
"Which products have inventory risk in the next 30 days?"
```

**System Response:**
- Queries real-time inventory data
- Calculates days on hand
- Identifies products below safety stock
- Recommends production priorities

---

## 📈 Data Schema

### Unity Catalog Structure

```
biolabs_catalog/
├── operations/
│   ├── sales_transactions
│   ├── inventory_levels
│   ├── pos_master
│   ├── distribution_routes
│   └── production_batches
├── marketing/
│   ├── campaigns
│   ├── customer_segments
│   ├── competitor_intel
│   └── channel_performance
├── finance/
│   ├── product_costs
│   ├── revenue_by_channel
│   ├── budgets
│   └── margin_analysis
└── scientific/
    ├── documents (Delta table for RAG)
    └── raw_pdfs/ (Unity Catalog Volume)
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed schema definitions.

---

## 🎬 Demo Video Structure

1. **Hook (0:00-0:45)**: Problem statement - CEO decision complexity
2. **Solution (0:45-1:00)**: Multi-agent system introduction
3. **Demo (1:00-3:00)**:
   - CEO query input
   - 4 agents responding in parallel
   - Scientific chart interpretation
   - Synthesis with visualizations
4. **Technical Deep Dive (3:00-4:00)**:
   - Genie Spaces config
   - Multimodal RAG pipeline
   - MCP tools
   - Orchestration logic
5. **Impact (4:00-4:45)**: Differentiation and business value
6. **Call to Action (4:45-5:00)**: GitHub, replicability

---

## 📚 Documentation

- [Architecture Deep Dive](docs/ARCHITECTURE.md)
- [Setup Guide](docs/SETUP_GUIDE.md)
- [Genie Spaces Configuration](docs/GENIE_SPACES_CONFIG.md)
- [MCP Tools Reference](mcp_server/README.md)
- [Gradio App Guide](gradio_app/README.md)

---

## 🔧 Technology Stack

- **Platform**: Databricks Free Edition
- **Orchestration**: Custom Python + Databricks SDK
- **Business Agents**: Genie Spaces (3)
- **Scientific RAG**: Vector Search + Vision Models
- **Tools**: FastMCP Server
- **Frontend**: Gradio
- **Data**: Unity Catalog (Delta Lake)
- **LLMs**: Databricks Foundation Models + Claude Sonnet 4

---

## 🎯 Hackathon Alignment

### Technical Complexity ✅
- 4 specialized agents with different data sources
- Multimodal RAG with vision interpretation
- MCP server with 12 custom tools
- Orchestration layer with intelligent routing

### Creativity & Innovation ✅
- Unique combination of Genie + RAG + MCP
- CEO orchestrator pattern
- Scientific advisor with real papers
- Business narrative (BioLabs)

### Presentation ✅
- Professional Gradio interface
- Clear value proposition
- Structured demo flow
- Visual architecture diagrams

### Impact & Learning ✅
- Replicable template for any industry
- Open-source code
- Comprehensive documentation
- Community teaching resource

---

## 🚧 Roadmap

- [x] Project architecture design
- [x] Repository structure setup
- [ ] Synthetic data generation
- [ ] Unity Catalog setup
- [ ] Genie Spaces configuration
- [ ] PDF processing pipeline
- [ ] Vector Search index creation
- [ ] MCP server implementation
- [ ] Gradio app development
- [ ] CEO orchestrator logic
- [ ] End-to-end testing
- [ ] Documentation finalization
- [ ] Demo video production

---

## 🤝 Contributing

This is a hackathon project, but contributions and feedback are welcome!

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file

---

## 👨‍💻 Author

**Angel Maraver**
- GitHub: [@os-angel](https://github.com/os-angel)
- LinkedIn: [Angel Maraver](https://linkedin.com/in/angel-maraver)

---

## 🙏 Acknowledgments

- Databricks team for the incredible Free Edition
- Hackathon organizers
- Open-source community

---

**Built with ❤️ for Databricks Hackathon 2025**
