"""
Analytics schemas for multi-year trends and predictions.
"""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field


class YearMetric(BaseModel):
    """A single metric value for a specific year."""
    year: str
    value: Optional[float] = None
    

class MetricTrend(BaseModel):
    """Trend data for a single metric across years."""
    metric_name: str
    display_name: str
    values: List[YearMetric] = Field(default_factory=list)
    average: Optional[float] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    trend_direction: str = "stable"  # "up", "down", "stable"


class MultiYearAnalyticsResponse(BaseModel):
    """Response for multi-year analytics."""
    institution_name: str
    batch_count: int
    years_requested: int
    available_years: List[str] = Field(default_factory=list)
    
    # KPI metrics across years
    metrics: Dict[str, List[YearMetric]] = Field(default_factory=dict)
    
    # Summary statistics
    trend_summary: Dict[str, MetricTrend] = Field(default_factory=dict)
    
    # Best/worst years
    best_year: Optional[str] = None
    worst_year: Optional[str] = None
    
    # Insights
    insights: List[str] = Field(default_factory=list)


class PredictionRequest(BaseModel):
    """Request for 5-year prediction."""
    batch_ids: List[str]
    years_to_predict: int = 5
    metrics: List[str] = Field(default=["fsr_score", "infrastructure_score", "placement_index", "overall_score"])


class MetricPrediction(BaseModel):
    """Predicted values for a single metric."""
    metric_name: str
    display_name: str
    historical_values: List[YearMetric] = Field(default_factory=list)
    predicted_values: List[YearMetric] = Field(default_factory=list)
    trend_direction: str = "stable"
    confidence: float = 0.0  # 0-1
    explanation: str = ""


class PredictionResponse(BaseModel):
    """Response for 5-year prediction."""
    institution_name: str
    historical_years: List[str] = Field(default_factory=list)
    prediction_years: List[str] = Field(default_factory=list)
    
    # Predictions per metric
    forecasts: Dict[str, MetricPrediction] = Field(default_factory=dict)
    
    # Overall insights
    growth_areas: List[str] = Field(default_factory=list)
    decline_warnings: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    
    # Validation
    has_enough_data: bool = True
    error_message: Optional[str] = None
