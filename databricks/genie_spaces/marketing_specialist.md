# Genie Space Configuration: Marketing Specialist

## Overview
This Genie Space provides marketing insights for BioLabs, focusing on customer acquisition, campaign performance, and competitive positioning.

---

## Data Assets

### Tables to Add:
1. `biolabs_catalog.marketing.campaigns`
2. `biolabs_catalog.marketing.customer_segments`
3. `biolabs_catalog.marketing.competitor_intel`
4. `biolabs_catalog.marketing.channel_performance`

---

## Instructions

```
CONTEXT:
========
BioLabs Brand Positioning:
- Tagatose: "Premium natural sweetener for health-conscious consumers"
- Allulose: "Science-backed, zero-net-carb solution for keto/diabetic"
- Trehalose: "Sustained energy for athletes and active lifestyles"

COMPETITIVE LANDSCAPE:
======================
Main Competitors:
- Stevia: 70% market share, taste issues, declining favorability
- Monk Fruit: Premium segment, supply-constrained, high price
- Erythritol: Declining due to GI side effects and negative studies
- Xylitol: Niche player, pet toxicity concerns

BioLabs Advantage: Science-backed efficacy, superior taste, multi-product portfolio

CUSTOMER SEGMENTS:
==================
1. Diabetics (2.3M potential)
   - High LTV: $450
   - Best product: Allulose
   - Channels: Pharmacy, Hospital
   - Education-intensive, doctor-driven

2. Keto (4.1M potential)
   - Medium LTV: $280
   - Best product: Allulose
   - Channels: Specialty Grocery, Gym
   - Digital-native, social media influenced

3. Athletes (3.2M potential)
   - Medium-High LTV: $320
   - Best product: Trehalose
   - Channels: Gym, Specialty Grocery
   - Performance-focused, brand loyal

4. Health-Conscious (8.7M potential)
   - Low LTV: $120
   - Best product: Tagatose
   - Channels: Specialty Grocery
   - Mass market, price-sensitive

CHANNEL ECONOMICS:
==================
- Pharmacy: 45% margin, slow education, high CAC ($400-500)
- Specialty Grocery: 35% margin, fast adoption, medium CAC ($300-400)
- Gyms: 40% margin, demo-intensive, medium CAC ($350-450)
- Hospitals: 25% margin, long sales cycle, high CAC ($500-600)

MARKETING CHANNELS:
===================
- Social Media: CAC $35, conversion rate 3%, scalable
- Influencer: CAC $55, conversion rate 5%, trust-building
- Demo Events: CAC $75, conversion rate 12%, high touch
- Trade Events: CAC $95, conversion rate 8%, B2B focused
- Email: CAC $15, conversion rate 2%, retention tool

KEY METRICS TO ALWAYS CALCULATE:
=================================
1. CAC (Customer Acquisition Cost) = Marketing Spend / New Customers
   - Target: < $60 for mass market, < $100 for premium segments

2. LTV (Lifetime Value) = Avg Order × Frequency × Lifespan
   - Target: LTV/CAC ratio > 3:1

3. Payback Period = CAC / Monthly Revenue per Customer
   - Target: < 12 months

4. Conversion Rate by Channel
   - Track: Impressions → Clicks → Conversions

WHEN ANSWERING QUESTIONS:
==========================
1. Always segment analysis by customer type
2. Calculate CAC and LTV for any campaign recommendations
3. Consider competitive positioning
4. Match products to segments (Allulose→Keto/Diabetic, Trehalose→Athletes, etc.)
5. Evaluate channel fit (digital for Keto, pharmacy for Diabetics)
6. Factor in payback period for budget recommendations
7. Analyze trends vs. prior periods

STRATEGIC PRIORITIES:
=====================
- Grow Allulose in keto segment (highest volume potential)
- Defend diabetic segment from Stevia
- Expand Trehalose in athletic channels
- Build awareness of Tagatose in mass market
```

---

## Example Queries

### Query 1: CAC by Customer Segment
```sql
SELECT
  target_segment as segment,
  COUNT(DISTINCT campaign_id) as num_campaigns,
  SUM(budget) as total_spend,
  SUM(conversions) as total_conversions,
  ROUND(SUM(budget) / NULLIF(SUM(conversions), 0), 2) as cac,
  ROUND(SUM(revenue_attributed) / NULLIF(SUM(budget), 0) * 100, 2) as roi_pct
FROM biolabs_catalog.marketing.campaigns
WHERE start_date >= ADD_MONTHS(CURRENT_DATE, -6)
GROUP BY target_segment
ORDER BY cac ASC
```

### Query 2: Campaign Performance by Channel
```sql
SELECT
  channel,
  product,
  COUNT(*) as num_campaigns,
  SUM(budget) as total_budget,
  SUM(impressions) as total_impressions,
  SUM(clicks) as total_clicks,
  SUM(conversions) as total_conversions,
  ROUND(SUM(clicks) / NULLIF(SUM(impressions), 0) * 100, 3) as ctr_pct,
  ROUND(SUM(conversions) / NULLIF(SUM(clicks), 0) * 100, 2) as conversion_rate_pct,
  ROUND(SUM(revenue_attributed), 2) as total_revenue
FROM biolabs_catalog.marketing.campaigns
WHERE end_date >= CURRENT_DATE - INTERVAL 90 DAY
GROUP BY channel, product
ORDER BY total_revenue DESC
```

### Query 3: Customer Segment Opportunities
```sql
SELECT
  segment,
  size as market_size,
  avg_ltv,
  avg_order_value,
  purchase_frequency,
  retention_rate,
  primary_product,
  ROUND(avg_ltv * size / 1000000, 2) as total_market_value_millions
FROM biolabs_catalog.marketing.customer_segments
ORDER BY avg_ltv DESC
```

### Query 4: LTV/CAC Ratio by Segment
```sql
SELECT
  c.target_segment as segment,
  ROUND(AVG(s.avg_ltv), 2) as avg_ltv,
  ROUND(SUM(c.budget) / NULLIF(SUM(c.conversions), 0), 2) as avg_cac,
  ROUND(AVG(s.avg_ltv) / NULLIF(SUM(c.budget) / NULLIF(SUM(c.conversions), 0), 0), 2) as ltv_to_cac_ratio,
  CASE
    WHEN AVG(s.avg_ltv) / NULLIF(SUM(c.budget) / NULLIF(SUM(c.conversions), 0), 0) >= 3 THEN 'EXCELLENT'
    WHEN AVG(s.avg_ltv) / NULLIF(SUM(c.budget) / NULLIF(SUM(c.conversions), 0), 0) >= 2 THEN 'GOOD'
    WHEN AVG(s.avg_ltv) / NULLIF(SUM(c.budget) / NULLIF(SUM(c.conversions), 0), 0) >= 1 THEN 'ACCEPTABLE'
    ELSE 'POOR'
  END as assessment
FROM biolabs_catalog.marketing.campaigns c
JOIN biolabs_catalog.marketing.customer_segments s ON c.target_segment = s.segment
WHERE c.start_date >= ADD_MONTHS(CURRENT_DATE, -6)
GROUP BY c.target_segment
ORDER BY ltv_to_cac_ratio DESC
```

### Query 5: Competitive Landscape
```sql
SELECT
  competitor,
  price_per_kg,
  market_share_pct,
  ROUND(price_per_kg / (SELECT AVG(price_per_kg) FROM biolabs_catalog.marketing.competitor_intel) * 100, 1) as price_index,
  strengths,
  weaknesses
FROM biolabs_catalog.marketing.competitor_intel
ORDER BY market_share_pct DESC
```

---

## SQL Functions

```sql
USE SCHEMA biolabs_catalog.marketing;

-- Calculate CAC for a segment over date range
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
  FROM biolabs_catalog.marketing.campaigns
  WHERE target_segment = segment
    AND start_date >= start_date
    AND end_date <= end_date
);

-- Get recommended marketing channel for segment
CREATE OR REPLACE FUNCTION get_recommended_channels(
  segment STRING
)
RETURNS STRING
COMMENT 'Get recommended marketing channels for a customer segment'
RETURN (
  CASE
    WHEN segment = 'diabetic' THEN 'pharmacy, hospital, email'
    WHEN segment = 'keto' THEN 'social, influencer, specialty_grocery'
    WHEN segment = 'athlete' THEN 'gym, demo, influencer'
    WHEN segment = 'health_conscious' THEN 'specialty_grocery, social'
    ELSE 'social, specialty_grocery'
  END
);
```

---

## Setup Checklist

- [ ] Create Genie Space "Marketing Specialist"
- [ ] Add 4 marketing tables
- [ ] Copy instructions
- [ ] Add 5 example queries
- [ ] Create SQL functions
- [ ] Test with sample questions

---

## Test Questions

1. "What's our CAC by customer segment?"
2. "Which marketing channel has the best ROI?"
3. "What's the LTV/CAC ratio for the keto segment?"
4. "How does our pricing compare to competitors?"
5. "Which customer segment should we prioritize?"

---

## Routing Keywords (for CEO Orchestrator)

- Marketing, campaign, acquisition
- CAC, LTV, ROI
- Customer segment, targeting
- Competitors, competitive, market share
- Channel, social media, influencer
