"""
Calculation Tools for BioLabs MCP Server

These tools provide business calculations:
5. calculate_product_margin
6. calculate_inventory_turnover
7. calculate_customer_ltv
8. calculate_break_even
"""

from typing import Dict, Any
from ..config import PRODUCTS, CHANNELS, CUSTOMER_SEGMENTS


def calculate_product_margin(
    product: str,
    channel: str,
    volume_kg: float
) -> Dict[str, Any]:
    """
    Calculate margins for a product-channel combination.

    Args:
        product: Product name
        channel: Distribution channel
        volume_kg: Sales volume in kg

    Returns:
        Margin calculations
    """
    if product not in PRODUCTS:
        return {"error": f"Invalid product: {product}"}

    if channel not in CHANNELS:
        return {"error": f"Invalid channel: {channel}"}

    product_info = PRODUCTS[product]
    channel_info = CHANNELS[channel]

    # Pricing
    retail_price = product_info["retail_price_per_kg"]
    channel_margin = channel_info["margin"]
    wholesale_price = retail_price * (1 - channel_margin)  # BioLabs sells at wholesale

    # Costs
    cogs = product_info["cogs_per_kg"]
    packaging_cost = cogs * 0.08  # 8% of COGS
    distribution_cost = cogs * 0.05  # 5% of COGS
    total_variable_cost = cogs + packaging_cost + distribution_cost

    # Revenue
    revenue = volume_kg * wholesale_price

    # Gross margin (revenue - COGS)
    gross_profit = revenue - (volume_kg * cogs)
    gross_margin_pct = (gross_profit / revenue) * 100 if revenue > 0 else 0

    # Contribution margin (revenue - all variable costs)
    contribution_profit = revenue - (volume_kg * total_variable_cost)
    contribution_margin_pct = (contribution_profit / revenue) * 100 if revenue > 0 else 0

    # Margin dollars
    gross_margin_dollars = gross_profit
    contribution_margin_dollars = contribution_profit

    return {
        "product": product,
        "channel": channel,
        "volume_kg": volume_kg,
        "pricing": {
            "retail_price_per_kg": retail_price,
            "wholesale_price_per_kg": round(wholesale_price, 2),
            "channel_margin_pct": round(channel_margin * 100, 1)
        },
        "costs": {
            "cogs_per_kg": cogs,
            "packaging_cost_per_kg": round(packaging_cost, 2),
            "distribution_cost_per_kg": round(distribution_cost, 2),
            "total_variable_cost_per_kg": round(total_variable_cost, 2)
        },
        "margins": {
            "gross_margin_pct": round(gross_margin_pct, 2),
            "contribution_margin_pct": round(contribution_margin_pct, 2),
            "gross_margin_dollars": round(gross_margin_dollars, 2),
            "contribution_margin_dollars": round(contribution_margin_dollars, 2)
        },
        "revenue": round(revenue, 2),
        "assessment": _assess_margins(gross_margin_pct, contribution_margin_pct)
    }


def calculate_inventory_turnover(
    product: str,
    current_inventory_kg: float,
    daily_sales_kg: float
) -> Dict[str, Any]:
    """
    Calculate inventory turnover metrics.

    Args:
        product: Product name
        current_inventory_kg: Current inventory level
        daily_sales_kg: Average daily sales

    Returns:
        Inventory turnover analysis
    """
    if product not in PRODUCTS:
        return {"error": f"Invalid product: {product}"}

    if daily_sales_kg <= 0:
        return {"error": "Daily sales must be positive"}

    product_info = PRODUCTS[product]

    # Days on hand
    days_on_hand = current_inventory_kg / daily_sales_kg if daily_sales_kg > 0 else float('inf')

    # Turnover ratio (annual)
    turnover_ratio = 365 / days_on_hand if days_on_hand > 0 else 0

    # Carrying cost (15% annual inventory carrying cost)
    cogs = product_info["cogs_per_kg"]
    inventory_value = current_inventory_kg * cogs
    annual_carrying_cost = inventory_value * 0.15
    carrying_cost_daily = annual_carrying_cost / 365

    # Target inventory (30 days for fast movers, 45 for others)
    target_days = 30 if product == "Allulose" else 45
    target_inventory_kg = daily_sales_kg * target_days

    # Status
    if days_on_hand < target_days * 0.5:
        status = "CRITICAL"
        reorder_recommended = True
    elif days_on_hand < target_days:
        status = "WARNING"
        reorder_recommended = True
    elif days_on_hand <= target_days * 1.5:
        status = "HEALTHY"
        reorder_recommended = False
    else:
        status = "OVERSTOCKED"
        reorder_recommended = False

    return {
        "product": product,
        "inventory_metrics": {
            "current_inventory_kg": current_inventory_kg,
            "daily_sales_kg": daily_sales_kg,
            "days_on_hand": round(days_on_hand, 1),
            "turnover_ratio": round(turnover_ratio, 2),
            "inventory_value": round(inventory_value, 2)
        },
        "carrying_costs": {
            "annual_carrying_cost": round(annual_carrying_cost, 2),
            "daily_carrying_cost": round(carrying_cost_daily, 2)
        },
        "targets": {
            "target_days_on_hand": target_days,
            "target_inventory_kg": round(target_inventory_kg, 2)
        },
        "status": status,
        "reorder_recommended": reorder_recommended,
        "recommendation": _get_inventory_recommendation(status, days_on_hand, target_days)
    }


def calculate_customer_ltv(
    segment: str,
    product: str,
    avg_order_value: float = None,
    purchase_frequency: float = None
) -> Dict[str, Any]:
    """
    Calculate customer lifetime value (LTV).

    Args:
        segment: Customer segment
        product: Primary product
        avg_order_value: Average order value (optional, uses segment default)
        purchase_frequency: Monthly purchase frequency (optional, uses segment default)

    Returns:
        LTV calculations
    """
    if segment not in CUSTOMER_SEGMENTS:
        return {"error": f"Invalid segment: {segment}"}

    if product not in PRODUCTS:
        return {"error": f"Invalid product: {product}"}

    segment_info = CUSTOMER_SEGMENTS[segment]

    # Use provided values or defaults from segment
    avg_order = avg_order_value if avg_order_value is not None else segment_info.get("avg_order_value", 35.0)
    freq = purchase_frequency if purchase_frequency is not None else segment_info.get("purchase_frequency", 2.0)
    retention_rate = segment_info["retention_rate"]

    # Calculate LTV components
    monthly_revenue = avg_order * freq
    yearly_revenue = monthly_revenue * 12

    # Average customer lifespan (months) = 1 / churn rate
    churn_rate = 1 - retention_rate
    avg_lifespan_months = 1 / churn_rate if churn_rate > 0 else float('inf')

    # LTV = (Avg Monthly Revenue × Retention Rate) / Churn Rate
    ltv_12_months = monthly_revenue * 12 * retention_rate
    ltv_lifetime = monthly_revenue * avg_lifespan_months if avg_lifespan_months != float('inf') else segment_info["avg_ltv"]

    # Discount LTV to present value (using discount rate)
    discount_rate_monthly = 0.15 / 12  # 15% annual
    discounted_ltv = ltv_lifetime * (1 / (1 + discount_rate_monthly))

    return {
        "segment": segment,
        "product": product,
        "inputs": {
            "avg_order_value": round(avg_order, 2),
            "purchase_frequency_per_month": freq,
            "retention_rate": retention_rate,
            "churn_rate": round(churn_rate, 3)
        },
        "ltv": {
            "ltv_12_months": round(ltv_12_months, 2),
            "ltv_lifetime": round(ltv_lifetime, 2) if ltv_lifetime != float('inf') else "Infinite",
            "discounted_ltv": round(discounted_ltv, 2) if discounted_ltv != float('inf') else "Infinite"
        },
        "metrics": {
            "monthly_revenue_per_customer": round(monthly_revenue, 2),
            "yearly_revenue_per_customer": round(yearly_revenue, 2),
            "avg_customer_lifespan_months": round(avg_lifespan_months, 1) if avg_lifespan_months != float('inf') else "Infinite"
        },
        "segment_size": segment_info.get("size", "Unknown"),
        "assessment": _assess_ltv(ltv_lifetime, monthly_revenue)
    }


def calculate_break_even(
    fixed_costs: float,
    variable_cost_per_unit: float,
    price_per_unit: float
) -> Dict[str, Any]:
    """
    Calculate break-even analysis.

    Args:
        fixed_costs: Total fixed costs ($)
        variable_cost_per_unit: Variable cost per unit ($)
        price_per_unit: Selling price per unit ($)

    Returns:
        Break-even calculations
    """
    if price_per_unit <= variable_cost_per_unit:
        return {"error": "Price must be greater than variable cost per unit"}

    # Contribution margin per unit
    contribution_margin = price_per_unit - variable_cost_per_unit
    contribution_margin_pct = (contribution_margin / price_per_unit) * 100

    # Break-even point (units)
    break_even_units = fixed_costs / contribution_margin if contribution_margin > 0 else float('inf')

    # Break-even revenue
    break_even_revenue = break_even_units * price_per_unit if break_even_units != float('inf') else float('inf')

    # Months to break even (assuming growth rate)
    # Assume linear growth from 0 to monthly capacity
    assumed_monthly_capacity = 1000  # units/month
    monthly_ramp_up = assumed_monthly_capacity / 6  # Ramp up over 6 months

    months_to_break_even = 0
    cumulative_units = 0
    for month in range(1, 37):  # Max 36 months
        monthly_units = min(month * monthly_ramp_up, assumed_monthly_capacity)
        cumulative_units += monthly_units
        if cumulative_units >= break_even_units:
            months_to_break_even = month
            break
    else:
        months_to_break_even = float('inf')

    # Safety margin (how much above break-even we need)
    safety_margin_units = break_even_units * 0.20 if break_even_units != float('inf') else 0  # 20% buffer
    target_units = break_even_units + safety_margin_units if break_even_units != float('inf') else 0

    return {
        "inputs": {
            "fixed_costs": fixed_costs,
            "variable_cost_per_unit": variable_cost_per_unit,
            "price_per_unit": price_per_unit
        },
        "contribution_margin": {
            "per_unit": round(contribution_margin, 2),
            "percentage": round(contribution_margin_pct, 2)
        },
        "break_even": {
            "units": round(break_even_units, 0) if break_even_units != float('inf') else "Not achievable",
            "revenue": round(break_even_revenue, 2) if break_even_revenue != float('inf') else "Not achievable",
            "months_to_break_even": round(months_to_break_even, 1) if months_to_break_even != float('inf') else "Not achievable"
        },
        "targets": {
            "safety_margin_units": round(safety_margin_units, 0),
            "target_units_with_margin": round(target_units, 0)
        },
        "assessment": _assess_break_even(months_to_break_even, contribution_margin_pct)
    }


# Helper functions for assessments
def _assess_margins(gross_margin: float, contribution_margin: float) -> str:
    if gross_margin >= 40 and contribution_margin >= 30:
        return "EXCELLENT: Margins exceed targets"
    elif gross_margin >= 35 and contribution_margin >= 25:
        return "GOOD: Margins meet minimum thresholds"
    elif gross_margin >= 30:
        return "ACCEPTABLE: Margins below target, monitor closely"
    else:
        return "POOR: Margins insufficient, review pricing or costs"


def _get_inventory_recommendation(status: str, days_on_hand: float, target: int) -> str:
    if status == "CRITICAL":
        return f"URGENT: Reorder immediately. Only {days_on_hand:.0f} days of inventory remaining."
    elif status == "WARNING":
        return f"REORDER SOON: Below target of {target} days. Place order within 7 days."
    elif status == "HEALTHY":
        return f"NO ACTION NEEDED: Inventory at healthy levels."
    else:  # OVERSTOCKED
        excess_days = days_on_hand - target
        return f"OVERSTOCKED: {excess_days:.0f} days excess inventory. Reduce orders or promote sales."


def _assess_ltv(ltv: float, monthly_revenue: float) -> str:
    if ltv == float('inf'):
        return "EXCELLENT: High retention leads to exceptional lifetime value"
    elif ltv > 500:
        return "EXCELLENT: Very high lifetime value, prioritize retention"
    elif ltv > 300:
        return "GOOD: Strong lifetime value, justify acquisition investments"
    elif ltv > 150:
        return "ACCEPTABLE: Moderate lifetime value, watch CAC carefully"
    else:
        return "POOR: Low lifetime value, must optimize pricing or retention"


def _assess_break_even(months: float, margin_pct: float) -> str:
    if months == float('inf'):
        return "NOT VIABLE: Cannot break even with current unit economics"
    elif months <= 12 and margin_pct >= 40:
        return "EXCELLENT: Quick payback with strong margins"
    elif months <= 18 and margin_pct >= 30:
        return "GOOD: Acceptable payback period"
    elif months <= 24:
        return "MARGINAL: Long payback, monitor carefully"
    else:
        return "RISKY: Very long payback period, reconsider economics"
