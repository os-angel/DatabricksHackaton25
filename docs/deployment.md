# 🚀 Deployment Guide - DecisionMakingArena

Complete guide to deploy DecisionMakingArena to production on Databricks.

---

## 📋 Deployment Overview

**Three Deployment Options**:

1. **Databricks Apps** (Recommended) - Native Databricks hosting
2. **Docker Container** - Self-hosted or cloud (AWS, Azure, GCP)
3. **Serverless** - AWS Lambda/Azure Functions with API Gateway

This guide covers **Option 1: Databricks Apps** in detail.

---

## 🎯 Option 1: Deploy as Databricks App (Recommended)

### Prerequisites

- Databricks Workspace (Standard or Premium tier for Apps)
- Unity Catalog enabled
- Admin or workspace creator permissions
- Databricks CLI installed

### Architecture in Production

```
┌─────────────────────────────────────────────────┐
│         DATABRICKS APP                          │
│   (Gradio running on Databricks compute)        │
└─────────────────┬───────────────────────────────┘
                  │
    ┌─────────────┼─────────────┐
    ▼             ▼             ▼
┌────────┐  ┌──────────┐  ┌────────────┐
│Genies  │  │Vector    │  │Unity       │
│Spaces  │  │Search    │  │Catalog Fns │
└────────┘  └──────────┘  └────────────┘
```

---

## 📝 Step-by-Step Production Deployment

### Step 1: Prepare Data Tables (15 min)

First, upload your business data to Databricks:

```sql
-- 1.1 Create catalog and schema
CREATE CATALOG IF NOT EXISTS decision_making_prod;
USE CATALOG decision_making_prod;

CREATE SCHEMA IF NOT EXISTS business_data;
USE SCHEMA business_data;

-- 1.2 Create sales table
CREATE TABLE sales_data (
    date DATE,
    product_id STRING,
    product_name STRING,
    category STRING,
    region STRING,
    units_sold INT,
    revenue DECIMAL(10,2),
    cost DECIMAL(10,2),
    profit_margin DECIMAL(5,4)
) USING DELTA;

-- 1.3 Create finance table
CREATE TABLE financial_data (
    date DATE,
    account STRING,
    category STRING,
    amount DECIMAL(10,2),
    type STRING -- 'revenue', 'cost', 'investment'
) USING DELTA;

-- 1.4 Create strategic data table
CREATE TABLE strategic_metrics (
    date DATE,
    metric_name STRING,
    metric_value DECIMAL(10,2),
    target DECIMAL(10,2),
    category STRING
) USING DELTA;

-- 1.5 Load your data
-- Option A: From CSV
COPY INTO sales_data
FROM '/path/to/your/sales.csv'
FILEFORMAT = CSV
FORMAT_OPTIONS ('header' = 'true');

-- Option B: From existing tables
INSERT INTO sales_data
SELECT * FROM your_existing_sales_table;
```

### Step 2: Create Genie Spaces (10 min)

**2.1 Sales Genie**
1. Go to Databricks workspace → **Genie** (left sidebar)
2. Click **Create Space**
3. Configure:
   - Name: `Production Sales Genie`
   - Description: `Sales data analysis for DecisionMakingArena`
   - Connect to tables: `decision_making_prod.business_data.sales_data`
4. Click **Create**
5. **Copy Space ID** from Settings → paste in `.env`

**2.2 Finance Genie**
1. Create Space
2. Configure:
   - Name: `Production Finance Genie`
   - Description: `Financial data analysis`
   - Connect to tables: `decision_making_prod.business_data.financial_data`
3. **Copy Space ID** → paste in `.env`

**2.3 Strategic Genie**
1. Create Space
2. Configure:
   - Name: `Production Strategic Genie`
   - Description: `Strategic metrics analysis`
   - Connect to tables: `decision_making_prod.business_data.strategic_metrics`
3. **Copy Space ID** → paste in `.env`

**2.4 Test Genies**
In each Genie, ask test questions:
- Sales: "What were total sales last month?"
- Finance: "What's our current burn rate?"
- Strategic: "Show me KPI performance vs targets"

### Step 3: Setup Vector Search (20 min)

**3.1 Create Vector Search Endpoint**

```python
from databricks.sdk import WorkspaceClient
from databricks.vector_search.client import VectorSearchClient

w = WorkspaceClient()
vsc = VectorSearchClient(workspace_url=w.config.host)

# Create endpoint
vsc.create_endpoint(
    name="decision_making_vs_endpoint",
    endpoint_type="STANDARD"
)
```

**3.2 Prepare Knowledge Base Documents**

```sql
-- Create documents table
CREATE TABLE decision_making_prod.business_data.knowledge_base (
    id STRING,
    content STRING,
    category STRING,
    metadata MAP<STRING, STRING>,
    embedding ARRAY<DOUBLE>  -- Will be auto-generated
) USING DELTA;

-- Insert your business context documents
INSERT INTO knowledge_base VALUES
(
    'ctx_001',
    'Q3 historically shows 15-20% growth due to holiday season preparation. Key drivers: retail inventory buildup, promotional campaigns.',
    'historical_context',
    map('period', 'Q3', 'years', '2020-2023')
),
(
    'ctx_002',
    'Industry benchmark for retail net margin: B2B 12-15%, B2C 18-22%. Our company targets: B2B 15%, B2C 22%.',
    'benchmark',
    map('industry', 'retail', 'metric', 'net_margin')
),
-- Add more documents...
;
```

**3.3 Create Vector Index**

```python
# Create index on knowledge base
vsc.create_delta_sync_index(
    endpoint_name="decision_making_vs_endpoint",
    index_name="decision_making_prod.business_data.knowledge_base_index",
    source_table_name="decision_making_prod.business_data.knowledge_base",
    pipeline_type="TRIGGERED",
    primary_key="id",
    embedding_source_column="content",
    embedding_model_endpoint_name="databricks-bge-large-en"
)
```

**3.4 Wait for Indexing**
```python
# Check status
index = vsc.get_index(
    endpoint_name="decision_making_vs_endpoint",
    index_name="decision_making_prod.business_data.knowledge_base_index"
)
print(f"Status: {index.status}")
```

### Step 4: Deploy Unity Catalog Functions (15 min)

**4.1 Create Schema for Functions**

```sql
USE CATALOG decision_making_prod;
CREATE SCHEMA IF NOT EXISTS analytics_functions;
USE SCHEMA analytics_functions;
```

**4.2 Deploy ROI Calculation Function**

```sql
CREATE OR REPLACE FUNCTION calculate_roi_stores(
    num_stores INT,
    investment_per_store DOUBLE,
    avg_revenue_per_store DOUBLE,
    cost_ratio DOUBLE,
    forecast_months INT
)
RETURNS STRUCT<
    roi_percentage: DOUBLE,
    payback_months: INT,
    total_profit: DOUBLE,
    npv: DOUBLE
>
LANGUAGE PYTHON
AS $$
import numpy as np

# Calculate monthly revenue
monthly_revenue = avg_revenue_per_store / 12 * num_stores

# Calculate costs
monthly_costs = monthly_revenue * cost_ratio

# Initialize
total_investment = num_stores * investment_per_store
cumulative = -total_investment
monthly_cf = []
payback_month = None

# Calculate each month
for month in range(1, forecast_months + 1):
    # Ramp-up factor (S-curve)
    if month <= 6:
        ramp = 1 / (1 + np.exp(-2 * (month/6 - 0.5)))
    else:
        ramp = 1.0

    # Net cash flow
    net_cf = (monthly_revenue * ramp) - monthly_costs
    monthly_cf.append(net_cf)
    cumulative += net_cf

    # Track payback
    if payback_month is None and cumulative >= 0:
        payback_month = month

# Calculate ROI
total_profit = sum(monthly_cf)
roi = (total_profit / total_investment) * 100

# Calculate NPV (10% discount rate)
npv = -total_investment
for i, cf in enumerate(monthly_cf, 1):
    npv += cf / ((1 + 0.10/12) ** i)

return {
    'roi_percentage': round(roi, 2),
    'payback_months': payback_month or forecast_months,
    'total_profit': round(total_profit, 2),
    'npv': round(npv, 2)
}
$$;
```

**4.3 Test the Function**

```sql
SELECT calculate_roi_stores(5, 400000, 800000, 0.65, 18) AS result;
```

### Step 5: Configure Production Environment (5 min)

**5.1 Create Production .env**

```bash
# Production Environment Configuration

# Databricks
DATABRICKS_WORKSPACE_URL=https://your-workspace.cloud.databricks.com
DATABRICKS_TOKEN=<use_secret_scope>  # See Step 5.2
DATABRICKS_WAREHOUSE_ID=<your_warehouse_id>

# Genies (from Step 2)
SALES_GENIE_SPACE_ID=<sales_space_id>
FINANCE_GENIE_SPACE_ID=<finance_space_id>
STRATEGIC_GENIE_SPACE_ID=<strategic_space_id>

# Vector Search
VECTOR_SEARCH_ENDPOINT_NAME=decision_making_vs_endpoint
VECTOR_SEARCH_INDEX_NAME=decision_making_prod.business_data.knowledge_base_index

# Models
MODEL_ORCHESTRATOR_MODEL=databricks-meta-llama-3-1-405b-instruct
MODEL_CLASSIFIER_MODEL=databricks-meta-llama-3-1-70b-instruct

# App Settings
DEBUG=false
APP_MAX_CONVERSATION_HISTORY=10
APP_ENABLE_CACHING=true
APP_CACHE_TTL_SECONDS=300
```

**5.2 Use Databricks Secrets (Recommended)**

```bash
# Install Databricks CLI
pip install databricks-cli

# Configure
databricks configure --token

# Create secret scope
databricks secrets create-scope decision_making_secrets

# Add token
databricks secrets put-secret decision_making_secrets databricks_token
# Paste your token when prompted

# Update config/settings.py to read from secrets:
```

```python
# In config/settings.py, update:
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()
token = w.dbutils.secrets.get(scope="decision_making_secrets", key="databricks_token")
```

### Step 6: Create Databricks App (10 min)

**6.1 Create app.yml**

```yaml
# app.yml
command: ["python", "src/ui/app.py"]

resources:
  - name: decision-making-arena
    description: AI-Powered Executive Decision Support
    port: 7860

env:
  - name: DATABRICKS_WORKSPACE_URL
    value: https://your-workspace.cloud.databricks.com
  - name: SALES_GENIE_SPACE_ID
    valueFrom:
      secretKeyRef:
        name: decision_making_secrets
        key: sales_genie_space_id
  # Add other env vars...
```

**6.2 Update src/ui/app.py for Production**

Add at the beginning:

```python
# src/ui/app.py - Production mode
import os

# Production configuration
PRODUCTION_MODE = os.getenv("PRODUCTION_MODE", "false").lower() == "true"

if PRODUCTION_MODE:
    # Use Databricks secrets
    from databricks.sdk import WorkspaceClient
    w = WorkspaceClient()

    settings.databricks.token = w.dbutils.secrets.get(
        scope="decision_making_secrets",
        key="databricks_token"
    )
```

**6.3 Deploy the App**

```bash
# Using Databricks CLI
databricks apps create \
  --app-name decision-making-arena \
  --source-path . \
  --description "AI-Powered Executive Decision Support System"

# Or via UI:
# 1. Go to Databricks workspace → Apps
# 2. Click "Create App"
# 3. Upload your code or connect Git repo
# 4. Configure environment variables
# 5. Click "Deploy"
```

**6.4 Access Your App**

```
https://your-workspace.cloud.databricks.com/apps/decision-making-arena
```

### Step 7: Configure Access & Security (10 min)

**7.1 Set App Permissions**

```sql
-- Grant access to specific users/groups
GRANT USE ON APP decision_making_arena TO GROUP executives;
GRANT USE ON APP decision_making_arena TO USER ceo@company.com;

-- Grant access to underlying data
GRANT SELECT ON CATALOG decision_making_prod TO GROUP executives;
GRANT EXECUTE ON FUNCTION decision_making_prod.analytics_functions.calculate_roi_stores
  TO GROUP executives;
```

**7.2 Enable SSO (Optional)**

In Databricks workspace settings:
1. Go to **Admin Console** → **Authentication**
2. Enable **SSO** (SAML or OAuth)
3. Configure your identity provider
4. Users will auto-authenticate when accessing the app

### Step 8: Setup Monitoring & Logging (10 min)

**8.1 Enable App Logs**

```python
# Update src/utils/logger.py
import logging
from databricks.sdk.runtime import dbutils

def setup_production_logging():
    """Setup logging to Databricks"""
    handler = logging.StreamHandler()

    # In Databricks, logs automatically go to:
    # Workspace → Apps → decision-making-arena → Logs

    logger = logging.getLogger("decision_making_arena")
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    return logger
```

**8.2 Create Usage Tracking Table**

```sql
CREATE TABLE decision_making_prod.monitoring.usage_logs (
    timestamp TIMESTAMP,
    user_id STRING,
    query_type STRING,
    execution_time_seconds DOUBLE,
    tokens_used INT,
    success BOOLEAN,
    error_message STRING
) USING DELTA
PARTITIONED BY (DATE(timestamp));
```

**8.3 Add Telemetry to Orchestrator**

```python
# In src/orchestrator/master_orchestrator.py
from databricks.sdk import WorkspaceClient
from pyspark.sql import SparkSession

class MasterOrchestrator:
    def __init__(self):
        # ... existing code ...
        self.spark = SparkSession.builder.getOrCreate()

    async def process_question(self, question, context):
        start_time = time.time()
        success = True
        error_msg = None

        try:
            result = await self._process(question, context)
        except Exception as e:
            success = False
            error_msg = str(e)
            raise
        finally:
            # Log usage
            duration = time.time() - start_time
            self._log_usage(question, duration, success, error_msg)

        return result

    def _log_usage(self, query, duration, success, error):
        from datetime import datetime

        log_data = [(
            datetime.now(),
            self.get_current_user(),
            "query",
            duration,
            0,  # token count if available
            success,
            error
        )]

        df = self.spark.createDataFrame(log_data, [
            "timestamp", "user_id", "query_type",
            "execution_time_seconds", "tokens_used",
            "success", "error_message"
        ])

        df.write.mode("append").saveAsTable(
            "decision_making_prod.monitoring.usage_logs"
        )
```

**8.4 Create Monitoring Dashboard**

```sql
-- Create SQL dashboard in Databricks
-- Queries per hour
SELECT
    DATE_TRUNC('hour', timestamp) as hour,
    COUNT(*) as query_count,
    AVG(execution_time_seconds) as avg_time,
    SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful_queries
FROM decision_making_prod.monitoring.usage_logs
WHERE timestamp >= CURRENT_DATE - INTERVAL 7 DAYS
GROUP BY 1
ORDER BY 1 DESC;

-- Most active users
SELECT
    user_id,
    COUNT(*) as queries,
    AVG(execution_time_seconds) as avg_response_time
FROM decision_making_prod.monitoring.usage_logs
WHERE timestamp >= CURRENT_DATE - INTERVAL 7 DAYS
GROUP BY 1
ORDER BY 2 DESC
LIMIT 10;
```

---

## 🔄 Option 2: Docker Deployment

If you want to self-host outside Databricks:

**Dockerfile**:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose Gradio port
EXPOSE 7860

# Run app
CMD ["python", "src/ui/app.py"]
```

**Deploy**:

```bash
# Build
docker build -t decision-making-arena:latest .

# Run locally
docker run -p 7860:7860 \
  -e DATABRICKS_WORKSPACE_URL=your_url \
  -e DATABRICKS_TOKEN=your_token \
  decision-making-arena:latest

# Or push to cloud
docker tag decision-making-arena:latest your-registry/decision-making-arena:latest
docker push your-registry/decision-making-arena:latest
```

---

## 🐛 Troubleshooting Production Issues

### Issue: "Authentication failed"
**Solution**:
- Check token hasn't expired
- Verify workspace URL is correct
- Ensure service principal has correct permissions

### Issue: "Genie space not found"
**Solution**:
- Verify Space IDs in .env
- Check Genie spaces exist and are active
- Ensure app has permission to access spaces

### Issue: "Vector search timeout"
**Solution**:
- Check endpoint is running: `vsc.get_endpoint("decision_making_vs_endpoint")`
- Verify index is synced
- Increase timeout in config

### Issue: "High latency"
**Solution**:
- Enable caching: `APP_ENABLE_CACHING=true`
- Use smaller models for simple queries (70B instead of 405B)
- Add request batching

### Issue: "Out of compute quota"
**Solution**:
- Upgrade to Standard tier
- Optimize query frequency
- Implement rate limiting

---

## 📊 Production Checklist

Before going live:

- [ ] All Genie Spaces created and tested
- [ ] Vector Search indexed with production data
- [ ] Unity Catalog Functions deployed and tested
- [ ] Environment variables configured with secrets
- [ ] Access permissions configured (users/groups)
- [ ] Monitoring and logging enabled
- [ ] Usage dashboard created
- [ ] Error alerting configured
- [ ] Backup strategy for conversation history
- [ ] Load testing completed (10+ concurrent users)
- [ ] Security review passed
- [ ] Documentation updated for users
- [ ] Training completed for executive team

---

## 🔐 Security Best Practices

1. **Never commit tokens**: Use Databricks secrets
2. **Principle of least privilege**: Grant minimum required permissions
3. **Audit logging**: Track all queries and access
4. **Data governance**: Use Unity Catalog for data lineage
5. **Network security**: Use private endpoints if available
6. **Rate limiting**: Prevent abuse
7. **Input validation**: Sanitize user queries
8. **Output filtering**: Don't expose sensitive data

---

## 📈 Scaling for Production

### For 10-50 users:
- Single Databricks App instance
- Standard compute tier
- Basic monitoring

### For 50-200 users:
- Multiple App instances with load balancer
- Dedicated compute cluster
- Advanced monitoring + alerting
- Caching layer (Redis)

### For 200+ users:
- Kubernetes deployment
- Auto-scaling compute
- Separate inference endpoints for each model
- CDN for static assets
- Multi-region deployment

---

## 🎓 Training Your Users

**For Executives**:
1. Introduction video (5 min)
2. Example questions cheat sheet
3. Simulation studio walkthrough
4. Best practices guide

**For Admins**:
1. System architecture overview
2. Monitoring dashboard tour
3. Troubleshooting guide
4. Maintenance procedures

---

## 📞 Support & Maintenance

**Daily**:
- Check error logs
- Review usage metrics
- Monitor response times

**Weekly**:
- Review and clear cache
- Update knowledge base documents
- Analyze popular queries

**Monthly**:
- Genie space optimization
- Vector index rebuild
- Security audit
- User feedback review

---

**You're now ready for production!** 🚀

Next: [Create monitoring alerts](monitoring.md) | [User training materials](training.md)
