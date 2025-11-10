-- Databricks notebook source
-- MAGIC %md
-- MAGIC # Deploy Unity Catalog Functions for DecisionMakingArena
-- MAGIC
-- MAGIC This notebook deploys the business logic functions to Unity Catalog.
-- MAGIC
-- MAGIC **Functions**:
-- MAGIC 1. `calculate_roi_stores` - ROI calculation for new stores
-- MAGIC 2. `forecast_revenue_simple` - Simple revenue forecasting
-- MAGIC 3. `calculate_metrics` - Calculate key business metrics
-- MAGIC
-- MAGIC **Prerequisites**: Tables created in notebook 01

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 1. Setup Schema

-- COMMAND ----------

-- Create catalog if not exists
CREATE CATALOG IF NOT EXISTS decision_making_prod;

-- Use catalog
USE CATALOG decision_making_prod;

-- Create schema for functions
CREATE SCHEMA IF NOT EXISTS analytics_functions
COMMENT 'Business logic functions for DecisionMakingArena';

-- Use schema
USE SCHEMA analytics_functions;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 2. Deploy ROI Calculation Function

-- COMMAND ----------

-- Drop if exists (for redeployment)
DROP FUNCTION IF EXISTS calculate_roi_stores;

-- Create function
CREATE OR REPLACE FUNCTION calculate_roi_stores(
    num_stores INT COMMENT 'Number of new stores',
    investment_per_store DOUBLE COMMENT 'Investment per store in USD',
    avg_revenue_per_store DOUBLE COMMENT 'Expected annual revenue per store',
    cost_ratio DOUBLE COMMENT 'Operating cost ratio (0-1)',
    forecast_months INT COMMENT 'Forecast period in months'
)
RETURNS STRUCT<
    roi_percentage DOUBLE COMMENT 'ROI percentage',
    payback_months INT COMMENT 'Payback period in months',
    break_even_month INT COMMENT 'Break-even month',
    total_profit DOUBLE COMMENT 'Total profit over forecast period',
    npv DOUBLE COMMENT 'Net Present Value',
    monthly_revenue ARRAY<DOUBLE> COMMENT 'Monthly revenue projections'
>
LANGUAGE PYTHON
COMMENT 'Calculate ROI for new store openings with ramp-up curve'
AS $$
import numpy as np

# Calculate monthly revenue at full capacity
monthly_revenue_full = avg_revenue_per_store / 12

# Total investment
total_investment = num_stores * investment_per_store

# Initialize tracking
cumulative = -total_investment
monthly_cf = []
monthly_revenue_list = []
payback_month = None
break_even_month = None

# S-curve ramp-up (6 months to reach 80% capacity)
def ramp_up_factor(month):
    if month > 6:
        return 1.0
    return 1 / (1 + np.exp(-2 * (month/6 - 0.5)))

# Calculate for each month
for month in range(1, forecast_months + 1):
    # Apply ramp-up
    ramp = ramp_up_factor(month)

    # Monthly revenue for all stores
    monthly_rev = num_stores * monthly_revenue_full * ramp
    monthly_revenue_list.append(float(monthly_rev))

    # Operating costs
    monthly_costs = monthly_rev * cost_ratio

    # Net cash flow
    net_cf = monthly_rev - monthly_costs
    monthly_cf.append(net_cf)

    # Update cumulative
    cumulative += net_cf

    # Track break-even
    if break_even_month is None and cumulative >= 0:
        break_even_month = month

    # Track payback
    if payback_month is None and cumulative >= 0:
        payback_month = month

# Calculate ROI
total_profit = sum(monthly_cf)
roi = (total_profit / total_investment) * 100

# Calculate NPV (10% annual discount rate)
monthly_rate = 0.10 / 12
npv = -total_investment
for i, cf in enumerate(monthly_cf, 1):
    npv += cf / ((1 + monthly_rate) ** i)

return {
    'roi_percentage': round(roi, 2),
    'payback_months': payback_month if payback_month else forecast_months,
    'break_even_month': break_even_month if break_even_month else forecast_months,
    'total_profit': round(total_profit, 2),
    'npv': round(npv, 2),
    'monthly_revenue': [round(r, 2) for r in monthly_revenue_list]
}
$$;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 3. Test ROI Function

-- COMMAND ----------

-- Test with sample data
SELECT calculate_roi_stores(
    5,           -- 5 stores
    400000.0,    -- $400K investment each
    800000.0,    -- $800K annual revenue each
    0.65,        -- 65% cost ratio
    18           -- 18 month forecast
) AS roi_result;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 4. Deploy Revenue Forecasting Function

-- COMMAND ----------

DROP FUNCTION IF EXISTS forecast_revenue_simple;

CREATE OR REPLACE FUNCTION forecast_revenue_simple(
    historical_values ARRAY<DOUBLE> COMMENT 'Historical revenue values',
    forecast_periods INT COMMENT 'Number of periods to forecast',
    growth_rate DOUBLE COMMENT 'Expected growth rate (optional, -1 to auto-calculate)'
)
RETURNS STRUCT<
    forecast ARRAY<DOUBLE> COMMENT 'Forecasted values',
    growth_rate_used DOUBLE COMMENT 'Growth rate used for forecast',
    trend STRING COMMENT 'Trend direction: increasing, decreasing, stable'
>
LANGUAGE PYTHON
COMMENT 'Simple revenue forecasting with linear growth'
AS $$
import numpy as np

# Convert to numpy array
hist = np.array(historical_values)

if len(hist) < 2:
    # Not enough data
    return {
        'forecast': [hist[0]] * forecast_periods if len(hist) > 0 else [0] * forecast_periods,
        'growth_rate_used': 0.0,
        'trend': 'insufficient_data'
    }

# Calculate growth rate if not provided
if growth_rate < 0:
    # Calculate average period-over-period growth
    growth_rates = []
    for i in range(1, len(hist)):
        if hist[i-1] > 0:
            rate = (hist[i] - hist[i-1]) / hist[i-1]
            growth_rates.append(rate)
    growth_rate = np.mean(growth_rates) if growth_rates else 0.0

# Determine trend
if growth_rate > 0.02:
    trend = 'increasing'
elif growth_rate < -0.02:
    trend = 'decreasing'
else:
    trend = 'stable'

# Generate forecast
last_value = hist[-1]
forecast = []
for period in range(1, forecast_periods + 1):
    forecasted = last_value * ((1 + growth_rate) ** period)
    forecast.append(round(float(forecasted), 2))

return {
    'forecast': forecast,
    'growth_rate_used': round(float(growth_rate), 4),
    'trend': trend
}
$$;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 5. Test Forecasting Function

-- COMMAND ----------

-- Test with sample historical data
SELECT forecast_revenue_simple(
    ARRAY(100000.0, 105000.0, 110000.0, 115000.0, 120000.0),  -- Historical
    6,        -- Forecast 6 periods
    -1.0      -- Auto-calculate growth rate
) AS forecast_result;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 6. Deploy Metrics Calculation Function

-- COMMAND ----------

DROP FUNCTION IF EXISTS calculate_business_metrics;

CREATE OR REPLACE FUNCTION calculate_business_metrics(
    revenue DOUBLE,
    cost DOUBLE,
    investment DOUBLE
)
RETURNS STRUCT<
    gross_profit DOUBLE,
    gross_margin_pct DOUBLE,
    net_profit DOUBLE,
    net_margin_pct DOUBLE,
    roi_pct DOUBLE
>
LANGUAGE SQL
COMMENT 'Calculate key business metrics'
AS $$
    SELECT
        revenue - cost AS gross_profit,
        CASE WHEN revenue > 0 THEN ((revenue - cost) / revenue) * 100 ELSE 0 END AS gross_margin_pct,
        revenue - cost - investment AS net_profit,
        CASE WHEN revenue > 0 THEN ((revenue - cost - investment) / revenue) * 100 ELSE 0 END AS net_margin_pct,
        CASE WHEN investment > 0 THEN ((revenue - cost - investment) / investment) * 100 ELSE 0 END AS roi_pct
$$;

-- COMMAND ----------

-- Test metrics function
SELECT calculate_business_metrics(
    1000000.0,  -- $1M revenue
    650000.0,   -- $650K cost
    200000.0    -- $200K investment
) AS metrics;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 7. Create Helper View for Sales Analysis

-- COMMAND ----------

USE CATALOG decision_making_prod;
USE SCHEMA business_data;

-- Create view for easy sales querying
CREATE OR REPLACE VIEW sales_summary AS
SELECT
    DATE_TRUNC('month', date) as month,
    product_name,
    category,
    region,
    SUM(units_sold) as total_units,
    SUM(revenue) as total_revenue,
    SUM(cost) as total_cost,
    SUM(revenue - cost) as gross_profit,
    AVG(profit_margin) as avg_margin
FROM sales_data
GROUP BY 1, 2, 3, 4;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 8. Grant Permissions

-- COMMAND ----------

USE CATALOG decision_making_prod;

-- Grant execute permission on functions
GRANT EXECUTE ON FUNCTION analytics_functions.calculate_roi_stores TO GROUP executives;
GRANT EXECUTE ON FUNCTION analytics_functions.forecast_revenue_simple TO GROUP executives;
GRANT EXECUTE ON FUNCTION analytics_functions.calculate_business_metrics TO GROUP executives;

-- Grant select on views
GRANT SELECT ON VIEW business_data.sales_summary TO GROUP executives;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## 9. Verify Deployment

-- COMMAND ----------

-- List all functions in schema
SHOW FUNCTIONS IN decision_making_prod.analytics_functions;

-- COMMAND ----------

-- Show function details
DESCRIBE FUNCTION EXTENDED decision_making_prod.analytics_functions.calculate_roi_stores;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## ✅ Deployment Complete!
-- MAGIC
-- MAGIC **Functions Deployed**:
-- MAGIC - ✅ `calculate_roi_stores` - ROI calculations with ramp-up
-- MAGIC - ✅ `forecast_revenue_simple` - Revenue forecasting
-- MAGIC - ✅ `calculate_business_metrics` - Key metrics calculation
-- MAGIC
-- MAGIC **Next Steps**:
-- MAGIC 1. Update `.env` with correct catalog/schema names
-- MAGIC 2. Test functions from Python application
-- MAGIC 3. Deploy Gradio application

-- COMMAND ----------

-- MAGIC %python
-- MAGIC print("=" * 60)
-- MAGIC print("✅ UNITY CATALOG FUNCTIONS DEPLOYED!")
-- MAGIC print("=" * 60)
-- MAGIC print("\nCatalog: decision_making_prod")
-- MAGIC print("Schema: analytics_functions")
-- MAGIC print("\nFunctions available:")
-- MAGIC print("  ✓ calculate_roi_stores")
-- MAGIC print("  ✓ forecast_revenue_simple")
-- MAGIC print("  ✓ calculate_business_metrics")
-- MAGIC print("\n📋 Next: Deploy the Gradio application")
-- MAGIC print("     Run: python src/ui/app.py")
