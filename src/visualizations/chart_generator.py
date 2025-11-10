"""
Chart Generator using Plotly
Creates executive-level visualizations
"""
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Optional, Any
import pandas as pd

from src.utils.logger import ui_logger as logger


class ChartGenerator:
    """
    Generates charts for different types of data and queries
    """

    # Corporate color scheme
    COLORS = {
        "primary": "#1f77b4",
        "secondary": "#ff7f0e",
        "success": "#2ca02c",
        "warning": "#d62728",
        "info": "#9467bd",
        "neutral": "#7f7f7f"
    }

    @staticmethod
    def create_chart(
        data: Dict[str, Any],
        chart_type: str = "auto",
        title: Optional[str] = None,
        **kwargs
    ) -> Optional[go.Figure]:
        """
        Create a chart based on data and type

        Args:
            data: Data to visualize
            chart_type: Type of chart (auto, line, bar, pie, waterfall, etc.)
            title: Chart title
            **kwargs: Additional chart parameters

        Returns:
            Plotly figure or None
        """
        logger.info(f"Creating {chart_type} chart...")

        try:
            if chart_type == "auto":
                chart_type = ChartGenerator._determine_chart_type(data)

            # Dispatch to specific chart method
            if chart_type == "line":
                return ChartGenerator.create_line_chart(data, title, **kwargs)
            elif chart_type == "bar":
                return ChartGenerator.create_bar_chart(data, title, **kwargs)
            elif chart_type == "pie":
                return ChartGenerator.create_pie_chart(data, title, **kwargs)
            elif chart_type == "waterfall":
                return ChartGenerator.create_waterfall_chart(data, title, **kwargs)
            elif chart_type == "comparison":
                return ChartGenerator.create_comparison_chart(data, title, **kwargs)
            elif chart_type == "roi_timeline":
                return ChartGenerator.create_roi_timeline(data, title, **kwargs)
            elif chart_type == "sensitivity":
                return ChartGenerator.create_sensitivity_chart(data, title, **kwargs)
            else:
                logger.warning(f"Unknown chart type: {chart_type}")
                return None

        except Exception as e:
            logger.error(f"Error creating chart: {e}", exc_info=True)
            return None

    @staticmethod
    def _determine_chart_type(data: Dict) -> str:
        """Automatically determine the best chart type"""
        # Check for simulation data
        if "monthly_cash_flow" in data or "roi_percentage" in data:
            return "roi_timeline"

        # Check for comparison data
        if "scenario_a" in data and "scenario_b" in data:
            return "comparison"

        # Check for time series
        if "forecast" in data or any(k.startswith("month") for k in data.keys()):
            return "line"

        # Default to bar chart
        return "bar"

    @staticmethod
    def create_line_chart(
        data: Dict,
        title: Optional[str] = None,
        xlabel: str = "Period",
        ylabel: str = "Value"
    ) -> go.Figure:
        """Create a line chart"""
        fig = go.Figure()

        # Handle different data formats
        if "forecast" in data:
            # Forecasting data
            forecast = data["forecast"]
            x = list(range(1, len(forecast) + 1))

            fig.add_trace(go.Scatter(
                x=x,
                y=forecast,
                mode='lines+markers',
                name='Forecast',
                line=dict(color=ChartGenerator.COLORS["primary"], width=2)
            ))

            # Add confidence intervals if available
            if "confidence_intervals" in data:
                ci = data["confidence_intervals"]
                lower = [c[0] for c in ci]
                upper = [c[1] for c in ci]

                fig.add_trace(go.Scatter(
                    x=x + x[::-1],
                    y=upper + lower[::-1],
                    fill='toself',
                    fillcolor='rgba(31, 119, 180, 0.2)',
                    line=dict(color='rgba(255,255,255,0)'),
                    name='Confidence Interval',
                    showlegend=True
                ))

            # Add historical data if available
            if "historical_data" in data:
                hist = data["historical_data"]
                hist_x = list(range(-len(hist) + 1, 1))

                fig.add_trace(go.Scatter(
                    x=hist_x,
                    y=hist,
                    mode='lines+markers',
                    name='Historical',
                    line=dict(color=ChartGenerator.COLORS["neutral"], width=2, dash='dot')
                ))

        else:
            # Generic time series
            for key, values in data.items():
                if isinstance(values, (list, tuple)):
                    x = list(range(1, len(values) + 1))
                    fig.add_trace(go.Scatter(
                        x=x,
                        y=values,
                        mode='lines+markers',
                        name=key.replace('_', ' ').title()
                    ))

        fig.update_layout(
            title=title or "Trend Analysis",
            xaxis_title=xlabel,
            yaxis_title=ylabel,
            template="plotly_white",
            hovermode='x unified'
        )

        return fig

    @staticmethod
    def create_bar_chart(
        data: Dict,
        title: Optional[str] = None,
        orientation: str = "v"
    ) -> go.Figure:
        """Create a bar chart"""
        fig = go.Figure()

        # Convert data to lists
        if isinstance(data, dict):
            categories = list(data.keys())
            values = list(data.values())

            fig.add_trace(go.Bar(
                x=categories if orientation == "v" else values,
                y=values if orientation == "v" else categories,
                orientation=orientation,
                marker_color=ChartGenerator.COLORS["primary"]
            ))

        fig.update_layout(
            title=title or "Comparison",
            template="plotly_white",
            showlegend=False
        )

        return fig

    @staticmethod
    def create_pie_chart(
        data: Dict,
        title: Optional[str] = None
    ) -> go.Figure:
        """Create a pie chart"""
        fig = go.Figure()

        labels = list(data.keys())
        values = list(data.values())

        fig.add_trace(go.Pie(
            labels=labels,
            values=values,
            marker=dict(colors=list(ChartGenerator.COLORS.values()))
        ))

        fig.update_layout(
            title=title or "Distribution",
            template="plotly_white"
        )

        return fig

    @staticmethod
    def create_waterfall_chart(
        data: Dict,
        title: Optional[str] = None
    ) -> go.Figure:
        """Create a waterfall chart (useful for P&L, cash flow)"""
        # Extract categories and values
        if "categories" in data and "values" in data:
            categories = data["categories"]
            values = data["values"]
        else:
            categories = list(data.keys())
            values = list(data.values())

        # Determine measure types
        measures = []
        for i, val in enumerate(values):
            if i == 0:
                measures.append("absolute")
            elif i == len(values) - 1:
                measures.append("total")
            else:
                measures.append("relative")

        fig = go.Figure(go.Waterfall(
            name="",
            orientation="v",
            measure=measures,
            x=categories,
            y=values,
            connector={"line": {"color": "rgb(63, 63, 63)"}},
        ))

        fig.update_layout(
            title=title or "Waterfall Analysis",
            template="plotly_white",
            showlegend=False
        )

        return fig

    @staticmethod
    def create_comparison_chart(
        data: Dict,
        title: Optional[str] = None
    ) -> go.Figure:
        """Create a comparison chart for scenarios"""
        fig = go.Figure()

        # Extract scenarios
        scenario_a_name = data.get("scenario_a", "Scenario A")
        scenario_b_name = data.get("scenario_b", "Scenario B")

        metrics = data.get("metrics", {})

        # Prepare data
        metric_names = []
        scenario_a_values = []
        scenario_b_values = []

        for metric_name, metric_data in metrics.items():
            metric_names.append(metric_name.replace('_', ' ').title())
            scenario_a_values.append(metric_data.get("scenario_a", 0))
            scenario_b_values.append(metric_data.get("scenario_b", 0))

        # Create grouped bar chart
        fig.add_trace(go.Bar(
            name=scenario_a_name,
            x=metric_names,
            y=scenario_a_values,
            marker_color=ChartGenerator.COLORS["primary"]
        ))

        fig.add_trace(go.Bar(
            name=scenario_b_name,
            x=metric_names,
            y=scenario_b_values,
            marker_color=ChartGenerator.COLORS["secondary"]
        ))

        fig.update_layout(
            title=title or "Scenario Comparison",
            barmode='group',
            template="plotly_white",
            xaxis_title="Metrics",
            yaxis_title="Value"
        )

        return fig

    @staticmethod
    def create_roi_timeline(
        data: Dict,
        title: Optional[str] = None
    ) -> go.Figure:
        """Create ROI timeline chart showing cumulative profit"""
        monthly_cash_flow = data.get("monthly_cash_flow", [])
        initial_investment = data.get("initial_investment", 0)

        if not monthly_cash_flow:
            return ChartGenerator.create_line_chart(data, title)

        # Calculate cumulative profit
        cumulative = [-initial_investment]
        for cf in monthly_cash_flow:
            cumulative.append(cumulative[-1] + cf)

        months = list(range(0, len(cumulative)))

        fig = go.Figure()

        # Add cumulative profit line
        fig.add_trace(go.Scatter(
            x=months,
            y=cumulative,
            mode='lines+markers',
            name='Cumulative Profit',
            line=dict(color=ChartGenerator.COLORS["primary"], width=3),
            fill='tozeroy',
            fillcolor='rgba(31, 119, 180, 0.1)'
        ))

        # Add break-even line
        fig.add_hline(
            y=0,
            line_dash="dash",
            line_color=ChartGenerator.COLORS["success"],
            annotation_text="Break-Even",
            annotation_position="right"
        )

        # Mark break-even point
        break_even_month = data.get("break_even_month")
        if break_even_month and break_even_month < len(cumulative):
            fig.add_trace(go.Scatter(
                x=[break_even_month],
                y=[cumulative[break_even_month]],
                mode='markers',
                name='Break-Even Point',
                marker=dict(size=15, color=ChartGenerator.COLORS["success"]),
                showlegend=True
            ))

        fig.update_layout(
            title=title or f"ROI Timeline - {data.get('roi_percentage', 0)}% ROI",
            xaxis_title="Month",
            yaxis_title="Cumulative Profit ($)",
            template="plotly_white",
            hovermode='x unified'
        )

        return fig

    @staticmethod
    def create_sensitivity_chart(
        data: Dict,
        title: Optional[str] = None
    ) -> go.Figure:
        """Create tornado chart for sensitivity analysis"""
        sensitivities = data.get("sensitivities", {})

        if not sensitivities:
            return None

        # Prepare data for tornado chart
        variables = []
        low_impacts = []
        high_impacts = []

        for var_name, var_data in sensitivities.items():
            base_value = var_data.get("base_value", 0)
            variations = var_data.get("variations", [])

            if len(variations) >= 2:
                # Get low and high variation impacts
                low_var = variations[0]  # -20%
                high_var = variations[-1]  # +20%

                variables.append(var_name.replace('_', ' ').title())
                low_impacts.append(low_var.get("value", 0) - base_value)
                high_impacts.append(high_var.get("value", 0) - base_value)

        # Create tornado chart
        fig = go.Figure()

        fig.add_trace(go.Bar(
            name='Low (-20%)',
            y=variables,
            x=low_impacts,
            orientation='h',
            marker_color=ChartGenerator.COLORS["warning"]
        ))

        fig.add_trace(go.Bar(
            name='High (+20%)',
            y=variables,
            x=high_impacts,
            orientation='h',
            marker_color=ChartGenerator.COLORS["success"]
        ))

        fig.update_layout(
            title=title or "Sensitivity Analysis",
            barmode='overlay',
            template="plotly_white",
            xaxis_title="Impact on Outcome",
            yaxis_title="Variables"
        )

        return fig

    @staticmethod
    def create_kpi_card(
        value: float,
        title: str,
        subtitle: Optional[str] = None,
        trend: Optional[str] = None,
        format_as: str = "number"
    ) -> str:
        """
        Create HTML for a KPI card

        Args:
            value: KPI value
            title: KPI title
            subtitle: Optional subtitle
            trend: Optional trend indicator ('+15%', '-5%', etc.)
            format_as: How to format the value (number, currency, percent)

        Returns:
            HTML string
        """
        # Format value
        if format_as == "currency":
            formatted_value = f"${value:,.0f}"
        elif format_as == "percent":
            formatted_value = f"{value:.1f}%"
        else:
            formatted_value = f"{value:,.0f}"

        # Determine trend color
        trend_color = "green" if trend and trend.startswith("+") else "red" if trend and trend.startswith("-") else "gray"

        html = f"""
        <div style="
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 20px;
            margin: 10px;
            background-color: #f9f9f9;
            text-align: center;
        ">
            <h3 style="margin: 0; color: #333;">{title}</h3>
            <h1 style="margin: 10px 0; color: #1f77b4;">{formatted_value}</h1>
            {f'<p style="margin: 5px 0; color: {trend_color}; font-weight: bold;">{trend}</p>' if trend else ''}
            {f'<p style="margin: 5px 0; color: #666;">{subtitle}</p>' if subtitle else ''}
        </div>
        """

        return html
