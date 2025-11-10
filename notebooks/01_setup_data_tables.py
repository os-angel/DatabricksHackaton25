# Databricks notebook source
# MAGIC %md
# MAGIC # Setup Data Tables for DecisionMakingArena
# MAGIC
# MAGIC This notebook creates the production data tables for DecisionMakingArena.
# MAGIC
# MAGIC **Steps**:
# MAGIC 1. Create catalog and schema
# MAGIC 2. Create sales, finance, and strategic tables
# MAGIC 3. Load sample data (or your production data)
# MAGIC 4. Verify data quality

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Configuration

# COMMAND ----------

# Configuration
CATALOG_NAME = "decision_making_prod"
SCHEMA_NAME = "business_data"
SAMPLE_DATA_PATH = "dbfs:/FileStore/decision_making_arena/sample_data/"

print(f"Catalog: {CATALOG_NAME}")
print(f"Schema: {SCHEMA_NAME}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Create Catalog and Schema

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Create catalog
# MAGIC CREATE CATALOG IF NOT EXISTS decision_making_prod;
# MAGIC
# MAGIC -- Use catalog
# MAGIC USE CATALOG decision_making_prod;
# MAGIC
# MAGIC -- Create schema
# MAGIC CREATE SCHEMA IF NOT EXISTS business_data;
# MAGIC
# MAGIC -- Use schema
# MAGIC USE SCHEMA business_data;

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Create Sales Table

# COMMAND ----------

# MAGIC %sql
# MAGIC DROP TABLE IF EXISTS sales_data;
# MAGIC
# MAGIC CREATE TABLE sales_data (
# MAGIC     date DATE COMMENT 'Transaction date',
# MAGIC     product_id STRING COMMENT 'Product identifier',
# MAGIC     product_name STRING COMMENT 'Product name',
# MAGIC     category STRING COMMENT 'Product category',
# MAGIC     region STRING COMMENT 'Sales region',
# MAGIC     units_sold INT COMMENT 'Units sold',
# MAGIC     revenue DECIMAL(10,2) COMMENT 'Revenue in USD',
# MAGIC     cost DECIMAL(10,2) COMMENT 'Cost in USD',
# MAGIC     profit_margin DECIMAL(5,4) COMMENT 'Profit margin ratio'
# MAGIC )
# MAGIC USING DELTA
# MAGIC COMMENT 'Sales transaction data'
# MAGIC PARTITIONED BY (date);

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Create Finance Table

# COMMAND ----------

# MAGIC %sql
# MAGIC DROP TABLE IF EXISTS financial_data;
# MAGIC
# MAGIC CREATE TABLE financial_data (
# MAGIC     date DATE COMMENT 'Transaction date',
# MAGIC     account STRING COMMENT 'Account name',
# MAGIC     category STRING COMMENT 'Financial category',
# MAGIC     amount DECIMAL(10,2) COMMENT 'Amount in USD',
# MAGIC     type STRING COMMENT 'Type: revenue, cost, investment'
# MAGIC )
# MAGIC USING DELTA
# MAGIC COMMENT 'Financial transaction data'
# MAGIC PARTITIONED BY (date);

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Create Strategic Metrics Table

# COMMAND ----------

# MAGIC %sql
# MAGIC DROP TABLE IF EXISTS strategic_metrics;
# MAGIC
# MAGIC CREATE TABLE strategic_metrics (
# MAGIC     date DATE COMMENT 'Metric date',
# MAGIC     metric_name STRING COMMENT 'Metric name',
# MAGIC     metric_value DECIMAL(10,2) COMMENT 'Metric value',
# MAGIC     target DECIMAL(10,2) COMMENT 'Target value',
# MAGIC     category STRING COMMENT 'Metric category'
# MAGIC )
# MAGIC USING DELTA
# MAGIC COMMENT 'Strategic business metrics'
# MAGIC PARTITIONED BY (date);

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6. Load Sample Data
# MAGIC
# MAGIC **Option A**: Load from uploaded CSV files
# MAGIC **Option B**: Generate sample data
# MAGIC **Option C**: Copy from existing tables

# COMMAND ----------

# OPTION A: Load from CSV (if you have files uploaded)

# Uncomment if you have CSV files in DBFS:
"""
# Sales data
spark.read.format("csv") \
    .option("header", "true") \
    .option("inferSchema", "true") \
    .load(f"{SAMPLE_DATA_PATH}sales_data.csv") \
    .write.mode("overwrite") \
    .saveAsTable(f"{CATALOG_NAME}.{SCHEMA_NAME}.sales_data")

# Finance data
spark.read.format("csv") \
    .option("header", "true") \
    .option("inferSchema", "true") \
    .load(f"{SAMPLE_DATA_PATH}financial_data.csv") \
    .write.mode("overwrite") \
    .saveAsTable(f"{CATALOG_NAME}.{SCHEMA_NAME}.financial_data")

# Strategic metrics
spark.read.format("csv") \
    .option("header", "true") \
    .option("inferSchema", "true") \
    .load(f"{SAMPLE_DATA_PATH}strategic_metrics.csv") \
    .write.mode("overwrite") \
    .saveAsTable(f"{CATALOG_NAME}.{SCHEMA_NAME}.strategic_metrics")
"""

# COMMAND ----------

# OPTION B: Generate sample data

from pyspark.sql import functions as F
from pyspark.sql.types import *
from datetime import datetime, timedelta
import random

# Generate sales data
def generate_sales_data():
    dates = [datetime.now() - timedelta(days=x) for x in range(365)]
    products = [
        ("P001", "Premium Widget", "Electronics"),
        ("P002", "Standard Widget", "Electronics"),
        ("P003", "Basic Widget", "Home"),
        ("P004", "Deluxe Gadget", "Electronics"),
        ("P005", "Essential Tool", "Tools")
    ]
    regions = ["North", "South", "East", "West"]

    data = []
    for date in dates:
        for product_id, product_name, category in products:
            for region in regions:
                units = random.randint(50, 300)
                unit_price = random.uniform(100, 500)
                revenue = units * unit_price
                cost = revenue * random.uniform(0.6, 0.8)
                margin = (revenue - cost) / revenue

                data.append((
                    date.date(),
                    product_id,
                    product_name,
                    category,
                    region,
                    units,
                    round(revenue, 2),
                    round(cost, 2),
                    round(margin, 4)
                ))

    schema = StructType([
        StructField("date", DateType()),
        StructField("product_id", StringType()),
        StructField("product_name", StringType()),
        StructField("category", StringType()),
        StructField("region", StringType()),
        StructField("units_sold", IntegerType()),
        StructField("revenue", DecimalType(10, 2)),
        StructField("cost", DecimalType(10, 2)),
        StructField("profit_margin", DecimalType(5, 4))
    ])

    df = spark.createDataFrame(data, schema)
    return df

# Generate and save
sales_df = generate_sales_data()
sales_df.write.mode("overwrite").saveAsTable(f"{CATALOG_NAME}.{SCHEMA_NAME}.sales_data")

print(f"✅ Generated {sales_df.count()} sales records")

# COMMAND ----------

# Generate financial data

def generate_financial_data():
    dates = [datetime.now() - timedelta(days=x) for x in range(365)]
    accounts = [
        ("Revenue - Product Sales", "revenue", "revenue"),
        ("Revenue - Services", "revenue", "revenue"),
        ("Cost - COGS", "cost_of_sales", "cost"),
        ("Cost - Marketing", "operating_expense", "cost"),
        ("Cost - R&D", "operating_expense", "cost"),
        ("Investment - CapEx", "capital_expenditure", "investment")
    ]

    data = []
    for date in dates:
        for account, category, type_ in accounts:
            if type_ == "revenue":
                amount = random.uniform(100000, 500000)
            elif type_ == "cost":
                amount = random.uniform(50000, 200000)
            else:  # investment
                amount = random.uniform(10000, 100000) if random.random() > 0.8 else 0

            if amount > 0:
                data.append((
                    date.date(),
                    account,
                    category,
                    round(amount, 2),
                    type_
                ))

    schema = StructType([
        StructField("date", DateType()),
        StructField("account", StringType()),
        StructField("category", StringType()),
        StructField("amount", DecimalType(10, 2)),
        StructField("type", StringType())
    ])

    df = spark.createDataFrame(data, schema)
    return df

# Generate and save
finance_df = generate_financial_data()
finance_df.write.mode("overwrite").saveAsTable(f"{CATALOG_NAME}.{SCHEMA_NAME}.financial_data")

print(f"✅ Generated {finance_df.count()} financial records")

# COMMAND ----------

# Generate strategic metrics data

def generate_strategic_metrics():
    dates = [datetime.now() - timedelta(days=x) for x in range(365)]
    metrics = [
        ("Customer Acquisition Cost", "CAC", 100, 80),
        ("Customer Lifetime Value", "LTV", 800, 1000),
        ("Monthly Recurring Revenue", "MRR", 500000, 600000),
        ("Churn Rate", "Retention", 5, 3),
        ("Net Promoter Score", "NPS", 50, 70)
    ]

    data = []
    for date in dates:
        for metric_name, category, base_value, target in metrics:
            # Add some variance
            value = base_value * random.uniform(0.9, 1.1)

            data.append((
                date.date(),
                metric_name,
                round(value, 2),
                round(target, 2),
                category
            ))

    schema = StructType([
        StructField("date", DateType()),
        StructField("metric_name", StringType()),
        StructField("metric_value", DecimalType(10, 2)),
        StructField("target", DecimalType(10, 2)),
        StructField("category", StringType())
    ])

    df = spark.createDataFrame(data, schema)
    return df

# Generate and save
metrics_df = generate_strategic_metrics()
metrics_df.write.mode("overwrite").saveAsTable(f"{CATALOG_NAME}.{SCHEMA_NAME}.strategic_metrics")

print(f"✅ Generated {metrics_df.count()} strategic metric records")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 7. Verify Data

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Check sales data
# MAGIC SELECT
# MAGIC     COUNT(*) as total_records,
# MAGIC     MIN(date) as earliest_date,
# MAGIC     MAX(date) as latest_date,
# MAGIC     SUM(revenue) as total_revenue
# MAGIC FROM decision_making_prod.business_data.sales_data;

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Check financial data
# MAGIC SELECT
# MAGIC     type,
# MAGIC     COUNT(*) as records,
# MAGIC     SUM(amount) as total_amount
# MAGIC FROM decision_making_prod.business_data.financial_data
# MAGIC GROUP BY type;

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Check strategic metrics
# MAGIC SELECT
# MAGIC     category,
# MAGIC     COUNT(DISTINCT metric_name) as metrics_count
# MAGIC FROM decision_making_prod.business_data.strategic_metrics
# MAGIC GROUP BY category;

# COMMAND ----------

# MAGIC %md
# MAGIC ## 8. Grant Permissions

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Grant access to executives group
# MAGIC GRANT SELECT ON CATALOG decision_making_prod TO GROUP executives;
# MAGIC GRANT SELECT ON SCHEMA decision_making_prod.business_data TO GROUP executives;

# COMMAND ----------

# MAGIC %md
# MAGIC ## ✅ Setup Complete!
# MAGIC
# MAGIC **Next Steps**:
# MAGIC 1. Run notebook `02_setup_genies.py` to create Genie Spaces
# MAGIC 2. Run notebook `03_setup_vector_search.py` to setup RAG
# MAGIC 3. Run notebook `04_deploy_uc_functions.py` to deploy functions

# COMMAND ----------

print("=" * 50)
print("✅ DATA TABLES SETUP COMPLETE!")
print("=" * 50)
print(f"\nCatalog: {CATALOG_NAME}")
print(f"Schema: {SCHEMA_NAME}")
print("\nTables created:")
print("  ✓ sales_data")
print("  ✓ financial_data")
print("  ✓ strategic_metrics")
print("\n📋 Next: Run notebook '02_setup_genies.py'")
