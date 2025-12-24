"""
Analytics API router.
Endpoints for multi-year trends and predictions.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from schemas.analytics import (
    MultiYearAnalyticsResponse,
    PredictionRequest,
    PredictionResponse,
)
from services.multi_year_analytics import (
    aggregate_multi_year_data,
    build_trend_summary,
    find_best_worst_years,
    generate_insights,
    normalize_year,
)
from services.prediction_engine import (
    predict_all_metrics,
    generate_growth_areas,
    generate_decline_warnings,
    generate_recommendations,
)

router = APIRouter()


@router.get("/analytics/multi_year", response_model=MultiYearAnalyticsResponse)
def get_multi_year_analytics(
    batch_ids: str = Query(..., description="Comma-separated batch IDs"),
    years: int = Query(default=5, ge=1, le=10, description="Number of years to analyze"),
    metrics: Optional[str] = Query(default=None, description="Comma-separated metrics to include")
):
    """
    Get multi-year analytics for selected batches.
    Aggregates KPIs across years for trend analysis.
    """
    ids = [bid.strip() for bid in batch_ids.split(",") if bid.strip()]
    
    if len(ids) < 1:
        raise HTTPException(status_code=400, detail="Provide at least one batch_id")
    
    # Aggregate data
    all_metrics, available_years, institution_name = aggregate_multi_year_data(ids)
    
    if not available_years:
        raise HTTPException(status_code=404, detail="No data available for the specified batches")
    
    # Limit to requested years
    if len(available_years) > years:
        # Take most recent years
        sorted_years = sorted(available_years, key=normalize_year, reverse=True)
        available_years = sorted(sorted_years[:years], key=normalize_year)
        
        # Filter metrics to these years
        for kpi in all_metrics:
            all_metrics[kpi] = [v for v in all_metrics[kpi] if v.year in available_years]
    
    # Filter metrics if specified
    if metrics:
        requested_metrics = [m.strip() for m in metrics.split(",")]
        all_metrics = {k: v for k, v in all_metrics.items() if k in requested_metrics}
    
    # Build trend summary
    trend_summary = build_trend_summary(all_metrics)
    
    # Find best/worst years
    best_year, worst_year = find_best_worst_years(all_metrics)
    
    # Generate insights
    insights = generate_insights(trend_summary)
    
    return MultiYearAnalyticsResponse(
        institution_name=institution_name,
        batch_count=len(ids),
        years_requested=years,
        available_years=available_years,
        metrics=all_metrics,
        trend_summary=trend_summary,
        best_year=best_year,
        worst_year=worst_year,
        insights=insights,
    )


@router.post("/analytics/predict", response_model=PredictionResponse)
def predict_future_kpis(request: PredictionRequest):
    """
    Predict future KPI values using linear regression.
    Requires minimum 3 years of historical data.
    """
    if not request.batch_ids:
        raise HTTPException(status_code=400, detail="Provide at least one batch_id")
    
    # Aggregate historical data
    all_metrics, available_years, institution_name = aggregate_multi_year_data(request.batch_ids)
    
    if len(available_years) < 3:
        return PredictionResponse(
            institution_name=institution_name,
            historical_years=available_years,
            prediction_years=[],
            forecasts={},
            has_enough_data=False,
            error_message=f"Not enough historical data for prediction. Found {len(available_years)} year(s), minimum 3 required."
        )
    
    # Filter to requested metrics
    filtered_metrics = {k: v for k, v in all_metrics.items() if k in request.metrics}
    
    if not filtered_metrics:
        filtered_metrics = all_metrics
    
    # Generate predictions
    forecasts = predict_all_metrics(filtered_metrics, request.years_to_predict)
    
    # Generate prediction years
    last_year = normalize_year(available_years[-1]) if available_years else 2024
    prediction_years = [str(last_year + i + 1) for i in range(request.years_to_predict)]
    
    return PredictionResponse(
        institution_name=institution_name,
        historical_years=available_years,
        prediction_years=prediction_years,
        forecasts=forecasts,
        growth_areas=generate_growth_areas(forecasts),
        decline_warnings=generate_decline_warnings(forecasts),
        recommendations=generate_recommendations(forecasts),
        has_enough_data=True,
        error_message=None,
    )


@router.get("/analytics/summary")
def get_analytics_summary(batch_id: str = Query(..., description="Single batch ID")):
    """
    Get a quick analytics summary for a single batch.
    Used for dashboard widgets.
    """
    all_metrics, available_years, institution_name = aggregate_multi_year_data([batch_id])
    
    if not available_years:
        raise HTTPException(status_code=404, detail="No data available for this batch")
    
    trend_summary = build_trend_summary(all_metrics)
    insights = generate_insights(trend_summary)
    
    return {
        "institution_name": institution_name,
        "years_available": len(available_years),
        "latest_year": available_years[-1] if available_years else None,
        "overall_trend": trend_summary.get("overall_score", {}).trend_direction if "overall_score" in trend_summary else "unknown",
        "insights": insights[:3],
    }
