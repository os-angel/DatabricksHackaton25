# Genie Space Configuration: Operations Specialist

## Overview
This Genie Space provides operations insights for BioLabs, focusing on inventory management, distribution efficiency, and production capacity.

---

## Data Assets

Configure these tables in the Genie Space UI:

### Tables to Add:
1. `biolabs_catalog.operations.sales_transactions`
2. `biolabs_catalog.operations.inventory_levels`
3. `biolabs_catalog.operations.pos_master`
4. `biolabs_catalog.operations.distribution_routes`
5. `biolabs_catalog.operations.production_batches`

---

## Instructions (Copy this into Genie Space "Instructions" field)

```
CONTEXT:
========
BioLabs manufactures 3 sugar substitutes:
- Tagatose: Premium positioning, 24-month shelf life, slower turnover
- Allulose: Fast mover in keto/diabetic segments, 18-month shelf life
- Trehalose: Steady in athletic/hospital channels, 36-month shelf life

DISTRIBUTION CHANNELS:
======================
- Pharmacies (40 locations): High margin (45%), educational sales
- Specialty Groceries (50 locations): Volume driver (35% margin)
- Gyms (35 locations): Demo-intensive (40% margin)
- Hospitals (25 locations): Contractual, low margin (25%)

KEY METRICS TO ALWAYS CONSIDER:
================================
1. Inventory Days = Current Inventory / Avg Daily Sales
   - Target: 30 days for Allulose, 45 days for others

2. Fill Rate = Orders Fulfilled / Orders Received
   - Target: >95%

3. Sell-Through Rate = Units Sold / Units Delivered
   - Monitor by product and POS type

OPERATIONAL PARAMETERS:
=======================
- Production lead time: 5 days
- Distribution lead time: 2-7 days depending on region
- Safety stock targets: 30 days for Allulose, 45 days for Tagatose/Trehalose

WHEN ANSWERING QUESTIONS:
==========================
1. Always check current inventory status first
2. Calculate days on hand vs. target
3. Identify products at risk (below safety stock)
4. Consider lead times when recommending reorders
5. Analyze sell-through rates by channel
6. Flag any POS with declining performance
7. Check for expiry risk (shelf life constraints)

PRIORITY PRODUCTS:
==================
- Allulose: Highest growth, requires close monitoring
- Trehalose: Longest shelf life, lower risk
- Tagatose: Premium product, watch for slow-moving inventory

COMMON QUERIES YOU'LL HANDLE:
==============================
- "Which products need reordering?"
- "What's our inventory turnover by product?"
- "Which POS locations are underperforming?"
- "Can we fulfill a large order for [product]?"
- "What's the sell-through rate in gyms?"
- "Do we have capacity to expand distribution?"
```

---

## Example Queries (Add these to Genie Space)

### Query 1: Inventory Days by Product
```sql
SELECT
  product_name,
  ROUND(SUM(current_stock_kg) / AVG(daily_sales_30d_avg), 1) as inventory_days,
  SUM(current_stock_kg) as total_stock_kg,
  AVG(daily_sales_30d_avg) as avg_daily_sales_kg
FROM biolabs_catalog.operations.inventory_levels
WHERE snapshot_date = (SELECT MAX(snapshot_date) FROM biolabs_catalog.operations.inventory_levels)
GROUP BY product_name
ORDER BY inventory_days ASC
```

### Query 2: Top POS by Allulose Volume
```sql
SELECT
  pos_name,
  pos_type,
  region,
  SUM(units_sold) as total_units,
  SUM(revenue) as total_revenue,
  ROUND(SUM(revenue) / SUM(units_sold), 2) as avg_price_per_kg
FROM biolabs_catalog.operations.sales_transactions
WHERE product_name = 'Allulose'
  AND date >= CURRENT_DATE - INTERVAL 90 DAY
GROUP BY pos_name, pos_type, region
ORDER BY total_units DESC
LIMIT 10
```

### Query 3: Products Below Safety Stock
```sql
SELECT
  i.product_name,
  i.current_stock_kg,
  i.days_on_hand,
  CASE
    WHEN i.product_name = 'Allulose' THEN 30
    ELSE 45
  END as target_days,
  CASE
    WHEN i.days_on_hand < 15 THEN 'CRITICAL'
    WHEN i.days_on_hand < 30 THEN 'WARNING'
    ELSE 'HEALTHY'
  END as status
FROM biolabs_catalog.operations.inventory_levels i
WHERE i.snapshot_date = (SELECT MAX(snapshot_date) FROM biolabs_catalog.operations.inventory_levels)
  AND i.days_on_hand < 45
ORDER BY i.days_on_hand ASC
```

### Query 4: Channel Performance Summary
```sql
SELECT
  pos_type as channel,
  COUNT(DISTINCT pos_id) as num_locations,
  SUM(units_sold) as total_units_kg,
  SUM(revenue) as total_revenue,
  ROUND(SUM(revenue) / SUM(units_sold), 2) as avg_price_per_kg,
  ROUND(SUM(revenue) / COUNT(DISTINCT pos_id), 2) as revenue_per_location
FROM biolabs_catalog.operations.sales_transactions
WHERE date >= CURRENT_DATE - INTERVAL 90 DAY
GROUP BY pos_type
ORDER BY total_revenue DESC
```

### Query 5: Sell-Through Rate by Product and Channel
```sql
SELECT
  s.product_name,
  s.pos_type as channel,
  SUM(s.units_sold) as units_sold,
  SUM(s.units_sold) / NULLIF(COUNT(DISTINCT s.date), 0) as avg_daily_sales,
  COUNT(DISTINCT s.pos_id) as active_locations,
  SUM(s.revenue) as total_revenue
FROM biolabs_catalog.operations.sales_transactions s
WHERE s.date >= CURRENT_DATE - INTERVAL 30 DAY
GROUP BY s.product_name, s.pos_type
ORDER BY s.product_name, total_revenue DESC
```

---

## SQL Functions to Create

Run these in Databricks SQL Editor:

```sql
USE SCHEMA biolabs_catalog.operations;

-- Calculate sell-through rate for specific product/POS
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
  FROM biolabs_catalog.operations.sales_transactions
  WHERE product_name = product
    AND pos_id = pos_id
    AND date >= CURRENT_DATE - INTERVAL days DAY
);

-- Calculate days on hand for product
CREATE OR REPLACE FUNCTION calc_days_on_hand(
  product STRING
)
RETURNS INT
COMMENT 'Calculate current days on hand for a product'
RETURN (
  SELECT days_on_hand
  FROM biolabs_catalog.operations.inventory_levels
  WHERE product_name = product
    AND snapshot_date = (SELECT MAX(snapshot_date) FROM biolabs_catalog.operations.inventory_levels)
  LIMIT 1
);
```

---

## Setup Checklist

- [ ] Create Genie Space named "Operations Specialist"
- [ ] Add all 5 tables from operations schema
- [ ] Copy Instructions text into Instructions field
- [ ] Add all 5 Example Queries
- [ ] Create SQL functions in Databricks
- [ ] Test with sample queries:
  - "What's our current inventory status?"
  - "Which products need reordering?"
  - "Show me top performing POS locations"
  - "What's the sell-through rate for Allulose in gyms?"

---

## Testing

Once configured, test with these questions:

1. **Inventory Health**: "Which products are below safety stock levels?"
2. **Channel Analysis**: "How are gyms performing compared to pharmacies?"
3. **Product Movement**: "What's the turnover rate for each product?"
4. **Distribution**: "Can we fulfill an order for 500kg of Allulose?"
5. **POS Performance**: "Which locations have the best sell-through rates?"

Expected: Genie should query tables, calculate metrics, and provide actionable insights.

---

## Notes for CEO Orchestrator

When routing questions to Operations Specialist, look for keywords:
- Inventory, stock, reorder
- Distribution, fulfillment, capacity
- POS, locations, channels
- Sell-through, turnover
- Production, manufacturing
