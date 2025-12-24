"""
KPI Details API Router.
Returns detailed parameter-level breakdown for each KPI.
NO dummy data - everything from real backend computation.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from services.kpi_detailed import get_kpi_detailed_breakdown
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/details/{batch_id}/{kpi_type}")
def get_kpi_details(batch_id: str, kpi_type: str) -> Dict[str, Any]:
    """
    Get detailed parameter breakdown for a specific KPI.
    
    Args:
        batch_id: Batch ID
        kpi_type: One of 'fsr', 'infrastructure', 'placement', 'lab', 'overall'
    
    Returns:
        Detailed breakdown with parameters, evidence, calculation steps
    """
    valid_types = ["fsr", "infrastructure", "placement", "lab", "overall"]
    kpi_type_lower = kpi_type.lower().strip()
    
    if kpi_type_lower not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid KPI type. Must be one of: {', '.join(valid_types)}"
        )
    
    try:
        result = get_kpi_detailed_breakdown(batch_id, kpi_type_lower)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        import traceback
        logger.error(f"Error getting KPI details: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

