-- ============================================================
-- BioLabs Unity Catalog Setup
-- ============================================================
-- This script creates the complete Unity Catalog structure
-- for the BioLabs Multi-Agent System
--
-- Run this in Databricks SQL Editor or via CLI
-- ============================================================

-- ============================================================
-- CATALOG CREATION
-- ============================================================

-- Create main catalog (if not exists)
CREATE CATALOG IF NOT EXISTS biolabs_catalog
COMMENT 'BioLabs business data catalog for multi-agent system';

USE CATALOG biolabs_catalog;

-- ============================================================
-- SCHEMA CREATION
-- ============================================================

-- Operations Schema
CREATE SCHEMA IF NOT EXISTS operations
COMMENT 'Operations data: sales, inventory, POS, distribution';

-- Marketing Schema
CREATE SCHEMA IF NOT EXISTS marketing
COMMENT 'Marketing data: campaigns, segments, competitor intel';

-- Finance Schema
CREATE SCHEMA IF NOT EXISTS finance
COMMENT 'Finance data: costs, revenue, margins, budgets';

-- Scientific Schema
CREATE SCHEMA IF NOT EXISTS scientific
COMMENT 'Scientific knowledge base: papers, clinical trials, regulations';

-- ============================================================
-- OPERATIONS SCHEMA TABLES
-- ============================================================

USE SCHEMA operations;

-- Sales Transactions Table
CREATE TABLE IF NOT EXISTS sales_transactions (
  transaction_id STRING NOT NULL,
  date DATE NOT NULL,
  product_name STRING NOT NULL,
  pos_id STRING NOT NULL,
  pos_name STRING NOT NULL,
  pos_type STRING NOT NULL,
  units_sold DECIMAL(10,2) NOT NULL,
  revenue DECIMAL(10,2) NOT NULL,
  cost DECIMAL(10,2) NOT NULL,
  region STRING NOT NULL,
  CONSTRAINT pk_transactions PRIMARY KEY (transaction_id)
)
USING DELTA
COMMENT 'Sales transactions from all POS locations'
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true'
);

-- Inventory Levels Table
CREATE TABLE IF NOT EXISTS inventory_levels (
  snapshot_date DATE NOT NULL,
  product_name STRING NOT NULL,
  location STRING NOT NULL,
  current_stock_kg DECIMAL(10,2) NOT NULL,
  reserved_stock_kg DECIMAL(10,2) NOT NULL,
  available_stock_kg DECIMAL(10,2) NOT NULL,
  daily_sales_30d_avg DECIMAL(8,2) NOT NULL,
  days_on_hand INT NOT NULL,
  CONSTRAINT pk_inventory PRIMARY KEY (snapshot_date, product_name, location)
)
USING DELTA
COMMENT 'Daily inventory snapshots by product and location'
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true'
);

-- POS Master Table
CREATE TABLE IF NOT EXISTS pos_master (
  pos_id STRING NOT NULL,
  pos_name STRING NOT NULL,
  pos_type STRING NOT NULL,
  region STRING NOT NULL,
  city STRING NOT NULL,
  address STRING,
  active_since DATE NOT NULL,
  account_manager STRING,
  CONSTRAINT pk_pos PRIMARY KEY (pos_id)
)
USING DELTA
COMMENT 'Master data for Point of Sale locations';

-- Distribution Routes Table
CREATE TABLE IF NOT EXISTS distribution_routes (
  route_id STRING NOT NULL,
  route_name STRING NOT NULL,
  region STRING NOT NULL,
  pos_ids ARRAY<STRING>,
  frequency STRING NOT NULL,
  lead_time_days INT NOT NULL,
  CONSTRAINT pk_routes PRIMARY KEY (route_id)
)
USING DELTA
COMMENT 'Distribution routes and logistics information';

-- Production Batches Table
CREATE TABLE IF NOT EXISTS production_batches (
  batch_id STRING NOT NULL,
  product_name STRING NOT NULL,
  production_date DATE NOT NULL,
  quantity_kg DECIMAL(10,2) NOT NULL,
  expiry_date DATE NOT NULL,
  status STRING NOT NULL,
  quality_score DECIMAL(3,2),
  CONSTRAINT pk_batches PRIMARY KEY (batch_id)
)
USING DELTA
COMMENT 'Production batch tracking information';

-- ============================================================
-- MARKETING SCHEMA TABLES
-- ============================================================

USE SCHEMA marketing;

-- Campaigns Table
CREATE TABLE IF NOT EXISTS campaigns (
  campaign_id STRING NOT NULL,
  campaign_name STRING NOT NULL,
  product STRING NOT NULL,
  channel STRING NOT NULL,
  target_segment STRING NOT NULL,
  start_date DATE NOT NULL,
  end_date DATE NOT NULL,
  budget DECIMAL(10,2) NOT NULL,
  impressions INT,
  clicks INT,
  conversions INT,
  revenue_attributed DECIMAL(10,2),
  CONSTRAINT pk_campaigns PRIMARY KEY (campaign_id)
)
USING DELTA
COMMENT 'Marketing campaign performance data'
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true'
);

-- Customer Segments Table
CREATE TABLE IF NOT EXISTS customer_segments (
  segment STRING NOT NULL,
  size INT NOT NULL,
  avg_ltv DECIMAL(8,2) NOT NULL,
  avg_order_value DECIMAL(8,2) NOT NULL,
  purchase_frequency DECIMAL(4,2) NOT NULL,
  retention_rate DECIMAL(3,2) NOT NULL,
  primary_product STRING NOT NULL,
  characteristics STRING,
  CONSTRAINT pk_segments PRIMARY KEY (segment)
)
USING DELTA
COMMENT 'Customer segmentation and behavior data';

-- Competitor Intelligence Table
CREATE TABLE IF NOT EXISTS competitor_intel (
  competitor STRING NOT NULL,
  product_category STRING NOT NULL,
  price_per_kg DECIMAL(6,2) NOT NULL,
  market_share_pct DECIMAL(4,2) NOT NULL,
  last_updated DATE NOT NULL,
  strengths STRING,
  weaknesses STRING,
  CONSTRAINT pk_competitors PRIMARY KEY (competitor)
)
USING DELTA
COMMENT 'Competitive landscape intelligence';

-- Channel Performance Table
CREATE TABLE IF NOT EXISTS channel_performance (
  month DATE NOT NULL,
  channel STRING NOT NULL,
  product STRING NOT NULL,
  sales_volume_kg DECIMAL(10,2),
  revenue DECIMAL(12,2),
  cac DECIMAL(8,2),
  conversion_rate DECIMAL(4,2),
  CONSTRAINT pk_channel_perf PRIMARY KEY (month, channel, product)
)
USING DELTA
COMMENT 'Channel-level performance metrics';

-- ============================================================
-- FINANCE SCHEMA TABLES
-- ============================================================

USE SCHEMA finance;

-- Product Costs Table
CREATE TABLE IF NOT EXISTS product_costs (
  product_name STRING NOT NULL,
  cogs_per_kg DECIMAL(6,2) NOT NULL,
  packaging_cost_per_unit DECIMAL(3,2) NOT NULL,
  distribution_cost_per_kg DECIMAL(2,2) NOT NULL,
  total_variable_cost DECIMAL(6,2) NOT NULL,
  last_updated DATE NOT NULL,
  CONSTRAINT pk_product_costs PRIMARY KEY (product_name)
)
USING DELTA
COMMENT 'Product cost structure and COGS';

-- Revenue by Channel Table
CREATE TABLE IF NOT EXISTS revenue_by_channel (
  month DATE NOT NULL,
  product_name STRING NOT NULL,
  channel STRING NOT NULL,
  revenue DECIMAL(12,2) NOT NULL,
  cost DECIMAL(12,2) NOT NULL,
  gross_profit DECIMAL(12,2) NOT NULL,
  gross_margin_pct DECIMAL(4,2) NOT NULL,
  CONSTRAINT pk_revenue PRIMARY KEY (month, product_name, channel)
)
USING DELTA
COMMENT 'Monthly revenue and margins by channel'
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true'
);

-- Budgets Table
CREATE TABLE IF NOT EXISTS budgets (
  budget_id STRING NOT NULL,
  fiscal_year INT NOT NULL,
  quarter INT NOT NULL,
  department STRING NOT NULL,
  category STRING NOT NULL,
  budget_amount DECIMAL(12,2) NOT NULL,
  actual_spend DECIMAL(12,2),
  variance DECIMAL(12,2),
  CONSTRAINT pk_budgets PRIMARY KEY (budget_id)
)
USING DELTA
COMMENT 'Budget planning and tracking';

-- Margin Analysis Table
CREATE TABLE IF NOT EXISTS margin_analysis (
  analysis_date DATE NOT NULL,
  product_name STRING NOT NULL,
  channel STRING NOT NULL,
  gross_margin_pct DECIMAL(4,2),
  contribution_margin_pct DECIMAL(4,2),
  ebitda_margin_pct DECIMAL(4,2),
  CONSTRAINT pk_margin_analysis PRIMARY KEY (analysis_date, product_name, channel)
)
USING DELTA
COMMENT 'Detailed margin analysis by product and channel';

-- ============================================================
-- SCIENTIFIC SCHEMA TABLES
-- ============================================================

USE SCHEMA scientific;

-- Scientific Documents Table (for RAG)
CREATE TABLE IF NOT EXISTS documents (
  doc_id STRING NOT NULL,
  document_type STRING NOT NULL,
  product STRING NOT NULL,
  title STRING NOT NULL,
  authors STRING,
  publication_date DATE,
  journal STRING,

  -- Processed content
  text_content STRING,
  image_descriptions ARRAY<STRING>,
  formulas ARRAY<STRING>,
  combined_content STRING,

  -- Metadata for retrieval
  study_type STRING,
  sample_size INT,
  p_value DOUBLE,
  key_findings ARRAY<STRING>,

  -- References
  citations ARRAY<STRING>,
  pdf_path STRING,

  -- Timestamps
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),

  CONSTRAINT pk_documents PRIMARY KEY (doc_id)
)
USING DELTA
COMMENT 'Scientific knowledge base for RAG system'
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true'
);

-- ============================================================
-- SQL FUNCTIONS (for Genie Spaces)
-- ============================================================

USE SCHEMA operations;

-- Function: Calculate Sell-Through Rate
CREATE OR REPLACE FUNCTION calc_sell_through(
  product STRING,
  pos_id STRING,
  days INT
)
RETURNS DOUBLE
COMMENT 'Calculate sell-through rate for a product at a specific POS over N days'
RETURN (
  SELECT
    COALESCE(SUM(units_sold) / NULLIF(SUM(units_sold) + 10, 0), 0)
  FROM sales_transactions
  WHERE product_name = product
    AND pos_id = pos_id
    AND date >= CURRENT_DATE - INTERVAL days DAY
);

-- Function: Calculate Days on Hand
CREATE OR REPLACE FUNCTION calc_days_on_hand(
  product STRING
)
RETURNS INT
COMMENT 'Calculate current days on hand for a product'
RETURN (
  SELECT days_on_hand
  FROM inventory_levels
  WHERE product_name = product
    AND snapshot_date = (SELECT MAX(snapshot_date) FROM inventory_levels)
  LIMIT 1
);

USE SCHEMA marketing;

-- Function: Calculate CAC (Customer Acquisition Cost)
CREATE OR REPLACE FUNCTION calc_cac(
  segment STRING,
  start_date DATE,
  end_date DATE
)
RETURNS DECIMAL(10,2)
COMMENT 'Calculate CAC for a segment over a date range'
RETURN (
  SELECT
    COALESCE(SUM(budget) / NULLIF(SUM(conversions), 0), 0)
  FROM campaigns
  WHERE target_segment = segment
    AND start_date >= start_date
    AND end_date <= end_date
);

USE SCHEMA finance;

-- Function: Calculate Gross Margin
CREATE OR REPLACE FUNCTION calc_gross_margin(
  product STRING,
  channel STRING
)
RETURNS DECIMAL(4,2)
COMMENT 'Calculate gross margin % for product-channel combination'
RETURN (
  SELECT
    COALESCE(AVG(gross_margin_pct), 0)
  FROM revenue_by_channel
  WHERE product_name = product
    AND channel = channel
    AND month >= ADD_MONTHS(CURRENT_DATE, -6)
);

-- ============================================================
-- CREATE UNITY CATALOG VOLUMES (for PDF storage)
-- ============================================================

USE SCHEMA scientific;

CREATE VOLUME IF NOT EXISTS raw_pdfs
COMMENT 'Storage for raw scientific PDF files';

CREATE VOLUME IF NOT EXISTS parsed_images
COMMENT 'Storage for extracted images from PDFs';

-- ============================================================
-- GRANTS (optional - adjust based on your security model)
-- ============================================================

-- Grant usage on catalog to all users
-- GRANT USAGE ON CATALOG biolabs_catalog TO `account users`;

-- Grant usage on schemas
-- GRANT USAGE ON SCHEMA operations TO `account users`;
-- GRANT USAGE ON SCHEMA marketing TO `account users`;
-- GRANT USAGE ON SCHEMA finance TO `account users`;
-- GRANT USAGE ON SCHEMA scientific TO `account users`;

-- ============================================================
-- VERIFICATION QUERIES
-- ============================================================

-- Show all schemas
SHOW SCHEMAS IN biolabs_catalog;

-- Show all tables in operations
SHOW TABLES IN operations;

-- Show all tables in marketing
SHOW TABLES IN marketing;

-- Show all tables in finance
SHOW TABLES IN finance;

-- Show all tables in scientific
SHOW TABLES IN scientific;

-- Show all functions
SHOW USER FUNCTIONS IN operations;
SHOW USER FUNCTIONS IN marketing;
SHOW USER FUNCTIONS IN finance;

-- Show volumes
SHOW VOLUMES IN scientific;

-- ============================================================
-- SETUP COMPLETE
-- ============================================================

SELECT '✓ Unity Catalog setup complete!' AS status;
SELECT '✓ Catalog: biolabs_catalog created' AS status;
SELECT '✓ 4 schemas created: operations, marketing, finance, scientific' AS status;
SELECT '✓ 15 tables created across all schemas' AS status;
SELECT '✓ 4 SQL functions created for Genie Spaces' AS status;
SELECT '✓ 2 volumes created for PDF storage' AS status;
