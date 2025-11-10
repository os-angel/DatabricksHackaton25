# 🚀 Quick Deployment Guide

Deploy DecisionMakingArena to production in 30 minutes!

---

## 🎯 Deployment Options

Choose your deployment method:

1. **[Automated Script](#option-1-automated-deployment)** - Fastest (10 min setup)
2. **[Manual Steps](#option-2-manual-deployment)** - Full control (30 min)
3. **[Docker](#option-3-docker-deployment)** - Self-hosted

---

## Option 1: Automated Deployment

### Prerequisites
```bash
# Install Databricks CLI
pip install databricks-cli

# Configure authentication
databricks configure --token
```

### Step 1: Configure Environment (3 min)
```bash
# Copy environment template
cp .env.example .env

# Edit with your credentials
nano .env
```

Add your Databricks workspace URL and token:
```env
DATABRICKS_WORKSPACE_URL=https://your-workspace.cloud.databricks.com
DATABRICKS_TOKEN=dapi123...
```

### Step 2: Run Deployment Script (5 min)
```bash
# Make script executable (if not already)
chmod +x scripts/deploy.sh

# Run full deployment
./scripts/deploy.sh all
```

The script will:
- ✅ Create Databricks secrets
- ✅ Upload notebooks to workspace
- ✅ Deploy the application

### Step 3: Setup Genie Spaces (10 min)

**Manual step required** - Create 3 Genie Spaces in Databricks UI:

1. Go to Databricks → **Genie** → **Create Space**

2. **Sales Genie**:
   - Name: `Production Sales Genie`
   - Connect to: `decision_making_prod.business_data.sales_data`
   - Copy Space ID → Add to `.env` as `SALES_GENIE_SPACE_ID`

3. **Finance Genie**:
   - Name: `Production Finance Genie`
   - Connect to: `decision_making_prod.business_data.financial_data`
   - Copy Space ID → Add to `.env` as `FINANCE_GENIE_SPACE_ID`

4. **Strategic Genie**:
   - Name: `Production Strategic Genie`
   - Connect to: `decision_making_prod.business_data.strategic_metrics`
   - Copy Space ID → Add to `.env` as `STRATEGIC_GENIE_SPACE_ID`

5. Update secrets:
   ```bash
   ./scripts/deploy.sh secrets
   ```

### Step 4: Run Setup Notebooks (10 min)

In Databricks UI:

1. Go to **Workspace** → **Shared** → **DecisionMakingArena**
2. Run notebooks in order:
   - `01_setup_data_tables.py` (creates tables & loads data)
   - `02_setup_vector_search.py` (sets up RAG)
   - `03_deploy_uc_functions.sql` (deploys business logic)

### Step 5: Access Your App! (1 min)

```
https://your-workspace.cloud.databricks.com/apps/decision-making-arena
```

🎉 **Done!** Your app is live!

---

## Option 2: Manual Deployment

### Step 1: Create Data Tables

```sql
-- In Databricks SQL Editor
CREATE CATALOG decision_making_prod;
USE CATALOG decision_making_prod;

CREATE SCHEMA business_data;
USE SCHEMA business_data;

-- Create tables (see notebooks/01_setup_data_tables.py for full SQL)
```

### Step 2: Setup Vector Search

```python
# In Databricks notebook
from databricks.vector_search.client import VectorSearchClient

vsc = VectorSearchClient()

# Create endpoint
vsc.create_endpoint(
    name="decision_making_vs_endpoint",
    endpoint_type="STANDARD"
)

# Create index (see notebooks/02_setup_vector_search.py for details)
```

### Step 3: Deploy Unity Catalog Functions

```sql
-- In Databricks SQL Editor
-- See notebooks/03_deploy_uc_functions.sql for full SQL
CREATE FUNCTION calculate_roi_stores(...);
-- ... other functions
```

### Step 4: Create Databricks Secrets

```bash
# Create scope
databricks secrets create-scope decision_making_secrets

# Add secrets
echo "your_token" | databricks secrets put-secret \
  --scope decision_making_secrets \
  --key databricks_token

# Repeat for all secrets in .env
```

### Step 5: Deploy App

**Option A: Using Databricks Apps**
```bash
databricks apps deploy app.yaml
```

**Option B: Using Databricks CLI**
```bash
# Upload code to workspace
databricks workspace import-dir . /Workspace/DecisionMakingArena

# Create job to run app
databricks jobs create --json-file job_config.json
```

---

## Option 3: Docker Deployment

### Build Image
```bash
docker build -t decision-making-arena:latest .
```

### Run Locally
```bash
docker run -p 7860:7860 \
  -e DATABRICKS_WORKSPACE_URL=your_url \
  -e DATABRICKS_TOKEN=your_token \
  -e SALES_GENIE_SPACE_ID=space_id \
  decision-making-arena:latest
```

### Deploy to Cloud

**AWS ECS/Fargate**:
```bash
# Push to ECR
aws ecr get-login-password | docker login --username AWS --password-stdin
docker tag decision-making-arena:latest ${ECR_URI}:latest
docker push ${ECR_URI}:latest

# Create ECS service
aws ecs create-service --cluster my-cluster --service-name decision-making-arena ...
```

**Azure Container Instances**:
```bash
az container create \
  --resource-group my-rg \
  --name decision-making-arena \
  --image your-registry/decision-making-arena:latest \
  --ports 7860
```

**Google Cloud Run**:
```bash
gcloud run deploy decision-making-arena \
  --image gcr.io/project/decision-making-arena:latest \
  --port 7860
```

---

## 🔍 Verification Checklist

After deployment, verify:

- [ ] **Data Tables** exist and have data
  ```sql
  SELECT COUNT(*) FROM decision_making_prod.business_data.sales_data;
  ```

- [ ] **Vector Search** index is online
  ```python
  vsc.get_index("decision_making_vs_endpoint", "...index_name...").status
  ```

- [ ] **Genies** respond to test questions
  - Sales: "What were total sales last month?"
  - Finance: "Show me revenue breakdown"

- [ ] **Unity Catalog Functions** work
  ```sql
  SELECT calculate_roi_stores(5, 400000, 800000, 0.65, 18);
  ```

- [ ] **App** loads and responds
  - Open app URL
  - Ask test question: "What were our Q3 sales?"

---

## 🐛 Troubleshooting

### Issue: "Secrets scope not found"
```bash
# Create scope
databricks secrets create-scope decision_making_secrets
```

### Issue: "Table not found"
```bash
# Run setup notebooks first
# Or create tables manually (see notebooks/)
```

### Issue: "Genie space not configured"
```bash
# Check .env has correct Space IDs
# Recreate secrets: ./scripts/deploy.sh secrets
```

### Issue: "Vector Search endpoint not ready"
```bash
# Wait 5-10 minutes for endpoint to come online
# Check status in Databricks UI → Vector Search
```

### Issue: "App not accessible"
```bash
# Check app status
databricks apps get decision-making-arena

# View logs
databricks apps logs decision-making-arena
```

---

## 📊 Post-Deployment

### Monitor Usage
```sql
-- Create monitoring queries
SELECT
    DATE_TRUNC('hour', timestamp) as hour,
    COUNT(*) as queries,
    AVG(execution_time_seconds) as avg_time
FROM decision_making_prod.monitoring.usage_logs
GROUP BY 1
ORDER BY 1 DESC;
```

### Update Knowledge Base
```python
# Add new documents to RAG
new_docs = [{
    "id": "new_001",
    "content": "Your context...",
    "category": "category"
}]

# Insert and sync
spark.createDataFrame(new_docs).write.mode("append").saveAsTable("knowledge_base")
vsc.get_index(...).sync()
```

### Scale Resources
```yaml
# Update app.yaml
scaling:
  min_instances: 2  # Increase for high traffic
  max_instances: 10
```

---

## 🎓 Training Users

### For Executives
Share this quick guide:

**Example Questions to Try**:
1. "What were our sales in Q3 and how do they compare to last year?"
2. "Calculate ROI if we open 5 new stores with $2M investment"
3. "Show me our profit margins vs industry benchmarks"
4. "Forecast revenue for the next 6 months"

**Using Simulation Studio**:
1. Go to **Simulation Studio** tab
2. Adjust sliders for your scenario
3. Click **Run Simulation**
4. Review ROI timeline and sensitivity analysis

### For Admins

**Daily Monitoring**:
- Check error logs in Databricks
- Review usage metrics
- Monitor response times

**Weekly Maintenance**:
- Update knowledge base documents
- Review popular queries
- Optimize slow queries

---

## 📞 Support

**Documentation**:
- [Full Documentation](README.md)
- [Architecture Details](docs/architecture.md)
- [Detailed Deployment Guide](docs/deployment.md)

**Common Issues**:
- Check [Troubleshooting](#troubleshooting) section above
- View app logs: `databricks apps logs decision-making-arena`
- GitHub Issues: [Report a bug](https://github.com/os-angel/DatabricksHackaton25/issues)

---

## ⚡ Quick Commands Reference

```bash
# Check deployment status
databricks apps get decision-making-arena

# View logs
databricks apps logs decision-making-arena --tail

# Update secrets
./scripts/deploy.sh secrets

# Redeploy app
databricks apps deploy app.yaml

# Test connection
databricks workspace ls /

# List functions
databricks sql execute "SHOW FUNCTIONS IN decision_making_prod.analytics_functions"
```

---

**Need help?** Check the [full deployment guide](docs/deployment.md) or [open an issue](https://github.com/os-angel/DatabricksHackaton25/issues)

**Ready to deploy?** Run: `./scripts/deploy.sh all`
