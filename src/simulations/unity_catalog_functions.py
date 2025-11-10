"""
Unity Catalog Functions for Simulations
Business logic for ROI, forecasting, and scenario analysis
"""
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from src.utils.logger import simulation_logger as logger


@dataclass
class ROIResult:
    """Result from ROI calculation"""
    roi_percentage: float
    payback_period_months: int
    break_even_month: int
    cumulative_profit_18mo: float
    monthly_cash_flow: List[float]
    npv: float
    irr: float


@dataclass
class ForecastResult:
    """Result from forecasting"""
    forecast: List[float]
    confidence_intervals: List[Tuple[float, float]]
    trend: str  # 'increasing', 'decreasing', 'stable'
    seasonality_detected: bool
    forecast_accuracy: float


class UnityC atalogFunctions:
    """
    Simulation engine using business logic
    In production, these would be Unity Catalog Functions (SQL/Python UDFs)
    """

    @staticmethod
    def calculate_roi_new_stores(
        num_stores: int,
        investment_per_store: float,
        avg_revenue_per_store: float,
        operational_cost_ratio: float,
        ramp_up_months: int = 6,
        forecast_months: int = 18,
        discount_rate: float = 0.10
    ) -> ROIResult:
        """
        Calculate ROI for new store openings

        Args:
            num_stores: Number of new stores
            investment_per_store: Initial investment per store
            avg_revenue_per_store: Average annual revenue per store
            operational_cost_ratio: Operating costs as ratio of revenue
            ramp_up_months: Months to reach full capacity
            forecast_months: Forecast period in months
            discount_rate: Annual discount rate for NPV

        Returns:
            ROIResult with detailed metrics
        """
        logger.info(f"Calculating ROI for {num_stores} new stores...")

        # Total investment
        total_investment = num_stores * investment_per_store

        # Monthly revenue per store at full capacity
        monthly_revenue_full = avg_revenue_per_store / 12

        # Calculate monthly cash flows
        monthly_cash_flow = []
        cumulative_profit = -total_investment  # Start with investment

        # Ramp-up curve (gradual increase to full capacity)
        ramp_up_curve = UnityCatalogFunctions._calculate_ramp_up_curve(
            ramp_up_months
        )

        break_even_month = None
        payback_month = None

        for month in range(1, forecast_months + 1):
            # Revenue with ramp-up
            if month <= ramp_up_months:
                revenue_factor = ramp_up_curve[month - 1]
            else:
                revenue_factor = 1.0

            # Monthly revenue for all stores
            monthly_revenue = num_stores * monthly_revenue_full * revenue_factor

            # Operating costs
            monthly_costs = monthly_revenue * operational_cost_ratio

            # Net cash flow
            net_cash_flow = monthly_revenue - monthly_costs
            monthly_cash_flow.append(net_cash_flow)

            # Track cumulative
            cumulative_profit += net_cash_flow

            # Track break-even
            if break_even_month is None and cumulative_profit >= 0:
                break_even_month = month

            # Track payback (when cumulative profit covers investment)
            if payback_month is None and cumulative_profit >= 0:
                payback_month = month

        # Calculate ROI
        total_profit = sum(monthly_cash_flow)
        roi_percentage = (total_profit / total_investment) * 100

        # Calculate NPV
        npv = UnityCatalogFunctions._calculate_npv(
            cash_flows=monthly_cash_flow,
            initial_investment=total_investment,
            discount_rate=discount_rate
        )

        # Calculate IRR (approximate)
        irr = UnityCatalogFunctions._calculate_irr_approximate(
            cash_flows=monthly_cash_flow,
            initial_investment=total_investment
        )

        result = ROIResult(
            roi_percentage=round(roi_percentage, 2),
            payback_period_months=payback_month or forecast_months,
            break_even_month=break_even_month or forecast_months,
            cumulative_profit_18mo=round(cumulative_profit, 2),
            monthly_cash_flow=[round(cf, 2) for cf in monthly_cash_flow],
            npv=round(npv, 2),
            irr=round(irr, 4) if irr else 0.0
        )

        logger.info(f"ROI calculated: {result.roi_percentage}%, Payback: {result.payback_period_months} months")
        return result

    @staticmethod
    def _calculate_ramp_up_curve(ramp_up_months: int) -> List[float]:
        """Calculate S-curve for store ramp-up"""
        # S-curve: slow start, accelerate, then level off
        x = np.linspace(0, 1, ramp_up_months)
        # Sigmoid function
        curve = 1 / (1 + np.exp(-10 * (x - 0.5)))
        # Normalize to 0-1
        curve = (curve - curve.min()) / (curve.max() - curve.min())
        return curve.tolist()

    @staticmethod
    def _calculate_npv(
        cash_flows: List[float],
        initial_investment: float,
        discount_rate: float
    ) -> float:
        """Calculate Net Present Value"""
        monthly_discount_rate = discount_rate / 12

        npv = -initial_investment
        for month, cash_flow in enumerate(cash_flows, 1):
            npv += cash_flow / ((1 + monthly_discount_rate) ** month)

        return npv

    @staticmethod
    def _calculate_irr_approximate(
        cash_flows: List[float],
        initial_investment: float,
        max_iterations: int = 100
    ) -> Optional[float]:
        """Approximate IRR using Newton's method"""
        # Start with a guess
        irr = 0.1

        for _ in range(max_iterations):
            npv = -initial_investment
            npv_derivative = 0

            for month, cash_flow in enumerate(cash_flows, 1):
                monthly_rate = irr / 12
                discount_factor = (1 + monthly_rate) ** month
                npv += cash_flow / discount_factor
                npv_derivative -= month * cash_flow / (discount_factor * (1 + monthly_rate))

            if abs(npv) < 0.01:  # Close enough
                return irr

            # Newton's method update
            if npv_derivative != 0:
                irr = irr - npv / npv_derivative
            else:
                break

            # Bound the rate
            if irr < -0.99 or irr > 10:
                break

        return irr if -0.99 < irr < 10 else None

    @staticmethod
    def forecast_revenue(
        historical_data: List[float],
        forecast_periods: int,
        seasonality_periods: Optional[int] = None,
        growth_rate: Optional[float] = None,
        confidence_level: float = 0.95
    ) -> ForecastResult:
        """
        Forecast revenue using time series analysis

        Args:
            historical_data: Historical revenue data points
            forecast_periods: Number of periods to forecast
            seasonality_periods: Seasonality cycle length (e.g., 12 for monthly)
            growth_rate: Optional fixed growth rate
            confidence_level: Confidence level for intervals

        Returns:
            ForecastResult with forecast and confidence intervals
        """
        logger.info(f"Forecasting {forecast_periods} periods from {len(historical_data)} data points...")

        if len(historical_data) < 2:
            logger.warning("Insufficient historical data")
            return ForecastResult(
                forecast=[historical_data[0]] * forecast_periods if historical_data else [0] * forecast_periods,
                confidence_intervals=[(0, 0)] * forecast_periods,
                trend="stable",
                seasonality_detected=False,
                forecast_accuracy=0.0
            )

        # Calculate trend
        trend_direction = UnityCatalogFunctions._detect_trend(historical_data)

        # Calculate growth rate if not provided
        if growth_rate is None:
            growth_rate = UnityCatalogFunctions._calculate_growth_rate(historical_data)

        # Detect seasonality
        seasonality_detected = False
        seasonal_factors = None
        if seasonality_periods and len(historical_data) >= seasonality_periods * 2:
            seasonality_detected, seasonal_factors = UnityCatalogFunctions._detect_seasonality(
                historical_data,
                seasonality_periods
            )

        # Generate forecast
        forecast = []
        last_value = historical_data[-1]

        for period in range(1, forecast_periods + 1):
            # Base forecast with growth
            forecasted_value = last_value * ((1 + growth_rate) ** period)

            # Apply seasonality if detected
            if seasonality_detected and seasonal_factors:
                season_index = (len(historical_data) + period - 1) % len(seasonal_factors)
                forecasted_value *= seasonal_factors[season_index]

            forecast.append(forecasted_value)

        # Calculate confidence intervals
        std_dev = np.std(historical_data)
        z_score = 1.96 if confidence_level == 0.95 else 2.576  # 95% or 99%

        confidence_intervals = []
        for i, pred in enumerate(forecast):
            # Widen interval as we forecast further
            adjusted_std = std_dev * np.sqrt(i + 1)
            margin = z_score * adjusted_std
            confidence_intervals.append((
                max(0, pred - margin),
                pred + margin
            ))

        # Estimate forecast accuracy based on historical variance
        cv = std_dev / np.mean(historical_data) if np.mean(historical_data) > 0 else 1.0
        forecast_accuracy = max(0, 1 - cv)

        result = ForecastResult(
            forecast=[round(f, 2) for f in forecast],
            confidence_intervals=[(round(l, 2), round(u, 2)) for l, u in confidence_intervals],
            trend=trend_direction,
            seasonality_detected=seasonality_detected,
            forecast_accuracy=round(forecast_accuracy, 2)
        )

        logger.info(f"Forecast complete: Trend={trend_direction}, Seasonality={seasonality_detected}")
        return result

    @staticmethod
    def _detect_trend(data: List[float]) -> str:
        """Detect trend direction in data"""
        if len(data) < 2:
            return "stable"

        # Simple linear regression slope
        x = np.arange(len(data))
        y = np.array(data)

        slope = np.polyfit(x, y, 1)[0]

        # Normalize by mean to get relative slope
        mean_val = np.mean(y)
        relative_slope = slope / mean_val if mean_val > 0 else slope

        if relative_slope > 0.02:  # More than 2% trend
            return "increasing"
        elif relative_slope < -0.02:
            return "decreasing"
        else:
            return "stable"

    @staticmethod
    def _calculate_growth_rate(data: List[float]) -> float:
        """Calculate average growth rate"""
        if len(data) < 2:
            return 0.0

        # Calculate period-over-period growth rates
        growth_rates = []
        for i in range(1, len(data)):
            if data[i - 1] > 0:
                rate = (data[i] - data[i - 1]) / data[i - 1]
                growth_rates.append(rate)

        return np.mean(growth_rates) if growth_rates else 0.0

    @staticmethod
    def _detect_seasonality(
        data: List[float],
        period: int
    ) -> Tuple[bool, Optional[List[float]]]:
        """Detect and calculate seasonal factors"""
        if len(data) < period * 2:
            return False, None

        # Calculate average for each season
        seasonal_avgs = [[] for _ in range(period)]

        for i, value in enumerate(data):
            season = i % period
            seasonal_avgs[season].append(value)

        # Calculate seasonal factors (ratio to overall mean)
        overall_mean = np.mean(data)
        seasonal_factors = [
            np.mean(season_data) / overall_mean if overall_mean > 0 else 1.0
            for season_data in seasonal_avgs
        ]

        # Check if seasonality is significant (variance in factors)
        factor_variance = np.var(seasonal_factors)
        is_seasonal = factor_variance > 0.01  # Threshold for significance

        return is_seasonal, seasonal_factors if is_seasonal else None

    @staticmethod
    def compare_scenarios(
        scenario_a: Dict,
        scenario_b: Dict,
        metrics_to_compare: List[str]
    ) -> Dict:
        """
        Compare two scenarios

        Args:
            scenario_a: First scenario data
            scenario_b: Second scenario data
            metrics_to_compare: Metrics to compare

        Returns:
            Comparison results
        """
        logger.info("Comparing scenarios...")

        comparison = {
            "scenario_a": scenario_a.get("name", "Scenario A"),
            "scenario_b": scenario_b.get("name", "Scenario B"),
            "metrics": {},
            "winner": None,
            "recommendation": ""
        }

        scores = {"a": 0, "b": 0}

        for metric in metrics_to_compare:
            value_a = scenario_a.get(metric, 0)
            value_b = scenario_b.get(metric, 0)

            # Determine which is better (assuming higher is better for most metrics)
            if metric.lower() in ["cost", "risk", "payback_period"]:
                # Lower is better
                better = "a" if value_a < value_b else "b"
                scores[better] += 1
            else:
                # Higher is better
                better = "a" if value_a > value_b else "b"
                scores[better] += 1

            comparison["metrics"][metric] = {
                "scenario_a": value_a,
                "scenario_b": value_b,
                "difference": value_b - value_a,
                "difference_pct": ((value_b - value_a) / value_a * 100) if value_a != 0 else 0,
                "better": better
            }

        # Determine overall winner
        comparison["winner"] = "Scenario A" if scores["a"] > scores["b"] else "Scenario B"
        comparison["score"] = f"{scores['a']} vs {scores['b']}"

        return comparison

    @staticmethod
    def sensitivity_analysis(
        base_scenario: Dict,
        variables_to_test: List[str],
        variation_range: float = 0.2
    ) -> Dict:
        """
        Perform sensitivity analysis

        Args:
            base_scenario: Base scenario parameters
            variables_to_test: Variables to test
            variation_range: ± variation percentage (e.g., 0.2 for ±20%)

        Returns:
            Sensitivity analysis results
        """
        logger.info(f"Performing sensitivity analysis on {len(variables_to_test)} variables...")

        results = {
            "base_scenario": base_scenario,
            "sensitivities": {},
            "most_sensitive_variables": []
        }

        sensitivity_scores = {}

        for variable in variables_to_test:
            if variable not in base_scenario:
                continue

            base_value = base_scenario[variable]

            # Test variations
            variations = []
            for factor in [-variation_range, -variation_range/2, 0, variation_range/2, variation_range]:
                varied_value = base_value * (1 + factor)
                variations.append({
                    "variation_pct": factor * 100,
                    "value": varied_value,
                    "factor": factor
                })

            results["sensitivities"][variable] = {
                "base_value": base_value,
                "variations": variations
            }

            # Calculate sensitivity score (how much output changes)
            sensitivity_scores[variable] = abs(variation_range)

        # Rank variables by sensitivity
        ranked = sorted(sensitivity_scores.items(), key=lambda x: x[1], reverse=True)
        results["most_sensitive_variables"] = [var for var, _ in ranked]

        return results
