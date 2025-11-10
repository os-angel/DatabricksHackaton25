"""
Simulation Tools for BioLabs MCP Server

These tools provide business simulation capabilities:
1. simulate_price_change
2. simulate_campaign_roi
3. simulate_channel_expansion
4. simulate_production_capacity
"""

import numpy as np
from typing import Dict, Any, List
from ..config import PRODUCTS, CHANNELS, MARKETING_CHANNELS, CUSTOMER_SEGMENTS, PRODUCTION_CAPACITY


def simulate_price_change(
    product: str,
    price_change_pct: float,
    duration_days: int = 90
) -> Dict[str, Any]:
    """
    Simulate the impact of a price change on revenue and volume.

    Args:
        product: Product name (Tagatose, Allulose, Trehalose)
        price_change_pct: Price change percentage (-20 to +50)
        duration_days: Simulation duration in days

    Returns:
        Dictionary with simulation results
    """
    if product not in PRODUCTS:
        return {"error": f"Invalid product: {product}"}

    if not -20 <= price_change_pct <= 50:
        return {"error": "Price change must be between -20% and +50%"}

    product_info = PRODUCTS[product]
    base_price = product_info["retail_price_per_kg"]
    elasticity = product_info["elasticity"]

    # Calculate new price
    new_price = base_price * (1 + price_change_pct / 100)
    price_change_ratio = (new_price - base_price) / base_price

    # Volume change based on elasticity
    volume_change_pct = elasticity * price_change_ratio * 100

    # Assume baseline monthly volume (can be fetched from database)
    baseline_monthly_volume_kg = 10000  # Example baseline

    # Calculate projected volume
    projected_volume_kg = baseline_monthly_volume_kg * (1 + volume_change_pct / 100)
    projected_volume_kg = max(0, projected_volume_kg)  # Can't be negative

    # Revenue calculations
    baseline_revenue = baseline_monthly_volume_kg * base_price
    projected_revenue = projected_volume_kg * new_price

    revenue_delta = projected_revenue - baseline_revenue
    revenue_delta_pct = (revenue_delta / baseline_revenue) * 100 if baseline_revenue > 0 else 0

    # Margin impact
    cogs = product_info["cogs_per_kg"]
    baseline_margin = ((base_price - cogs) / base_price) * 100
    new_margin = ((new_price - cogs) / new_price) * 100
    margin_impact = new_margin - baseline_margin

    # Competitive risk score (0-100)
    # Higher price increase = higher competitive risk
    competitive_risk_score = min(100, max(0, 50 + price_change_pct * 2))

    # Confidence interval
    confidence_interval = {
        "low": projected_revenue * 0.85,
        "high": projected_revenue * 1.15
    }

    return {
        "product": product,
        "price_change_pct": price_change_pct,
        "duration_days": duration_days,
        "baseline": {
            "price_per_kg": base_price,
            "monthly_volume_kg": baseline_monthly_volume_kg,
            "monthly_revenue": baseline_revenue,
            "gross_margin_pct": baseline_margin
        },
        "projected": {
            "price_per_kg": new_price,
            "monthly_volume_kg": round(projected_volume_kg, 2),
            "monthly_revenue": round(projected_revenue, 2),
            "gross_margin_pct": round(new_margin, 2)
        },
        "deltas": {
            "revenue_delta": round(revenue_delta, 2),
            "revenue_delta_pct": round(revenue_delta_pct, 2),
            "volume_delta_pct": round(volume_change_pct, 2),
            "margin_impact_pct": round(margin_impact, 2)
        },
        "competitive_risk_score": round(competitive_risk_score, 1),
        "confidence_interval": {
            "low": round(confidence_interval["low"], 2),
            "high": round(confidence_interval["high"], 2)
        },
        "recommendation": _get_price_recommendation(revenue_delta_pct, competitive_risk_score)
    }


def simulate_campaign_roi(
    product: str,
    channel: str,
    budget: float,
    target_segment: str
) -> Dict[str, Any]:
    """
    Simulate ROI for a marketing campaign.

    Args:
        product: Product name
        channel: Marketing channel (social, influencer, demo, events)
        budget: Campaign budget ($)
        target_segment: Customer segment (diabetic, keto, athlete, health_conscious)

    Returns:
        Campaign ROI projection
    """
    if product not in PRODUCTS:
        return {"error": f"Invalid product: {product}"}

    if channel not in MARKETING_CHANNELS:
        return {"error": f"Invalid channel: {channel}. Choose from: {list(MARKETING_CHANNELS.keys())}"}

    if target_segment not in CUSTOMER_SEGMENTS:
        return {"error": f"Invalid segment: {target_segment}"}

    # Get channel metrics
    channel_info = MARKETING_CHANNELS[channel]
    base_cac = channel_info["cac"]
    conversion_rate = channel_info["conversion_rate"]

    # Add randomness to CAC (real campaigns vary)
    actual_cac = base_cac * np.random.uniform(0.85, 1.15)

    # Calculate expected conversions
    impressions = int(budget * np.random.uniform(15, 25))
    clicks = int(impressions * np.random.uniform(0.02, 0.08))
    conversions = int(clicks * conversion_rate)

    # Alternatively, calculate from CAC
    conversions_from_cac = int(budget / actual_cac)

    # Use average
    expected_conversions = int((conversions + conversions_from_cac) / 2)

    # Get segment LTV
    segment_info = CUSTOMER_SEGMENTS[target_segment]
    ltv = segment_info["avg_ltv"]
    retention_rate = segment_info["retention_rate"]

    # Calculate revenue
    first_year_revenue = expected_conversions * ltv * 0.6  # 60% of LTV in year 1
    total_lifetime_revenue = expected_conversions * ltv

    # ROI calculations
    roi_first_year = ((first_year_revenue - budget) / budget) * 100 if budget > 0 else 0
    roi_lifetime = ((total_lifetime_revenue - budget) / budget) * 100 if budget > 0 else 0

    # Payback period (months)
    monthly_revenue_per_customer = ltv * 0.05  # Assume 5% of LTV per month
    monthly_revenue = expected_conversions * monthly_revenue_per_customer
    payback_period_months = budget / monthly_revenue if monthly_revenue > 0 else float('inf')

    return {
        "product": product,
        "channel": channel,
        "target_segment": target_segment,
        "budget": budget,
        "metrics": {
            "expected_impressions": impressions,
            "expected_clicks": clicks,
            "expected_conversions": expected_conversions,
            "actual_cac": round(actual_cac, 2),
            "customer_ltv": ltv
        },
        "revenue": {
            "first_year": round(first_year_revenue, 2),
            "lifetime": round(total_lifetime_revenue, 2)
        },
        "roi": {
            "first_year_pct": round(roi_first_year, 2),
            "lifetime_pct": round(roi_lifetime, 2)
        },
        "payback_period_months": round(payback_period_months, 1) if payback_period_months != float('inf') else "N/A",
        "recommendation": _get_campaign_recommendation(roi_first_year, payback_period_months)
    }


def simulate_channel_expansion(
    product: str,
    channel: str,
    num_locations: int,
    duration_months: int = 12
) -> Dict[str, Any]:
    """
    Simulate expansion into new channel locations.

    Args:
        product: Product name
        channel: Distribution channel (pharmacy, gym, specialty_grocery, hospital)
        num_locations: Number of new locations
        duration_months: Simulation duration (months)

    Returns:
        Channel expansion projection
    """
    if product not in PRODUCTS:
        return {"error": f"Invalid product: {product}"}

    if channel not in CHANNELS:
        return {"error": f"Invalid channel: {channel}"}

    product_info = PRODUCTS[product]
    channel_info = CHANNELS[channel]

    # Revenue per location (based on average volume)
    avg_volume_kg = channel_info["avg_volume_kg"]
    wholesale_price = product_info["retail_price_per_kg"] * (1 - channel_info["margin"])
    monthly_revenue_per_location = avg_volume_kg * 30 * wholesale_price

    # Adoption curve (S-curve)
    # Month 1: 30%, Month 3: 60%, Month 6: 90%, Month 12: 100%
    adoption_rates = {
        1: 0.30, 2: 0.45, 3: 0.60, 4: 0.70,
        5: 0.80, 6: 0.90, 7: 0.93, 8: 0.96,
        9: 0.98, 10: 0.99, 11: 0.995, 12: 1.0
    }

    # Project revenue by month
    monthly_projections = []
    cumulative_revenue = 0

    for month in range(1, min(duration_months + 1, 13)):
        adoption_rate = adoption_rates.get(month, 1.0)
        monthly_revenue = num_locations * monthly_revenue_per_location * adoption_rate
        cumulative_revenue += monthly_revenue

        monthly_projections.append({
            "month": month,
            "adoption_rate": round(adoption_rate * 100, 1),
            "monthly_revenue": round(monthly_revenue, 2),
            "cumulative_revenue": round(cumulative_revenue, 2)
        })

    # Costs
    cac_per_location = 500  # Customer acquisition cost per location
    total_cac = num_locations * cac_per_location

    cogs = product_info["cogs_per_kg"]
    total_volume_kg = num_locations * avg_volume_kg * 30 * duration_months
    total_cost = total_volume_kg * cogs + total_cac

    # Calculate metrics
    total_revenue = cumulative_revenue
    net_contribution = total_revenue - total_cost
    margin_pct = (net_contribution / total_revenue) * 100 if total_revenue > 0 else 0

    # Payback period
    for i, proj in enumerate(monthly_projections, 1):
        if proj["cumulative_revenue"] >= total_cac:
            payback_period = i
            break
    else:
        payback_period = float('inf')

    # Risk score (0-100)
    # More locations = higher execution risk
    risk_score = min(100, 30 + (num_locations / 10) * 20)

    return {
        "product": product,
        "channel": channel,
        "num_locations": num_locations,
        "duration_months": duration_months,
        "monthly_projections": monthly_projections,
        "summary": {
            "total_revenue": round(total_revenue, 2),
            "total_costs": round(total_cost, 2),
            "net_contribution": round(net_contribution, 2),
            "margin_pct": round(margin_pct, 2),
            "payback_period_months": payback_period if payback_period != float('inf') else "N/A"
        },
        "risk_score": round(risk_score, 1),
        "recommendation": _get_expansion_recommendation(net_contribution, payback_period, risk_score)
    }


def simulate_production_capacity(
    product: str,
    demand_increase_pct: float,
    months_ahead: int = 6
) -> Dict[str, Any]:
    """
    Assess production capacity constraints.

    Args:
        product: Product name
        demand_increase_pct: Expected demand increase (%)
        months_ahead: Planning horizon (months)

    Returns:
        Capacity analysis
    """
    if product not in PRODUCTS:
        return {"error": f"Invalid product: {product}"}

    if product not in PRODUCTION_CAPACITY:
        return {"error": f"No capacity data for: {product}"}

    current_capacity_kg = PRODUCTION_CAPACITY[product]
    current_utilization = 0.75  # Assume 75% current utilization

    current_production_kg = current_capacity_kg * current_utilization
    projected_demand_kg = current_production_kg * (1 + demand_increase_pct / 100)

    # Check if capacity is sufficient
    capacity_sufficient = projected_demand_kg <= current_capacity_kg
    shortfall_kg = max(0, projected_demand_kg - current_capacity_kg)

    # CAPEX required for expansion
    capex_per_kg_capacity = 50  # $50 per kg/month capacity
    capex_required = shortfall_kg * capex_per_kg_capacity if not capacity_sufficient else 0

    # Timeline to expand (months)
    timeline_to_expand = 0
    if not capacity_sufficient:
        if shortfall_kg < current_capacity_kg * 0.20:
            timeline_to_expand = 3  # Minor expansion
        elif shortfall_kg < current_capacity_kg * 0.50:
            timeline_to_expand = 6  # Moderate expansion
        else:
            timeline_to_expand = 12  # Major expansion

    # Bottleneck analysis
    bottlenecks = []
    if not capacity_sufficient:
        if shortfall_kg > current_capacity_kg * 0.30:
            bottlenecks.append("Production line capacity")
        if product == "Allulose":
            bottlenecks.append("Specialized fermentation equipment")
        if demand_increase_pct > 50:
            bottlenecks.append("Raw material supply chain")

    return {
        "product": product,
        "demand_increase_pct": demand_increase_pct,
        "months_ahead": months_ahead,
        "capacity_analysis": {
            "current_capacity_kg_per_month": current_capacity_kg,
            "current_production_kg_per_month": round(current_production_kg, 2),
            "current_utilization_pct": round(current_utilization * 100, 1),
            "projected_demand_kg_per_month": round(projected_demand_kg, 2),
            "capacity_sufficient": capacity_sufficient,
            "shortfall_kg_per_month": round(shortfall_kg, 2)
        },
        "expansion_requirements": {
            "capex_required": round(capex_required, 2),
            "timeline_months": timeline_to_expand,
            "bottlenecks": bottlenecks
        },
        "recommendation": _get_capacity_recommendation(capacity_sufficient, timeline_to_expand, capex_required)
    }


# Helper functions for recommendations
def _get_price_recommendation(revenue_delta_pct: float, risk_score: float) -> str:
    if revenue_delta_pct > 5 and risk_score < 60:
        return "PROCEED: Positive revenue impact with manageable competitive risk"
    elif revenue_delta_pct > 0 and risk_score < 70:
        return "CAUTIOUS: Slight revenue gain but monitor competition closely"
    elif revenue_delta_pct < -5:
        return "DO NOT PROCEED: Significant revenue loss expected"
    else:
        return "NEUTRAL: Minimal impact, consider other factors"


def _get_campaign_recommendation(roi_first_year: float, payback_months: float) -> str:
    if roi_first_year > 50 and payback_months < 12:
        return "STRONGLY RECOMMEND: Excellent ROI and quick payback"
    elif roi_first_year > 20 and payback_months < 18:
        return "RECOMMEND: Good ROI, acceptable payback period"
    elif roi_first_year > 0:
        return "CONSIDER: Positive ROI but may not meet targets"
    else:
        return "DO NOT RECOMMEND: Negative first-year ROI"


def _get_expansion_recommendation(net_contribution: float, payback_months: float, risk_score: float) -> str:
    if net_contribution > 0 and payback_months < 12 and risk_score < 50:
        return "STRONGLY RECOMMEND: Profitable with low risk"
    elif net_contribution > 0 and payback_months < 18 and risk_score < 70:
        return "RECOMMEND: Profitable but manage execution risks"
    elif net_contribution > 0 and risk_score < 60:
        return "CAUTIOUS: Profitable but longer payback or higher risk"
    else:
        return "DO NOT RECOMMEND: Insufficient returns or high risk"


def _get_capacity_recommendation(sufficient: bool, timeline: int, capex: float) -> str:
    if sufficient:
        return "NO ACTION REQUIRED: Sufficient capacity for projected demand"
    elif timeline <= 3 and capex < 100000:
        return "PROCEED: Minor expansion required, manageable investment"
    elif timeline <= 6 and capex < 500000:
        return "PLAN: Moderate expansion needed, start planning now"
    else:
        return "STRATEGIC DECISION: Major capacity investment required, board approval needed"
