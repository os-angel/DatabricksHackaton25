"""
MCP Server Configuration for BioLabs
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Server configuration
SERVER_HOST = os.getenv("MCP_SERVER_HOST", "localhost")
SERVER_PORT = int(os.getenv("MCP_SERVER_PORT", "8000"))

# Databricks configuration
DATABRICKS_HOST = os.getenv("DATABRICKS_HOST")
DATABRICKS_TOKEN = os.getenv("DATABRICKS_TOKEN")
DATABRICKS_WAREHOUSE_ID = os.getenv("DATABRICKS_WAREHOUSE_ID")
CATALOG_NAME = os.getenv("CATALOG_NAME", "biolabs_catalog")

# Product configuration
PRODUCTS = {
    "Tagatose": {
        "cogs_per_kg": 8.0,
        "retail_price_per_kg": 24.0,
        "shelf_life_months": 24,
        "elasticity": -1.2,  # Price elasticity
    },
    "Allulose": {
        "cogs_per_kg": 12.0,
        "retail_price_per_kg": 36.0,
        "shelf_life_months": 18,
        "elasticity": -1.5,
    },
    "Trehalose": {
        "cogs_per_kg": 6.0,
        "retail_price_per_kg": 18.0,
        "shelf_life_months": 36,
        "elasticity": -0.9,
    }
}

# Channel configuration
CHANNELS = {
    "pharmacy": {"margin": 0.45, "avg_volume_kg": 2.5},
    "specialty_grocery": {"margin": 0.35, "avg_volume_kg": 4.0},
    "gym": {"margin": 0.40, "avg_volume_kg": 3.0},
    "hospital": {"margin": 0.25, "avg_volume_kg": 3.5},
}

# Marketing channel CAC (Customer Acquisition Cost)
MARKETING_CHANNELS = {
    "social": {"cac": 35.0, "conversion_rate": 0.03},
    "influencer": {"cac": 55.0, "conversion_rate": 0.05},
    "demo": {"cac": 75.0, "conversion_rate": 0.12},
    "events": {"cac": 95.0, "conversion_rate": 0.08},
}

# Customer segments
CUSTOMER_SEGMENTS = {
    "diabetic": {"avg_ltv": 450.0, "retention_rate": 0.75},
    "keto": {"avg_ltv": 280.0, "retention_rate": 0.65},
    "athlete": {"avg_ltv": 320.0, "retention_rate": 0.70},
    "health_conscious": {"avg_ltv": 120.0, "retention_rate": 0.55},
}

# Production capacity (kg/month)
PRODUCTION_CAPACITY = {
    "Tagatose": 50000,
    "Allulose": 40000,
    "Trehalose": 60000,
}

# Financial targets
DISCOUNT_RATE = 0.15  # For NPV calculations
TARGET_PAYBACK_MONTHS = 18
MIN_GROSS_MARGIN = 0.40
