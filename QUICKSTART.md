# 🚀 Quick Start Guide - DecisionMakingArena

Get up and running in 10 minutes!

## Prerequisites

- Python 3.9+
- Databricks Workspace (Free Edition works!)
- Git

## Step 1: Clone & Install (2 min)

```bash
git clone https://github.com/os-angel/DatabricksHackaton25.git
cd DatabricksHackaton25
pip install -r requirements.txt
```

## Step 2: Configure Environment (3 min)

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your credentials
nano .env  # or use your preferred editor
```

**Required Configuration**:
```env
DATABRICKS_WORKSPACE_URL=https://your-workspace.cloud.databricks.com
DATABRICKS_TOKEN=your_token_here
SALES_GENIE_SPACE_ID=your_sales_space_id
FINANCE_GENIE_SPACE_ID=your_finance_space_id
STRATEGIC_GENIE_SPACE_ID=your_strategic_space_id
```

### Getting Databricks Token

1. Go to your Databricks workspace
2. Click on your profile (top right)
3. Go to **Settings** → **Developer** → **Access Tokens**
4. Click **Generate New Token**
5. Copy and paste into `.env`

### Creating Genie Spaces

1. In Databricks, go to **Genie** (in left sidebar)
2. Click **Create Space**
3. Name it (e.g., "Sales Genie")
4. Connect to your data tables
5. Get the Space ID from Settings
6. Repeat for Finance and Strategic spaces

## Step 3: Run the App (1 min)

```bash
python src/ui/app.py
```

The app will launch at `http://localhost:7860`

## Step 4: Try It Out! (4 min)

### Test Query 1: Simple Question
In the **CEO Chat** tab, ask:
```
What were our sales in Q3?
```

### Test Query 2: Complex Analysis
```
Compare our profit margins to industry benchmarks
```

### Test Query 3: Simulation
Switch to **Simulation Studio** tab:
- Select "ROI - New Store Opening"
- Adjust sliders:
  - Number of stores: 5
  - Investment per store: $400,000
  - Expected revenue: $800,000
- Click **Run Simulation**

### Test Query 4: Dashboard
Switch to **Live Dashboard** tab and click **Refresh Dashboard**

## Common Issues & Solutions

### Issue: "Genie space not configured"
**Solution**: Make sure you've created Genie Spaces in Databricks and added their IDs to `.env`

### Issue: "Authentication failed"
**Solution**: Check that your Databricks token is valid and has the correct permissions

### Issue: "Vector Search not available"
**Solution**: The app has fallback mock data. Vector Search is optional for demo purposes.

### Issue: ModuleNotFoundError
**Solution**: Make sure you installed all requirements:
```bash
pip install -r requirements.txt
```

## Demo Mode (Without Databricks)

To test the UI without Databricks connection:

1. The app will use mock data automatically if credentials are missing
2. Most features will work with sample data
3. You'll see warnings in the console but the app will function

## Next Steps

1. **Customize Genies**: Connect to your actual business data
2. **Add Knowledge Base**: Index documents into Vector Search
3. **Create Unity Catalog Functions**: Deploy simulation functions
4. **Customize UI**: Modify themes, add new tabs in `src/ui/app.py`

## Architecture Overview

```
User Question
    ↓
Intent Classifier (70B)
    ↓
Master Orchestrator (405B)
    ↓
Genies (Sales/Finance/Strategic) + Vector Search RAG
    ↓
Unity Catalog Functions (Simulations)
    ↓
Response Synthesis + Visualization
    ↓
Gradio UI Display
```

## Key Files

- **src/ui/app.py** - Main Gradio application
- **src/orchestrator/master_orchestrator.py** - Core logic
- **src/genies/genie_client.py** - Genie integration
- **src/simulations/unity_catalog_functions.py** - Business logic
- **config/settings.py** - Configuration management

## Getting Help

- 📖 Full docs: [README.md](README.md)
- 🏗️ Architecture: [docs/architecture.md](docs/architecture.md)
- 🐛 Issues: [GitHub Issues](https://github.com/os-angel/DatabricksHackaton25/issues)

## Performance Tips

1. **Enable Caching**: Set `APP_ENABLE_CACHING=true` in `.env`
2. **Reduce History**: Set `APP_MAX_CONVERSATION_HISTORY=5` for faster responses
3. **Use 70B for Simple Queries**: Modify model selection in `config/settings.py`

---

**Ready to go!** 🎉

Start asking questions and exploring what DecisionMakingArena can do!
