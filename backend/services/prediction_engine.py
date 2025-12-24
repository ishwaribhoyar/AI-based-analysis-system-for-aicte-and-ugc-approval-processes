"""
5-Year Prediction Engine using Linear Regression.
Statistical forecasting without ML libraries.
"""

import numpy as np
from typing import List, Dict, Optional, Tuple
from schemas.analytics import YearMetric, MetricPrediction


def linear_regression(x: np.ndarray, y: np.ndarray) -> Tuple[float, float]:
    """
    Simple linear regression: y = mx + b
    Returns: (slope, intercept)
    """
    n = len(x)
    if n < 2:
        return 0.0, float(y[0]) if len(y) > 0 else 0.0
    
    sum_x = np.sum(x)
    sum_y = np.sum(y)
    sum_xy = np.sum(x * y)
    sum_x2 = np.sum(x ** 2)
    
    denom = n * sum_x2 - sum_x ** 2
    if abs(denom) < 1e-10:
        return 0.0, sum_y / n
    
    slope = (n * sum_xy - sum_x * sum_y) / denom
    intercept = (sum_y - slope * sum_x) / n
    
    return float(slope), float(intercept)


def calculate_r_squared(y_actual: np.ndarray, y_predicted: np.ndarray) -> float:
    """Calculate R-squared (coefficient of determination)."""
    ss_res = np.sum((y_actual - y_predicted) ** 2)
    ss_tot = np.sum((y_actual - np.mean(y_actual)) ** 2)
    
    if ss_tot < 1e-10:
        return 1.0
    
    r2 = 1 - (ss_res / ss_tot)
    return max(0.0, min(1.0, r2))


def predict_values(historical_values: List[YearMetric], years_to_predict: int = 5) -> Tuple[List[YearMetric], float, str]:
    """
    Predict future values using linear regression.
    Uses actual years for regression, not array indices.
    
    Args:
        historical_values: List of historical data points (should be sorted by year)
        years_to_predict: Number of years to predict
    
    Returns:
        (predicted_values, confidence, trend_direction)
    """
    import re
    
    # Filter valid values and extract years
    valid_data = []
    for v in historical_values:
        if v.value is not None and v.year:
            # Extract year from string (e.g., "2023", "2023-24", "2024")
            year_str = str(v.year)
            match = re.search(r'(\d{4})', year_str)
            if match:
                year_num = int(match.group(1))
                valid_data.append((year_num, v.value))
    
    if len(valid_data) < 3:
        return [], 0.0, "insufficient_data"
    
    # Sort by year to ensure chronological order
    valid_data.sort(key=lambda x: x[0])
    
    # Extract years and values
    years = np.array([d[0] for d in valid_data], dtype=float)
    values = np.array([d[1] for d in valid_data], dtype=float)
    
    # Perform linear regression using actual years
    slope, intercept = linear_regression(years, values)
    
    # Calculate confidence (R-squared)
    y_pred = slope * years + intercept
    confidence = calculate_r_squared(values, y_pred)
    
    # Determine trend based on actual slope per year
    if slope > 1.0:  # More than 1 point per year
        trend = "up"
    elif slope < -1.0:  # More than 1 point decrease per year
        trend = "down"
    else:
        trend = "stable"
    
    # Get last year from sorted data
    last_year = int(years[-1])
    
    # Generate predictions for future years
    predictions = []
    for i in range(1, years_to_predict + 1):
        pred_year = last_year + i
        pred_y = slope * pred_year + intercept
        
        # Clip to valid range (0-100 for KPIs)
        pred_y = max(0.0, min(100.0, pred_y))
        
        predictions.append(YearMetric(year=str(pred_year), value=round(pred_y, 2)))
    
    return predictions, confidence, trend


def generate_explanation(metric_name: str, trend: str, slope: float, historical_avg: float) -> str:
    """Generate human-readable explanation for prediction."""
    display_names = {
        "fsr_score": "Faculty-Student Ratio",
        "infrastructure_score": "Infrastructure",
        "placement_index": "Placement Rate",
        "lab_compliance_index": "Lab Compliance",
        "overall_score": "Overall Performance",
    }
    
    name = display_names.get(metric_name, metric_name)
    
    if trend == "up":
        return f"{name} shows consistent improvement. Projected to continue growing based on {historical_avg:.1f} average historical performance."
    elif trend == "down":
        return f"{name} shows declining trend. Intervention recommended to reverse the {abs(slope):.1f} point annual decrease."
    else:
        return f"{name} remains relatively stable around {historical_avg:.1f}. No significant changes expected."


def predict_all_metrics(
    metrics: Dict[str, List[YearMetric]], 
    years_to_predict: int = 5
) -> Dict[str, MetricPrediction]:
    """
    Generate predictions for all metrics.
    
    Args:
        metrics: Historical KPI data indexed by metric name
        years_to_predict: Number of years to predict
    
    Returns:
        Dictionary of predictions per metric
    """
    display_names = {
        "fsr_score": "FSR Score",
        "infrastructure_score": "Infrastructure Score",
        "placement_index": "Placement Index",
        "lab_compliance_index": "Lab Compliance Index",
        "overall_score": "Overall Score",
    }
    
    forecasts = {}
    
    for metric_name, values in metrics.items():
        # Filter and sort values by year
        valid_data = []
        import re
        for v in values:
            if v.value is not None and v.year:
                year_str = str(v.year)
                match = re.search(r'(\d{4})', year_str)
                if match:
                    year_num = int(match.group(1))
                    valid_data.append((year_num, v.value, v))
        
        if len(valid_data) < 3:
            # Not enough data
            forecasts[metric_name] = MetricPrediction(
                metric_name=metric_name,
                display_name=display_names.get(metric_name, metric_name),
                historical_values=values,
                predicted_values=[],
                trend_direction="insufficient_data",
                confidence=0.0,
                explanation="Not enough historical data (minimum 3 years required)"
            )
            continue
        
        # Sort by year
        valid_data.sort(key=lambda x: x[0])
        sorted_values = [v[2] for v in valid_data]  # Extract YearMetric objects
        
        predictions, confidence, trend = predict_values(sorted_values, years_to_predict)
        
        valid_values = [v[1] for v in valid_data]  # Extract values
        historical_avg = sum(valid_values) / len(valid_values) if valid_values else 0
        
        # Calculate slope for explanation using actual years
        years = np.array([v[0] for v in valid_data], dtype=float)
        values_array = np.array(valid_values, dtype=float)
        slope, _ = linear_regression(years, values_array)
        
        explanation = generate_explanation(metric_name, trend, slope, historical_avg)
        
        forecasts[metric_name] = MetricPrediction(
            metric_name=metric_name,
            display_name=display_names.get(metric_name, metric_name),
            historical_values=sorted_values,  # Use sorted values
            predicted_values=predictions,
            trend_direction=trend,
            confidence=confidence,
            explanation=explanation
        )
    
    return forecasts


def generate_growth_areas(forecasts: Dict[str, MetricPrediction]) -> List[str]:
    """Identify areas showing growth."""
    growth = []
    for name, pred in forecasts.items():
        if pred.trend_direction == "up" and pred.confidence > 0.5:
            growth.append(f"📈 {pred.display_name}: Strong positive trend")
    return growth


def generate_decline_warnings(forecasts: Dict[str, MetricPrediction]) -> List[str]:
    """Identify areas showing decline."""
    warnings = []
    for name, pred in forecasts.items():
        if pred.trend_direction == "down" and pred.confidence > 0.5:
            warnings.append(f"⚠️ {pred.display_name}: Declining trend - action needed")
    return warnings


def generate_recommendations(forecasts: Dict[str, MetricPrediction]) -> List[str]:
    """Generate actionable recommendations."""
    recs = []
    
    for name, pred in forecasts.items():
        if pred.trend_direction == "down":
            if "fsr" in name.lower():
                recs.append("Consider hiring additional faculty to improve FSR")
            elif "infrastructure" in name.lower():
                recs.append("Plan infrastructure upgrades to meet growing demands")
            elif "placement" in name.lower():
                recs.append("Strengthen industry partnerships for better placement rates")
            elif "lab" in name.lower():
                recs.append("Invest in lab equipment upgrades for compliance")
        elif pred.trend_direction == "up":
            if pred.predicted_values:
                last_pred = pred.predicted_values[-1].value
                if last_pred and last_pred >= 90:
                    recs.append(f"Maintain current {pred.display_name} strategies - on track for excellence")
    
    return recs[:5]  # Limit to 5 recommendations
