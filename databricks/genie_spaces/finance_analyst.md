# Genie Space Configuration: Finance Analyst

## Overview
This Genie Space provides financial insights for BioLabs, focusing on profitability, pricing strategy, and investment decisions.

---

## Data Assets

### Tables to Add:
1. `biolabs_catalog.finance.product_costs`
2. `biolabs_catalog.finance.revenue_by_channel`
3. `biolabs_catalog.finance.budgets`
4. `biolabs_catalog.finance.margin_analysis`

---

## Instructions

```
CONTEXT:
========
BioLabs Product Economics:

PRODUCT COST STRUCTURE:
=======================
Tagatose:
- COGS: $8/kg (enzymatic conversion, moderate complexity)
- Retail: $24/kg
- Target Gross Margin: 66% (retail), 50% (wholesale)

Allulose:
- COGS: $12/kg (rare fermentation process, complex)
- Retail: $36/kg
- Target Gross Margin: 66% (retail), 50% (wholesale)

Trehalose:
- COGS: $6/kg (enzymatic, commodity inputs)
- Retail: $18/kg
- Target Gross Margin: 66% (retail), 50% (wholesale)

PRICING STRATEGY:
==================
- Standard markup: 3x COGS for retail
- Wholesale pricing: 50-75% of retail (depending on channel)
- Volume discounts: 5-10% for hospital contracts
- Premium pricing: Maintained for Allulose (science-backed value)

CHANNEL-SPECIFIC MARGINS:
==========================
- Direct to Consumer (if launched): 50% gross margin
- Specialty Grocery: 35% gross margin (wholesale)
- Pharmacy: 45% gross margin (wholesale + services)
- Hospital/Institutional: 25% gross margin (contractual)
- Gym: 40% gross margin (demo support)

FINANCIAL TARGETS:
==================
- Gross Margin: ≥40% (company-wide minimum)
- Contribution Margin: ≥30% after variable costs
- EBITDA Margin: 15% target
- Operating Margin: 10% target

Variable Costs (beyond COGS):
- Packaging: 8% of COGS
- Distribution: 5% of COGS
- Marketing: 15-20% of revenue (variable by segment)

KEY METRICS TO ALWAYS CALCULATE:
=================================
1. Gross Margin % = (Revenue - COGS) / Revenue
2. Contribution Margin % = (Revenue - Variable Costs) / Revenue
3. Break-Even Units = Fixed Costs / Contribution Margin per Unit
4. NPV = Σ(Cash Flows / (1 + Discount Rate)^t)
   - Use 15% discount rate
5. Payback Period = Investment / Annual Cash Flow
6. ROI % = (Gain - Cost) / Cost × 100

INVESTMENT EVALUATION CRITERIA:
================================
- ROI: Minimum 25% over 3 years
- Payback: Maximum 18 months preferred, 24 months acceptable
- NPV: Must be positive at 15% discount rate
- Risk-adjusted return: Higher returns for higher-risk initiatives

COST ANALYSIS FRAMEWORK:
========================
When evaluating new initiatives:
1. Calculate full variable cost per unit
2. Estimate fixed costs (one-time + recurring)
3. Project revenue over 12-36 months
4. Calculate break-even point
5. Assess sensitivity (best/base/worst case)
6. Compare to hurdle rates

WHEN ANSWERING QUESTIONS:
==========================
1. Always calculate both gross and contribution margins
2. Break down costs by category (COGS, packaging, distribution, marketing)
3. Compare actuals to targets (40% gross, 30% contribution)
4. Analyze trends vs. prior periods
5. Segment analysis by product AND channel
6. Flag margin erosion or pricing pressure
7. Calculate payback period for any investment question
8. Provide NPV for multi-year decisions
9. Include sensitivity analysis (±20% revenue scenarios)

PRICING DECISION FRAMEWORK:
============================
Price Increase Considerations:
- Competitive position
- Demand elasticity (Allulose: -1.5, Tagatose: -1.2, Trehalose: -0.9)
- Customer segment (diabetics less price-sensitive)
- Market share impact

Price Decrease Considerations:
- Volume opportunity
- Market penetration
- Competitor response
- Margin impact tolerance

FINANCIAL REPORTING:
====================
- Revenue recognition: Point of sale to wholesaler
- Inventory valuation: FIFO
- Depreciation: Straight-line, 7 years for equipment
- Working capital: 45 days inventory, 30 days receivables
```

---

## Example Queries

### Query 1: Product Profitability Analysis
```sql
SELECT
  r.product_name,
  SUM(r.revenue) as total_revenue,
  SUM(r.cost) as total_cogs,
  SUM(r.gross_profit) as total_gross_profit,
  ROUND(AVG(r.gross_margin_pct), 2) as avg_gross_margin_pct,
  ROUND(SUM(r.revenue) / SUM(r.cost), 2) as revenue_to_cost_ratio,
  CASE
    WHEN AVG(r.gross_margin_pct) >= 40 THEN 'EXCELLENT'
    WHEN AVG(r.gross_margin_pct) >= 35 THEN 'GOOD'
    WHEN AVG(r.gross_margin_pct) >= 30 THEN 'ACCEPTABLE'
    ELSE 'POOR'
  END as margin_assessment
FROM biolabs_catalog.finance.revenue_by_channel r
WHERE r.month >= ADD_MONTHS(CURRENT_DATE, -12)
GROUP BY r.product_name
ORDER BY avg_gross_margin_pct DESC
```

### Query 2: Channel Margin Analysis
```sql
SELECT
  r.channel,
  COUNT(DISTINCT r.product_name) as num_products,
  SUM(r.revenue) as total_revenue,
  SUM(r.gross_profit) as total_gross_profit,
  ROUND(AVG(r.gross_margin_pct), 2) as avg_margin_pct,
  ROUND(SUM(r.revenue) * 100 / (SELECT SUM(revenue) FROM biolabs_catalog.finance.revenue_by_channel WHERE month >= ADD_MONTHS(CURRENT_DATE, -12)), 2) as revenue_mix_pct
FROM biolabs_catalog.finance.revenue_by_channel r
WHERE r.month >= ADD_MONTHS(CURRENT_DATE, -12)
GROUP BY r.channel
ORDER BY total_revenue DESC
```

### Query 3: Margin Trends (Quarterly)
```sql
SELECT
  DATE_TRUNC('quarter', r.month) as quarter,
  r.product_name,
  SUM(r.revenue) as quarterly_revenue,
  ROUND(AVG(r.gross_margin_pct), 2) as avg_margin_pct,
  LAG(AVG(r.gross_margin_pct)) OVER (PARTITION BY r.product_name ORDER BY DATE_TRUNC('quarter', r.month)) as prior_quarter_margin,
  ROUND(AVG(r.gross_margin_pct) - LAG(AVG(r.gross_margin_pct)) OVER (PARTITION BY r.product_name ORDER BY DATE_TRUNC('quarter', r.month)), 2) as margin_change_pct
FROM biolabs_catalog.finance.revenue_by_channel r
WHERE r.month >= ADD_MONTHS(CURRENT_DATE, -24)
GROUP BY DATE_TRUNC('quarter', r.month), r.product_name
ORDER BY quarter DESC, avg_margin_pct DESC
```

### Query 4: Product-Channel Matrix (Contribution)
```sql
SELECT
  r.product_name,
  r.channel,
  SUM(r.revenue) as revenue,
  SUM(r.gross_profit) as gross_profit,
  ROUND(AVG(r.gross_margin_pct), 2) as gross_margin_pct,
  -- Estimate contribution margin (gross margin - 13% variable costs)
  ROUND(AVG(r.gross_margin_pct) - 13, 2) as est_contribution_margin_pct,
  ROUND(SUM(r.gross_profit) * 0.87, 2) as est_contribution_profit
FROM biolabs_catalog.finance.revenue_by_channel r
WHERE r.month >= ADD_MONTHS(CURRENT_DATE, -6)
GROUP BY r.product_name, r.channel
ORDER BY est_contribution_profit DESC
```

### Query 5: Price Point Analysis
```sql
SELECT
  c.product_name,
  c.cogs_per_kg,
  c.total_variable_cost,
  -- Calculate required selling price for 40% gross margin
  ROUND(c.cogs_per_kg / (1 - 0.40), 2) as min_price_40pct_margin,
  -- Calculate current average selling price from revenue
  ROUND(AVG(r.revenue / NULLIF(r.revenue / (r.revenue / (c.total_variable_cost * (r.revenue / r.cost))), 0)), 2) as current_avg_price,
  -- Margin at current price
  ROUND((1 - c.cogs_per_kg / NULLIF(r.revenue / NULLIF(r.revenue / (c.total_variable_cost * (r.revenue / r.cost)), 0), 0)) * 100, 2) as current_margin_pct
FROM biolabs_catalog.finance.product_costs c
LEFT JOIN biolabs_catalog.finance.revenue_by_channel r ON c.product_name = r.product_name
WHERE r.month >= ADD_MONTHS(CURRENT_DATE, -3)
GROUP BY c.product_name, c.cogs_per_kg, c.total_variable_cost
```

---

## SQL Functions

```sql
USE SCHEMA biolabs_catalog.finance;

-- Calculate gross margin for product-channel combo
CREATE OR REPLACE FUNCTION calc_gross_margin(
  product STRING,
  channel STRING
)
RETURNS DECIMAL(4,2)
COMMENT 'Calculate gross margin % for product-channel combination'
RETURN (
  SELECT
    COALESCE(AVG(gross_margin_pct), 0)
  FROM biolabs_catalog.finance.revenue_by_channel
  WHERE product_name = product
    AND channel = channel
    AND month >= ADD_MONTHS(CURRENT_DATE, -6)
);

-- Calculate break-even units
CREATE OR REPLACE FUNCTION calc_break_even_units(
  fixed_costs DOUBLE,
  price_per_unit DOUBLE,
  variable_cost_per_unit DOUBLE
)
RETURNS BIGINT
COMMENT 'Calculate break-even units given fixed costs, price, and variable cost'
RETURN (
  CASE
    WHEN price_per_unit > variable_cost_per_unit
    THEN CAST(fixed_costs / (price_per_unit - variable_cost_per_unit) AS BIGINT)
    ELSE NULL
  END
);

-- Calculate NPV
CREATE OR REPLACE FUNCTION calc_npv(
  initial_investment DOUBLE,
  annual_cash_flow DOUBLE,
  years INT,
  discount_rate DOUBLE
)
RETURNS DOUBLE
COMMENT 'Calculate Net Present Value'
RETURN (
  -initial_investment +
  (annual_cash_flow * ((1 - POWER(1 + discount_rate, -years)) / discount_rate))
);
```

---

## Setup Checklist

- [ ] Create Genie Space "Finance Analyst"
- [ ] Add 4 finance tables
- [ ] Copy instructions
- [ ] Add 5 example queries
- [ ] Create SQL functions
- [ ] Test with sample questions

---

## Test Questions

1. "What's our gross margin by product?"
2. "Which channel is most profitable?"
3. "What's the break-even point for launching in gyms?"
4. "Should we increase the price of Tagatose?"
5. "What's the NPV of expanding production capacity?"

---

## Routing Keywords (for CEO Orchestrator)

- Finance, financial, profitability
- Margin, gross margin, contribution
- ROI, return on investment
- NPV, net present value, payback
- Break-even, breakeven
- Pricing, price increase, revenue
- Cost, COGS, expenses
