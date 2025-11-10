"""
Data Tools for BioLabs MCP Server

These tools provide data aggregation and retrieval:
9. get_sales_summary
10. get_inventory_status
11. get_competitor_intel
12. get_customer_segments
"""

from typing import Dict, Any, List, Optional
from datetime import date, timedelta
from ..config import CUSTOMER_SEGMENTS


# Note: In production, these would query Databricks via SQL
# For now, we'll simulate with example data


def get_sales_summary(
    product: Optional[str] = None,
    channel: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get aggregated sales summary.

    Args:
        product: Filter by product (optional)
        channel: Filter by channel (optional)
        start_date: Start date YYYY-MM-DD (optional)
        end_date: End date YYYY-MM-DD (optional)

    Returns:
        Sales summary data
    """
    # In production, this would query:
    # SELECT product_name, pos_type, SUM(revenue), SUM(units_sold)
    # FROM biolabs_catalog.operations.sales_transactions
    # WHERE date BETWEEN start_date AND end_date
    # GROUP BY product_name, pos_type

    # Simulated data
    if start_date is None:
        start_date = (date.today() - timedelta(days=90)).isoformat()
    if end_date is None:
        end_date = date.today().isoformat()

    # Sample sales data (in production, query from Databricks)
    all_sales = {
        "Tagatose": {
            "pharmacy": {"revenue": 125000, "units": 5200},
            "specialty_grocery": {"revenue": 180000, "units": 7500},
            "gym": {"revenue": 45000, "units": 1875},
            "hospital": {"revenue": 95000, "units": 3950}
        },
        "Allulose": {
            "pharmacy": {"revenue": 210000, "units": 5833},
            "specialty_grocery": {"revenue": 320000, "units": 8889},
            "gym": {"revenue": 180000, "units": 5000},
            "hospital": {"revenue": 140000, "units": 3889}
        },
        "Trehalose": {
            "pharmacy": {"revenue": 90000, "units": 5000},
            "specialty_grocery": {"revenue": 160000, "units": 8889},
            "gym": {"revenue": 108000, "units": 6000},
            "hospital": {"revenue": 85000, "units": 4722}
        }
    }

    # Filter data
    filtered_sales = {}
    total_revenue = 0
    total_units = 0

    for prod, channels in all_sales.items():
        if product and prod != product:
            continue

        for chan, metrics in channels.items():
            if channel and chan != channel:
                continue

            key = f"{prod} - {chan}"
            filtered_sales[key] = metrics
            total_revenue += metrics["revenue"]
            total_units += metrics["units"]

    # Calculate average price
    avg_price = total_revenue / total_units if total_units > 0 else 0

    # Calculate growth (simulated)
    prior_period_revenue = total_revenue * 0.85  # Assume 15% growth
    growth_vs_prior = ((total_revenue - prior_period_revenue) / prior_period_revenue) * 100

    return {
        "filters": {
            "product": product if product else "All",
            "channel": channel if channel else "All",
            "start_date": start_date,
            "end_date": end_date
        },
        "summary": {
            "total_revenue": round(total_revenue, 2),
            "total_units": total_units,
            "avg_price": round(avg_price, 2),
            "growth_vs_prior_period_pct": round(growth_vs_prior, 2)
        },
        "breakdown": {
            k: {
                "revenue": v["revenue"],
                "units": v["units"],
                "avg_price": round(v["revenue"] / v["units"], 2) if v["units"] > 0 else 0
            }
            for k, v in filtered_sales.items()
        },
        "data_source": "biolabs_catalog.operations.sales_transactions"
    }


def get_inventory_status(
    product: str,
    alert_threshold_days: int = 30
) -> Dict[str, Any]:
    """
    Get current inventory status for a product.

    Args:
        product: Product name
        alert_threshold_days: Alert if days on hand below this (default: 30)

    Returns:
        Inventory status
    """
    # In production, query:
    # SELECT product_name, current_stock_kg, days_on_hand
    # FROM biolabs_catalog.operations.inventory_levels
    # WHERE snapshot_date = (SELECT MAX(snapshot_date) FROM inventory_levels)
    # AND product_name = product

    # Simulated current inventory
    inventory_data = {
        "Tagatose": {
            "current_stock_kg": 1250.50,
            "reserved_stock_kg": 180.00,
            "available_stock_kg": 1070.50,
            "daily_sales_avg_kg": 25.5,
            "location": "Main Warehouse"
        },
        "Allulose": {
            "current_stock_kg": 875.25,
            "reserved_stock_kg": 150.00,
            "available_stock_kg": 725.25,
            "daily_sales_avg_kg": 35.8,
            "location": "Main Warehouse"
        },
        "Trehalose": {
            "current_stock_kg": 1580.75,
            "reserved_stock_kg": 200.00,
            "available_stock_kg": 1380.75,
            "daily_sales_avg_kg": 28.2,
            "location": "Main Warehouse"
        }
    }

    if product not in inventory_data:
        return {"error": f"No inventory data for product: {product}"}

    inv = inventory_data[product]
    days_on_hand = inv["available_stock_kg"] / inv["daily_sales_avg_kg"]

    # Determine status
    if days_on_hand < alert_threshold_days * 0.5:
        status = "CRITICAL"
        reorder_recommended = True
    elif days_on_hand < alert_threshold_days:
        status = "WARNING"
        reorder_recommended = True
    elif days_on_hand <= alert_threshold_days * 1.5:
        status = "HEALTHY"
        reorder_recommended = False
    else:
        status = "OVERSTOCKED"
        reorder_recommended = False

    # Calculate reorder quantity
    target_days = 45
    target_stock = inv["daily_sales_avg_kg"] * target_days
    reorder_quantity = max(0, target_stock - inv["available_stock_kg"])

    return {
        "product": product,
        "location": inv["location"],
        "inventory": {
            "current_stock_kg": inv["current_stock_kg"],
            "reserved_stock_kg": inv["reserved_stock_kg"],
            "available_stock_kg": inv["available_stock_kg"],
            "days_on_hand": round(days_on_hand, 1)
        },
        "sales": {
            "daily_average_kg": inv["daily_sales_avg_kg"],
            "weekly_average_kg": round(inv["daily_sales_avg_kg"] * 7, 1),
            "monthly_average_kg": round(inv["daily_sales_avg_kg"] * 30, 1)
        },
        "status": status,
        "reorder_recommended": reorder_recommended,
        "reorder_quantity_kg": round(reorder_quantity, 2) if reorder_recommended else 0,
        "alert_threshold_days": alert_threshold_days,
        "data_source": "biolabs_catalog.operations.inventory_levels"
    }


def get_competitor_intel(
    competitor: Optional[str] = None,
    product_category: str = "Sugar Substitute"
) -> Dict[str, Any]:
    """
    Get competitor intelligence data.

    Args:
        competitor: Specific competitor name (optional)
        product_category: Product category (default: Sugar Substitute)

    Returns:
        Competitor intelligence
    """
    # In production, query:
    # SELECT competitor, price_per_kg, market_share_pct, strengths, weaknesses
    # FROM biolabs_catalog.marketing.competitor_intel
    # WHERE product_category = category

    competitors_data = {
        "Stevia": {
            "price_per_kg": 15.00,
            "market_share_pct": 70.0,
            "recent_actions": [
                "Launched new blend with erythritol (Q4 2024)",
                "Expanded into 500 new pharmacy locations (Q3 2024)"
            ],
            "threat_level": "HIGH",
            "strengths": "Market leader, wide availability, low price",
            "weaknesses": "Bitter aftertaste, limited applications"
        },
        "Monk Fruit": {
            "price_per_kg": 45.00,
            "market_share_pct": 15.0,
            "recent_actions": [
                "Supply shortage reported (Nov 2024)",
                "Price increase of 12% (Oct 2024)"
            ],
            "threat_level": "MEDIUM",
            "strengths": "Natural, clean taste, premium positioning",
            "weaknesses": "High price, supply constraints"
        },
        "Erythritol": {
            "price_per_kg": 12.00,
            "market_share_pct": 10.0,
            "recent_actions": [
                "Negative study on cardiovascular effects (Mar 2024)",
                "Market share declining 15% YoY"
            ],
            "threat_level": "LOW",
            "strengths": "Low price, bulk availability",
            "weaknesses": "GI issues, negative perception, declining"
        },
        "Xylitol": {
            "price_per_kg": 18.00,
            "market_share_pct": 5.0,
            "recent_actions": [
                "Dental health campaign launched (Q2 2024)"
            ],
            "threat_level": "LOW",
            "strengths": "Dental benefits, similar to sugar",
            "weaknesses": "Pet toxicity concerns, moderate price"
        }
    }

    if competitor:
        if competitor not in competitors_data:
            return {"error": f"No data for competitor: {competitor}"}
        result = {competitor: competitors_data[competitor]}
    else:
        result = competitors_data

    # Calculate BioLabs position
    total_market_share = sum(c["market_share_pct"] for c in competitors_data.values())
    biolabs_market_share = max(0, 100 - total_market_share)

    return {
        "product_category": product_category,
        "competitors": result,
        "market_overview": {
            "total_competitors": len(competitors_data),
            "biolabs_estimated_market_share_pct": round(biolabs_market_share, 1),
            "avg_competitor_price": round(
                sum(c["price_per_kg"] for c in competitors_data.values()) / len(competitors_data), 2
            )
        },
        "competitive_positioning": _analyze_competitive_position(competitors_data),
        "data_source": "biolabs_catalog.marketing.competitor_intel"
    }


def get_customer_segments(
    min_ltv: Optional[float] = None,
    product_affinity: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get customer segmentation data.

    Args:
        min_ltv: Minimum lifetime value filter (optional)
        product_affinity: Filter by product affinity (optional)

    Returns:
        Customer segments information
    """
    # In production, query:
    # SELECT segment, size, avg_ltv, retention_rate, primary_product
    # FROM biolabs_catalog.marketing.customer_segments
    # WHERE avg_ltv >= min_ltv

    segments_data = {
        "diabetic": {
            "size": 2_300_000,
            "avg_ltv": 450.0,
            "avg_order_value": 45.0,
            "purchase_frequency": 2.5,
            "retention_rate": 0.75,
            "primary_product": "Allulose",
            "characteristics": [
                "Health-focused",
                "Doctor recommended",
                "Price less sensitive",
                "Regular purchasing pattern"
            ],
            "recommended_channels": ["pharmacy", "hospital"],
            "acquisition_difficulty": "MEDIUM"
        },
        "keto": {
            "size": 4_100_000,
            "avg_ltv": 280.0,
            "avg_order_value": 35.0,
            "purchase_frequency": 2.0,
            "retention_rate": 0.65,
            "primary_product": "Allulose",
            "characteristics": [
                "Digital-native",
                "Trend-driven",
                "Social media influenced",
                "Moderate loyalty"
            ],
            "recommended_channels": ["specialty_grocery", "gym"],
            "acquisition_difficulty": "EASY"
        },
        "athlete": {
            "size": 3_200_000,
            "avg_ltv": 320.0,
            "avg_order_value": 40.0,
            "purchase_frequency": 2.2,
            "retention_rate": 0.70,
            "primary_product": "Trehalose",
            "characteristics": [
                "Performance-focused",
                "Premium tolerance",
                "Brand loyal",
                "Influenced by endorsements"
            ],
            "recommended_channels": ["gym", "specialty_grocery"],
            "acquisition_difficulty": "MEDIUM"
        },
        "health_conscious": {
            "size": 8_700_000,
            "avg_ltv": 120.0,
            "avg_order_value": 20.0,
            "purchase_frequency": 1.5,
            "retention_rate": 0.55,
            "primary_product": "Tagatose",
            "characteristics": [
                "Mass market",
                "Price sensitive",
                "Natural preference",
                "Lower engagement"
            ],
            "recommended_channels": ["specialty_grocery"],
            "acquisition_difficulty": "EASY"
        }
    }

    # Apply filters
    filtered_segments = {}
    for segment, data in segments_data.items():
        if min_ltv and data["avg_ltv"] < min_ltv:
            continue
        if product_affinity and data["primary_product"] != product_affinity:
            continue

        filtered_segments[segment] = data

    # Calculate totals
    total_addressable_market = sum(s["size"] for s in filtered_segments.values())
    weighted_avg_ltv = (
        sum(s["size"] * s["avg_ltv"] for s in filtered_segments.values()) / total_addressable_market
        if total_addressable_market > 0 else 0
    )

    return {
        "filters": {
            "min_ltv": min_ltv if min_ltv else "None",
            "product_affinity": product_affinity if product_affinity else "None"
        },
        "segments": filtered_segments,
        "summary": {
            "total_segments": len(filtered_segments),
            "total_addressable_market": total_addressable_market,
            "weighted_avg_ltv": round(weighted_avg_ltv, 2)
        },
        "recommendations": _segment_recommendations(filtered_segments),
        "data_source": "biolabs_catalog.marketing.customer_segments"
    }


# Helper functions
def _analyze_competitive_position(competitors: Dict[str, Any]) -> str:
    """Analyze BioLabs competitive position"""
    avg_price = sum(c["price_per_kg"] for c in competitors.values()) / len(competitors)
    biolabs_avg_price = (24 + 36 + 18) / 3  # Our products

    if biolabs_avg_price > avg_price * 1.2:
        return "PREMIUM: BioLabs products priced above market average. Emphasize quality and efficacy."
    elif biolabs_avg_price < avg_price * 0.8:
        return "VALUE: BioLabs products priced below market. Opportunity to increase margins or drive volume."
    else:
        return "COMPETITIVE: BioLabs pricing aligned with market. Differentiate on benefits and availability."


def _segment_recommendations(segments: Dict[str, Any]) -> List[str]:
    """Generate segment targeting recommendations"""
    recommendations = []

    # Sort by LTV
    sorted_segments = sorted(segments.items(), key=lambda x: x[1]["avg_ltv"], reverse=True)

    if sorted_segments:
        top_segment = sorted_segments[0]
        recommendations.append(
            f"PRIORITIZE: '{top_segment[0]}' segment has highest LTV (${top_segment[1]['avg_ltv']}) - focus acquisition here"
        )

    # Find largest segment
    largest = max(segments.items(), key=lambda x: x[1]["size"]) if segments else None
    if largest:
        recommendations.append(
            f"VOLUME PLAY: '{largest[0]}' is largest segment ({largest[1]['size']:,} potential customers)"
        )

    # Find easiest to acquire
    easy_segments = [s for s, d in segments.items() if d["acquisition_difficulty"] == "EASY"]
    if easy_segments:
        recommendations.append(
            f"QUICK WINS: Focus on {', '.join(easy_segments)} - marked as easy acquisition"
        )

    return recommendations
