# Databricks notebook source
# MAGIC %md
# MAGIC # Setup Vector Search for DecisionMakingArena
# MAGIC
# MAGIC This notebook sets up Mosaic AI Vector Search for RAG context enrichment.
# MAGIC
# MAGIC **Steps**:
# MAGIC 1. Create Vector Search endpoint
# MAGIC 2. Create knowledge base table
# MAGIC 3. Load business context documents
# MAGIC 4. Create vector index
# MAGIC 5. Test search functionality

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Install Dependencies

# COMMAND ----------

# MAGIC %pip install databricks-vectorsearch
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Configuration

# COMMAND ----------

from databricks.vector_search.client import VectorSearchClient
from databricks.sdk import WorkspaceClient

# Configuration
CATALOG_NAME = "decision_making_prod"
SCHEMA_NAME = "business_data"
ENDPOINT_NAME = "decision_making_vs_endpoint"
INDEX_NAME = f"{CATALOG_NAME}.{SCHEMA_NAME}.knowledge_base_index"
TABLE_NAME = f"{CATALOG_NAME}.{SCHEMA_NAME}.knowledge_base"

print(f"Endpoint: {ENDPOINT_NAME}")
print(f"Index: {INDEX_NAME}")
print(f"Table: {TABLE_NAME}")

# COMMAND ----------

# Initialize clients
w = WorkspaceClient()
vsc = VectorSearchClient(workspace_url=w.config.host)

print("✅ Clients initialized")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Create Vector Search Endpoint

# COMMAND ----------

# Check if endpoint exists
try:
    endpoint = vsc.get_endpoint(ENDPOINT_NAME)
    print(f"✅ Endpoint '{ENDPOINT_NAME}' already exists")
    print(f"   Status: {endpoint.endpoint_status.state}")
except Exception as e:
    # Create endpoint
    print(f"Creating endpoint '{ENDPOINT_NAME}'...")
    vsc.create_endpoint(
        name=ENDPOINT_NAME,
        endpoint_type="STANDARD"
    )
    print("✅ Endpoint created (will take 5-10 minutes to be ready)")
    print("   Run this cell again to check status")

# COMMAND ----------

# Wait for endpoint to be ready
import time

max_wait = 600  # 10 minutes
wait_time = 0
check_interval = 30

while wait_time < max_wait:
    try:
        endpoint = vsc.get_endpoint(ENDPOINT_NAME)
        status = endpoint.endpoint_status.state

        if status == "ONLINE":
            print(f"✅ Endpoint is ONLINE and ready!")
            break
        else:
            print(f"⏳ Endpoint status: {status} - waiting {check_interval}s...")
            time.sleep(check_interval)
            wait_time += check_interval
    except Exception as e:
        print(f"❌ Error checking endpoint: {e}")
        break

if wait_time >= max_wait:
    print("⚠️  Endpoint not ready after 10 minutes. Check Databricks UI.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Create Knowledge Base Table

# COMMAND ----------

# MAGIC %sql
# MAGIC USE CATALOG decision_making_prod;
# MAGIC USE SCHEMA business_data;
# MAGIC
# MAGIC -- Drop if exists (for clean setup)
# MAGIC DROP TABLE IF EXISTS knowledge_base;
# MAGIC
# MAGIC -- Create knowledge base table
# MAGIC CREATE TABLE knowledge_base (
# MAGIC     id STRING NOT NULL,
# MAGIC     content STRING NOT NULL COMMENT 'Document content to be embedded',
# MAGIC     category STRING COMMENT 'Document category',
# MAGIC     source STRING COMMENT 'Document source',
# MAGIC     date DATE COMMENT 'Relevant date',
# MAGIC     metadata STRING COMMENT 'Additional metadata as JSON',
# MAGIC     PRIMARY KEY(id)
# MAGIC )
# MAGIC USING DELTA
# MAGIC COMMENT 'Knowledge base for RAG context enrichment';

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Load Business Context Documents

# COMMAND ----------

from pyspark.sql.types import *
import json

# Sample business context documents
documents = [
    # Historical Context
    {
        "id": "hist_001",
        "content": "Q3 has historically shown 15-20% YoY growth due to holiday season preparation. Key drivers include retail inventory buildup and promotional campaigns. This trend has been consistent for the past 5 years.",
        "category": "historical_context",
        "source": "annual_reports",
        "date": "2024-01-01",
        "metadata": json.dumps({"period": "Q3", "years": "2019-2023"})
    },
    {
        "id": "hist_002",
        "content": "Previous store openings have shown average payback periods of 18-24 months with 25-30% ROI. Initial ramp-up typically takes 6 months to reach 80% of projected revenue.",
        "category": "historical_analysis",
        "source": "store_expansion_reports",
        "date": "2023-12-01",
        "metadata": json.dumps({"topic": "store_expansion"})
    },
    {
        "id": "hist_003",
        "content": "Company's historical gross margin has ranged from 35-40% with net margin around 12-15%. Best performing quarters show margins at the higher end of these ranges.",
        "category": "financial_context",
        "source": "financial_statements",
        "date": "2024-01-01",
        "metadata": json.dumps({"metric": "margins"})
    },

    # Industry Benchmarks
    {
        "id": "bench_001",
        "content": "Industry benchmark for retail net margin: B2B segment 12-15%, B2C segment 18-22%. Top quartile performers achieve 15%+ for B2B and 25%+ for B2C.",
        "category": "benchmark",
        "source": "industry_reports",
        "date": "2024-01-01",
        "metadata": json.dumps({"industry": "retail", "metric": "net_margin"})
    },
    {
        "id": "bench_002",
        "content": "Average revenue per retail store in similar markets: $800K-$1.2M annually. Top performers achieve $1.5M+. Operating costs typically 60-70% of revenue.",
        "category": "benchmark",
        "source": "market_research",
        "date": "2024-01-01",
        "metadata": json.dumps({"metric": "revenue_per_store"})
    },
    {
        "id": "bench_003",
        "content": "Industry average customer acquisition cost (CAC) is $80-$120. Customer lifetime value (LTV) averages $800-$1200. Target LTV:CAC ratio should be 3:1 minimum.",
        "category": "benchmark",
        "source": "marketing_research",
        "date": "2024-01-01",
        "metadata": json.dumps({"metric": "customer_metrics"})
    },

    # Best Practices
    {
        "id": "bp_001",
        "content": "Best practice for ROI analysis: Use discounted cash flow with 10% discount rate for retail investments. Include sensitivity analysis for key variables (revenue ±20%, costs ±15%).",
        "category": "best_practice",
        "source": "finance_playbook",
        "date": "2024-01-01",
        "metadata": json.dumps({"topic": "roi_analysis"})
    },
    {
        "id": "bp_002",
        "content": "New product launch best practices: Test in 2-3 pilot markets first. Measure success after 90 days. Key metrics: market penetration, customer feedback, margin achievement.",
        "category": "best_practice",
        "source": "product_playbook",
        "date": "2024-01-01",
        "metadata": json.dumps({"topic": "product_launch"})
    },
    {
        "id": "bp_003",
        "content": "Strategic planning framework: Use Porter's Five Forces for competitive analysis, SWOT for internal assessment, and scenario planning for uncertainty. Review quarterly.",
        "category": "best_practice",
        "source": "strategy_playbook",
        "date": "2024-01-01",
        "metadata": json.dumps({"topic": "strategic_planning"})
    },

    # Business Context
    {
        "id": "ctx_001",
        "content": "Company strategic focus areas: Premium segment expansion, digital channel integration, customer experience enhancement. Key initiatives include omnichannel strategy and personalization.",
        "category": "strategic_context",
        "source": "strategic_plan",
        "date": "2024-01-01",
        "metadata": json.dumps({"year": "2024"})
    },
    {
        "id": "ctx_002",
        "content": "Competitive landscape: Main competitors are Company A (30% market share), Company B (25%), us (20%). Differentiation through premium quality and customer service.",
        "category": "competitive_context",
        "source": "market_analysis",
        "date": "2024-01-01",
        "metadata": json.dumps({"topic": "competition"})
    },
    {
        "id": "ctx_003",
        "content": "Key Performance Indicators (KPIs) definitions: Revenue Growth (YoY %), Gross Margin %, Net Margin %, EBITDA, Customer Acquisition Cost, Lifetime Value, NPS.",
        "category": "definitions",
        "source": "kpi_glossary",
        "date": "2024-01-01",
        "metadata": json.dumps({"topic": "kpi_definitions"})
    },

    # Market Trends
    {
        "id": "trend_001",
        "content": "2024 retail trends: Shift to experiential retail, sustainability focus, AI-powered personalization, omnichannel integration. Consumer spending cautious but stable.",
        "category": "market_trends",
        "source": "trend_reports",
        "date": "2024-01-01",
        "metadata": json.dumps({"year": "2024"})
    },
    {
        "id": "trend_002",
        "content": "Economic outlook: GDP growth projected 2-3%, inflation moderating to 2-2.5%, consumer confidence recovering. Retail sector expected to grow 4-6% annually.",
        "category": "economic_context",
        "source": "economic_reports",
        "date": "2024-01-01",
        "metadata": json.dumps({"year": "2024"})
    },

    # Risk Factors
    {
        "id": "risk_001",
        "content": "Key business risks: Supply chain disruptions, competitive pressure, economic downturn, technology disruption. Mitigation strategies include supplier diversification and digital investment.",
        "category": "risk_analysis",
        "source": "risk_assessment",
        "date": "2024-01-01",
        "metadata": json.dumps({"topic": "business_risks"})
    },
]

# Create DataFrame
schema = StructType([
    StructField("id", StringType(), False),
    StructField("content", StringType(), False),
    StructField("category", StringType()),
    StructField("source", StringType()),
    StructField("date", DateType()),
    StructField("metadata", StringType())
])

docs_df = spark.createDataFrame(documents, schema)

# Write to table
docs_df.write.mode("overwrite").saveAsTable(TABLE_NAME)

print(f"✅ Loaded {docs_df.count()} documents into knowledge base")

# COMMAND ----------

# Verify data
display(spark.table(TABLE_NAME))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6. Create Vector Search Index

# COMMAND ----------

# Create index
try:
    print(f"Creating vector index on '{TABLE_NAME}'...")

    index = vsc.create_delta_sync_index(
        endpoint_name=ENDPOINT_NAME,
        source_table_name=TABLE_NAME,
        index_name=INDEX_NAME,
        pipeline_type="TRIGGERED",
        primary_key="id",
        embedding_source_column="content",
        embedding_model_endpoint_name="databricks-bge-large-en"
    )

    print(f"✅ Index created: {INDEX_NAME}")
    print("   Indexing will start automatically...")

except Exception as e:
    if "already exists" in str(e):
        print(f"⚠️  Index already exists: {INDEX_NAME}")
    else:
        print(f"❌ Error creating index: {e}")
        raise

# COMMAND ----------

# MAGIC %md
# MAGIC ## 7. Wait for Index Sync

# COMMAND ----------

import time

print("Waiting for index to sync...")
max_wait = 600  # 10 minutes
wait_time = 0
check_interval = 20

while wait_time < max_wait:
    try:
        index = vsc.get_index(
            endpoint_name=ENDPOINT_NAME,
            index_name=INDEX_NAME
        )

        status = index.status.state

        if status == "ONLINE":
            print(f"✅ Index is ONLINE and ready!")
            print(f"   Indexed rows: {index.status.indexed_row_count}")
            break
        else:
            print(f"⏳ Index status: {status} - waiting {check_interval}s...")
            time.sleep(check_interval)
            wait_time += check_interval

    except Exception as e:
        print(f"⏳ Index not ready yet: {str(e)[:100]}")
        time.sleep(check_interval)
        wait_time += check_interval

if wait_time >= max_wait:
    print("⚠️  Index not ready after 10 minutes. Check status in Databricks UI.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 8. Test Vector Search

# COMMAND ----------

# Test search with a sample query
test_query = "What is our historical performance in Q3?"

print(f"Testing search with query: '{test_query}'")
print("-" * 60)

try:
    results = vsc.get_index(
        endpoint_name=ENDPOINT_NAME,
        index_name=INDEX_NAME
    ).similarity_search(
        query_text=test_query,
        columns=["id", "content", "category", "source"],
        num_results=3
    )

    print(f"✅ Found {len(results['result']['data_array'])} relevant documents:\n")

    for i, result in enumerate(results['result']['data_array'], 1):
        print(f"{i}. ID: {result[0]}")
        print(f"   Category: {result[2]}")
        print(f"   Content: {result[1][:150]}...")
        print(f"   Score: {result[-1] if len(result) > 4 else 'N/A'}")
        print()

except Exception as e:
    print(f"❌ Error testing search: {e}")

# COMMAND ----------

# Test with different queries
test_queries = [
    "industry benchmarks for retail margins",
    "best practices for ROI analysis",
    "competitive landscape information",
    "risk factors for new store openings"
]

print("Testing multiple queries:")
print("=" * 60)

for query in test_queries:
    print(f"\n🔍 Query: '{query}'")
    print("-" * 60)

    try:
        results = vsc.get_index(
            endpoint_name=ENDPOINT_NAME,
            index_name=INDEX_NAME
        ).similarity_search(
            query_text=query,
            columns=["id", "category", "content"],
            num_results=2
        )

        if results and 'result' in results and 'data_array' in results['result']:
            for result in results['result']['data_array']:
                print(f"  ✓ {result[1]}: {result[2][:100]}...")
        else:
            print("  ℹ️  No results found")

    except Exception as e:
        print(f"  ❌ Error: {str(e)[:100]}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 9. Grant Permissions

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Grant access to knowledge base
# MAGIC GRANT SELECT ON TABLE decision_making_prod.business_data.knowledge_base
# MAGIC TO GROUP executives;
# MAGIC
# MAGIC -- Grant usage on catalog/schema
# MAGIC GRANT USAGE ON CATALOG decision_making_prod TO GROUP executives;
# MAGIC GRANT USAGE ON SCHEMA decision_making_prod.business_data TO GROUP executives;

# COMMAND ----------

# MAGIC %md
# MAGIC ## 10. Update Application Configuration

# COMMAND ----------

print("=" * 60)
print("✅ VECTOR SEARCH SETUP COMPLETE!")
print("=" * 60)
print(f"\nEndpoint: {ENDPOINT_NAME}")
print(f"Index: {INDEX_NAME}")
print(f"Documents indexed: {len(documents)}")
print("\n📝 Update your .env file with:")
print(f"   VECTOR_SEARCH_ENDPOINT_NAME={ENDPOINT_NAME}")
print(f"   VECTOR_SEARCH_INDEX_NAME={INDEX_NAME}")
print("\n📋 Next: Run notebook '03_deploy_uc_functions.py'")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 📚 Adding More Documents
# MAGIC
# MAGIC To add more documents to your knowledge base:
# MAGIC
# MAGIC ```python
# MAGIC # Create new documents
# MAGIC new_docs = [
# MAGIC     {
# MAGIC         "id": "new_001",
# MAGIC         "content": "Your business context here...",
# MAGIC         "category": "category_name",
# MAGIC         "source": "source_name",
# MAGIC         "date": "2024-01-01",
# MAGIC         "metadata": json.dumps({"key": "value"})
# MAGIC     }
# MAGIC ]
# MAGIC
# MAGIC # Append to table
# MAGIC new_df = spark.createDataFrame(new_docs, schema)
# MAGIC new_df.write.mode("append").saveAsTable(TABLE_NAME)
# MAGIC
# MAGIC # Trigger index sync
# MAGIC vsc.get_index(ENDPOINT_NAME, INDEX_NAME).sync()
# MAGIC ```
