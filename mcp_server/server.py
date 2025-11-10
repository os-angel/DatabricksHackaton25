"""
BioLabs MCP Server

This server provides 12 business tools for the multi-agent system:
- 4 Simulation tools
- 4 Calculation tools
- 4 Data aggregation tools

Run with: python server.py
"""

from fastmcp import FastMCP
from typing import Dict, Any

# Import tool functions
from tools.simulation_tools import (
    simulate_price_change,
    simulate_campaign_roi,
    simulate_channel_expansion,
    simulate_production_capacity
)
from tools.calculation_tools import (
    calculate_product_margin,
    calculate_inventory_turnover,
    calculate_customer_ltv,
    calculate_break_even
)
from tools.data_tools import (
    get_sales_summary,
    get_inventory_status,
    get_competitor_intel,
    get_customer_segments
)
from config import SERVER_HOST, SERVER_PORT

# Initialize FastMCP server
mcp = FastMCP("BioLabs Business Tools Server")


# ============================================================
# SIMULATION TOOLS (4)
# ============================================================

@mcp.tool()
def simulate_price_change_tool(
    product: str,
    price_change_pct: float,
    duration_days: int = 90
) -> Dict[str, Any]:
    """
    Simulate the impact of a price change on revenue and volume.

    Model price elasticity effects and competitive risks.

    Args:
        product: Product name (Tagatose | Allulose | Trehalose)
        price_change_pct: Price change percentage (-20 to +50)
        duration_days: Simulation duration in days (default: 90)

    Returns:
        Complete simulation results with revenue projections and risk scores
    """
    return simulate_price_change(product, price_change_pct, duration_days)


@mcp.tool()
def simulate_campaign_roi_tool(
    product: str,
    channel: str,
    budget: float,
    target_segment: str
) -> Dict[str, Any]:
    """
    Project ROI for a marketing campaign.

    Calculate expected conversions, revenue, and payback period.

    Args:
        product: Product name (Tagatose | Allulose | Trehalose)
        channel: Marketing channel (social | influencer | demo | events)
        budget: Campaign budget in dollars
        target_segment: Customer segment (diabetic | keto | athlete | health_conscious)

    Returns:
        Campaign ROI projection with conversions and payback timeline
    """
    return simulate_campaign_roi(product, channel, budget, target_segment)


@mcp.tool()
def simulate_channel_expansion_tool(
    product: str,
    channel: str,
    num_locations: int,
    duration_months: int = 12
) -> Dict[str, Any]:
    """
    Forecast results of expanding into new distribution locations.

    Models S-curve adoption and calculates payback period.

    Args:
        product: Product name (Tagatose | Allulose | Trehalose)
        channel: Distribution channel (pharmacy | gym | specialty_grocery | hospital)
        num_locations: Number of new locations to open
        duration_months: Simulation duration in months (default: 12)

    Returns:
        Month-by-month revenue projections, costs, and risk assessment
    """
    return simulate_channel_expansion(product, channel, num_locations, duration_months)


@mcp.tool()
def simulate_production_capacity_tool(
    product: str,
    demand_increase_pct: float,
    months_ahead: int = 6
) -> Dict[str, Any]:
    """
    Assess production capacity constraints for demand scenarios.

    Identifies bottlenecks and CAPEX requirements.

    Args:
        product: Product name (Tagatose | Allulose | Trehalose)
        demand_increase_pct: Expected demand increase percentage
        months_ahead: Planning horizon in months (default: 6)

    Returns:
        Capacity analysis with expansion requirements and timeline
    """
    return simulate_production_capacity(product, demand_increase_pct, months_ahead)


# ============================================================
# CALCULATION TOOLS (4)
# ============================================================

@mcp.tool()
def calculate_product_margin_tool(
    product: str,
    channel: str,
    volume_kg: float
) -> Dict[str, Any]:
    """
    Calculate gross and contribution margins for a product-channel combination.

    Args:
        product: Product name (Tagatose | Allulose | Trehalose)
        channel: Distribution channel (pharmacy | gym | specialty_grocery | hospital)
        volume_kg: Sales volume in kilograms

    Returns:
        Detailed margin analysis with revenue and cost breakdown
    """
    return calculate_product_margin(product, channel, volume_kg)


@mcp.tool()
def calculate_inventory_turnover_tool(
    product: str,
    current_inventory_kg: float,
    daily_sales_kg: float
) -> Dict[str, Any]:
    """
    Calculate inventory turnover metrics and carrying costs.

    Determines if reorder is needed based on days on hand.

    Args:
        product: Product name (Tagatose | Allulose | Trehalose)
        current_inventory_kg: Current inventory level in kg
        daily_sales_kg: Average daily sales in kg

    Returns:
        Turnover ratio, days on hand, carrying costs, and reorder recommendation
    """
    return calculate_inventory_turnover(product, current_inventory_kg, daily_sales_kg)


@mcp.tool()
def calculate_customer_ltv_tool(
    segment: str,
    product: str,
    avg_order_value: float = None,
    purchase_frequency: float = None
) -> Dict[str, Any]:
    """
    Calculate customer lifetime value (LTV) for a segment.

    Models retention and revenue over customer lifespan.

    Args:
        segment: Customer segment (diabetic | keto | athlete | health_conscious)
        product: Primary product (Tagatose | Allulose | Trehalose)
        avg_order_value: Average order value (optional, uses segment default)
        purchase_frequency: Monthly purchase frequency (optional, uses segment default)

    Returns:
        LTV projections for 12 months and lifetime
    """
    return calculate_customer_ltv(segment, product, avg_order_value, purchase_frequency)


@mcp.tool()
def calculate_break_even_tool(
    fixed_costs: float,
    variable_cost_per_unit: float,
    price_per_unit: float
) -> Dict[str, Any]:
    """
    Calculate break-even point in units and revenue.

    Includes time-to-break-even based on growth assumptions.

    Args:
        fixed_costs: Total fixed costs in dollars
        variable_cost_per_unit: Variable cost per unit in dollars
        price_per_unit: Selling price per unit in dollars

    Returns:
        Break-even units, revenue, and months to break-even
    """
    return calculate_break_even(fixed_costs, variable_cost_per_unit, price_per_unit)


# ============================================================
# DATA TOOLS (4)
# ============================================================

@mcp.tool()
def get_sales_summary_tool(
    product: str = None,
    channel: str = None,
    start_date: str = None,
    end_date: str = None
) -> Dict[str, Any]:
    """
    Get aggregated sales data from transactional database.

    Filters by product, channel, and date range.

    Args:
        product: Filter by product (optional, default: all)
        channel: Filter by channel (optional, default: all)
        start_date: Start date YYYY-MM-DD (optional, default: last 90 days)
        end_date: End date YYYY-MM-DD (optional, default: today)

    Returns:
        Sales summary with revenue, units, and growth metrics
    """
    return get_sales_summary(product, channel, start_date, end_date)


@mcp.tool()
def get_inventory_status_tool(
    product: str,
    alert_threshold_days: int = 30
) -> Dict[str, Any]:
    """
    Get current inventory status for a product.

    Checks days on hand against safety stock thresholds.

    Args:
        product: Product name (Tagatose | Allulose | Trehalose)
        alert_threshold_days: Alert if days on hand below this (default: 30)

    Returns:
        Current stock levels, days on hand, status, and reorder recommendation
    """
    return get_inventory_status(product, alert_threshold_days)


@mcp.tool()
def get_competitor_intel_tool(
    competitor: str = None,
    product_category: str = "Sugar Substitute"
) -> Dict[str, Any]:
    """
    Retrieve competitive intelligence data.

    Includes pricing, market share, and recent competitive actions.

    Args:
        competitor: Specific competitor name (optional, default: all)
        product_category: Product category (default: Sugar Substitute)

    Returns:
        Competitor pricing, market share, threat levels, and recent actions
    """
    return get_competitor_intel(competitor, product_category)


@mcp.tool()
def get_customer_segments_tool(
    min_ltv: float = None,
    product_affinity: str = None
) -> Dict[str, Any]:
    """
    Get customer segmentation data with targeting recommendations.

    Filters by minimum LTV or product affinity.

    Args:
        min_ltv: Minimum lifetime value filter (optional)
        product_affinity: Filter by product (optional)

    Returns:
        Segment details with size, LTV, characteristics, and targeting recommendations
    """
    return get_customer_segments(min_ltv, product_affinity)


# ============================================================
# SERVER INFO
# ============================================================

@mcp.tool()
def get_server_info() -> Dict[str, Any]:
    """
    Get information about the MCP server and available tools.

    Returns:
        Server metadata and tool categories
    """
    return {
        "server_name": "BioLabs Business Tools Server",
        "version": "1.0.0",
        "description": "Provides 12 business tools for multi-agent system",
        "categories": {
            "simulation": 4,
            "calculation": 4,
            "data": 4
        },
        "tools": {
            "simulation": [
                "simulate_price_change_tool",
                "simulate_campaign_roi_tool",
                "simulate_channel_expansion_tool",
                "simulate_production_capacity_tool"
            ],
            "calculation": [
                "calculate_product_margin_tool",
                "calculate_inventory_turnover_tool",
                "calculate_customer_ltv_tool",
                "calculate_break_even_tool"
            ],
            "data": [
                "get_sales_summary_tool",
                "get_inventory_status_tool",
                "get_competitor_intel_tool",
                "get_customer_segments_tool"
            ]
        },
        "products": ["Tagatose", "Allulose", "Trehalose"],
        "channels": ["pharmacy", "specialty_grocery", "gym", "hospital"],
        "segments": ["diabetic", "keto", "athlete", "health_conscious"]
    }


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║                                                          ║
    ║          BIOLABS MCP SERVER                              ║
    ║          Business Tools for Multi-Agent System           ║
    ║                                                          ║
    ╚══════════════════════════════════════════════════════════╝

    Server: {host}:{port}
    Tools: 12 (4 simulation + 4 calculation + 4 data)

    Available tools:
    ----------------
    SIMULATION:
      • simulate_price_change_tool
      • simulate_campaign_roi_tool
      • simulate_channel_expansion_tool
      • simulate_production_capacity_tool

    CALCULATION:
      • calculate_product_margin_tool
      • calculate_inventory_turnover_tool
      • calculate_customer_ltv_tool
      • calculate_break_even_tool

    DATA:
      • get_sales_summary_tool
      • get_inventory_status_tool
      • get_competitor_intel_tool
      • get_customer_segments_tool

    Starting server...
    """.format(host=SERVER_HOST, port=SERVER_PORT))

    # Run server
    mcp.run(host=SERVER_HOST, port=SERVER_PORT)
