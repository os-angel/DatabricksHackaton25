"""
Configuration for synthetic data generation
"""
from datetime import datetime, timedelta

# Time range for data generation
START_DATE = datetime(2023, 1, 1)
END_DATE = datetime(2024, 12, 31)
TOTAL_DAYS = (END_DATE - START_DATE).days

# Products configuration
PRODUCTS = {
    "Tagatose": {
        "cogs_per_kg": 8.0,
        "retail_price_per_kg": 24.0,
        "shelf_life_months": 24,
        "market_share": 0.30,
        "seasonality": {1: 0.85, 2: 0.9, 3: 0.95, 4: 1.0, 5: 1.05, 6: 1.1,
                       7: 1.05, 8: 1.0, 9: 1.05, 10: 1.15, 11: 1.25, 12: 1.3},
        "target_segments": ["health_conscious", "diabetic"],
    },
    "Allulose": {
        "cogs_per_kg": 12.0,
        "retail_price_per_kg": 36.0,
        "shelf_life_months": 18,
        "market_share": 0.45,
        "seasonality": {1: 1.2, 2: 1.15, 3: 1.1, 4: 1.05, 5: 1.0, 6: 0.95,
                       7: 0.95, 8: 0.95, 9: 1.0, 10: 1.1, 11: 1.15, 12: 1.1},
        "target_segments": ["keto", "diabetic", "athlete"],
    },
    "Trehalose": {
        "cogs_per_kg": 6.0,
        "retail_price_per_kg": 18.0,
        "shelf_life_months": 36,
        "market_share": 0.25,
        "seasonality": {1: 0.95, 2: 0.95, 3: 1.0, 4: 1.05, 5: 1.1, 6: 1.15,
                       7: 1.2, 8: 1.15, 9: 1.1, 10: 1.05, 11: 1.0, 12: 0.95},
        "target_segments": ["athlete", "health_conscious"],
    }
}

# Distribution channels configuration
CHANNELS = {
    "pharmacy": {
        "count": 40,
        "margin": 0.45,
        "avg_daily_volume_kg": 2.5,
        "product_affinity": {"Tagatose": 0.35, "Allulose": 0.40, "Trehalose": 0.25},
    },
    "specialty_grocery": {
        "count": 50,
        "margin": 0.35,
        "avg_daily_volume_kg": 4.0,
        "product_affinity": {"Tagatose": 0.30, "Allulose": 0.50, "Trehalose": 0.20},
    },
    "gym": {
        "count": 35,
        "margin": 0.40,
        "avg_daily_volume_kg": 3.0,
        "product_affinity": {"Tagatose": 0.20, "Allulose": 0.45, "Trehalose": 0.35},
    },
    "hospital": {
        "count": 25,
        "margin": 0.25,
        "avg_daily_volume_kg": 3.5,
        "product_affinity": {"Tagatose": 0.30, "Allulose": 0.40, "Trehalose": 0.30},
    }
}

# Regions in Guatemala
REGIONS = ["Guatemala", "Quetzaltenango", "Escuintla", "Alta Verapaz", "Petén"]

# Customer segments
CUSTOMER_SEGMENTS = {
    "diabetic": {
        "size": 2_300_000,
        "avg_ltv": 450.0,
        "avg_order_value": 45.0,
        "purchase_frequency": 2.5,  # per month
        "retention_rate": 0.75,
        "primary_product": "Allulose",
    },
    "keto": {
        "size": 4_100_000,
        "avg_ltv": 280.0,
        "avg_order_value": 35.0,
        "purchase_frequency": 2.0,
        "retention_rate": 0.65,
        "primary_product": "Allulose",
    },
    "athlete": {
        "size": 3_200_000,
        "avg_ltv": 320.0,
        "avg_order_value": 40.0,
        "purchase_frequency": 2.2,
        "retention_rate": 0.70,
        "primary_product": "Trehalose",
    },
    "health_conscious": {
        "size": 8_700_000,
        "avg_ltv": 120.0,
        "avg_order_value": 20.0,
        "purchase_frequency": 1.5,
        "retention_rate": 0.55,
        "primary_product": "Tagatose",
    }
}

# Competitor landscape
COMPETITORS = {
    "Stevia": {
        "market_share": 0.70,
        "price_per_kg": 15.0,
        "strengths": ["Market leader", "Wide availability"],
        "weaknesses": ["Bitter aftertaste", "Limited applications"],
    },
    "Monk Fruit": {
        "market_share": 0.15,
        "price_per_kg": 45.0,
        "strengths": ["Natural", "Clean taste"],
        "weaknesses": ["High price", "Supply constraints"],
    },
    "Erythritol": {
        "market_share": 0.10,
        "price_per_kg": 12.0,
        "strengths": ["Low price", "Bulk availability"],
        "weaknesses": ["GI issues", "Negative perception"],
    },
    "Xylitol": {
        "market_share": 0.05,
        "price_per_kg": 18.0,
        "strengths": ["Dental benefits", "Similar to sugar"],
        "weaknesses": ["Pet toxicity", "Moderate price"],
    }
}

# Marketing channels
MARKETING_CHANNELS = {
    "social": {"cac": 35.0, "conversion_rate": 0.03},
    "influencer": {"cac": 55.0, "conversion_rate": 0.05},
    "demo": {"cac": 75.0, "conversion_rate": 0.12},
    "events": {"cac": 95.0, "conversion_rate": 0.08},
    "email": {"cac": 15.0, "conversion_rate": 0.02},
}

# Data generation parameters
NUM_TRANSACTIONS = 100_000
NUM_POS = sum(ch["count"] for ch in CHANNELS.values())  # 150 total
NUM_CAMPAIGNS = 50
