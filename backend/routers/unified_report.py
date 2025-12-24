"""
Unified Report API Router.
Generates combined AICTE + UGC evaluation reports for mixed-mode batches.
"""

import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

from fastapi import APIRouter, HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel

from config.database import get_db, close_db, Block, Batch
from utils.cache import get_cached_payload, set_cached_payload
from routers.dashboard import get_dashboard_data
from services.approval_classifier import classify_approval, normalize_classification
from services.approval_requirements import check_approval_requirements

router = APIRouter()
logger = logging.getLogger(__name__)


class KPISummary(BaseModel):
    name: str
    value: Optional[float]
    status: str  # "good", "warning", "critical"


class RegulatorSummary(BaseModel):
    regulator: str  # "AICTE" or "UGC"
    overall_score: Optional[float]
    kpis: List[KPISummary]
    sufficiency_percentage: float
    compliance_flags_count: int
    missing_documents: List[str]


class UnifiedObservation(BaseModel):
    category: str
    observation: str
    severity: str


class UnifiedReportResponse(BaseModel):
    batch_id: str
    institution_name: Optional[str]
    generated_at: str
    classification: Dict[str, Any]
    
    # Institution Profile
    institution_profile: Dict[str, Any]
    
    # Regulator Summaries
    aicte_summary: Optional[RegulatorSummary]
    ugc_summary: Optional[RegulatorSummary]
    
    # Unified Analysis
    unified_observations: List[UnifiedObservation]
    
    # Final Scores
    consolidated_kpi_score: float
    approval_readiness_score: float
    final_recommendation: str
    
    # Evidence-based document sections (NO hardcoded lists)
    present_documents: List[Dict[str, Any]]  # Documents with evidence
    missing_documents: List[Dict[str, Any]]  # Expected but not found
    unknown_documents: List[Dict[str, Any]]  # Could not determine

    # Flattened view of all missing/unknown documents (for UI convenience)
    all_missing_documents: List[str] = []


def _get_kpi_status(value: Optional[float]) -> str:
    if value is None:
        return "warning"
    if value >= 80:
        return "good"
    if value >= 50:
        return "warning"
    return "critical"


def _generate_observations(dashboard: Any, classification: Dict) -> List[UnifiedObservation]:
    """Generate unified observations from dashboard data."""
    observations = []
    
    # Sufficiency observation
    if dashboard.sufficiency.percentage < 100:
        observations.append(UnifiedObservation(
            category="Sufficiency",
            observation=f"Document sufficiency is {dashboard.sufficiency.percentage:.1f}%. Missing blocks: {', '.join(dashboard.sufficiency.missing_blocks[:3])}",
            severity="warning" if dashboard.sufficiency.percentage >= 70 else "critical"
        ))
    else:
        observations.append(UnifiedObservation(
            category="Sufficiency",
            observation="All required information blocks are present",
            severity="good"
        ))
    
    # Compliance observations from flags
    for flag in dashboard.compliance_flags[:5]:
        observations.append(UnifiedObservation(
            category="Compliance",
            observation=f"{flag.title}: {flag.reason}",
            severity=flag.severity
        ))
    
    # KPI observations
    for kpi in dashboard.kpi_cards:
        if kpi.value is not None:
            if kpi.value < 50:
                observations.append(UnifiedObservation(
                    category="Performance",
                    observation=f"{kpi.name} is below threshold at {kpi.value:.1f}",
                    severity="critical"
                ))
            elif kpi.value >= 90:
                observations.append(UnifiedObservation(
                    category="Performance",
                    observation=f"{kpi.name} is excellent at {kpi.value:.1f}",
                    severity="good"
                ))
    
    # Classification observation
    observations.append(UnifiedObservation(
        category="Classification",
        observation=f"Detected as {classification['category'].upper()} {classification['subtype'].upper()} application",
        severity="good"
    ))
    
    return observations


@router.get("/unified-report/{batch_id}", response_model=UnifiedReportResponse)
def get_unified_report(batch_id: str):
    """Generate unified AICTE + UGC evaluation report."""
    # First, try cache – unified reports are expensive but mostly static
    cached = get_cached_payload("unified_report", batch_id)
    if cached:
        return cached

    db = get_db()
    try:
        # Get batch
        batch = db.query(Batch).filter(Batch.id == batch_id).first()
        if not batch:
            raise HTTPException(status_code=404, detail="Batch not found")
        
        # Get dashboard data
        dashboard = get_dashboard_data(batch_id)
        
        # Build full text from blocks for classification
        blocks = db.query(Block).filter(Block.batch_id == batch_id).all()
        full_text = ""
        blocks_dict: Dict[str, Dict[str, Any]] = {}
        
        for block in blocks:
            blocks_dict[block.block_type] = {
                "data": block.data or {},
                "confidence": block.confidence or 0,
                "evidence_snippet": block.evidence_snippet or "",
            }
            if block.data:
                for key, val in block.data.items():
                    if isinstance(val, str):
                        full_text += f" {val}"
        
        # Classify - now returns a dict
        classification_raw = classify_approval(full_text)
        
        # Normalize to ensure it's a dict
        classification = normalize_classification(classification_raw)
        
        # Ensure classification is a dict
        if not isinstance(classification, dict):
            logger.warning(f"⚠️  Classification normalization failed in unified report")
            classification = {
                "category": batch.mode or "aicte",
                "subtype": "unknown",
                "confidence": 0.0,
                "signals": []
            }
        
        # Build AICTE summary
        aicte_kpis = []
        aicte_overall = None
        for kpi in dashboard.kpi_cards:
            if "AICTE" in kpi.name or kpi.name in ["FSR Score", "Infrastructure Score", "Placement Index", "Lab Compliance Index"]:
                aicte_kpis.append(KPISummary(
                    name=kpi.name,
                    value=kpi.value,
                    status=_get_kpi_status(kpi.value)
                ))
                if "Overall" in kpi.name:
                    aicte_overall = kpi.value
        
        # Build UGC summary (use same KPIs for demo, in real would be different)
        ugc_kpis = []
        for kpi in dashboard.kpi_cards:
            ugc_kpis.append(KPISummary(
                name=kpi.name,
                value=kpi.value,
                status=_get_kpi_status(kpi.value)
            ))
        
        # Evaluate approval readiness using evidence-based check
        readiness_result = check_approval_requirements(batch_id)
        
        # Extract missing document keys (evidence-driven, no hardcoded lists)
        missing_doc_keys = [doc["key"] for doc in readiness_result.get("missing_documents", [])]
        
        # Build summaries
        aicte_summary = RegulatorSummary(
            regulator="AICTE",
            overall_score=aicte_overall or dashboard.kpis.get("overall_score"),
            kpis=aicte_kpis if aicte_kpis else [KPISummary(name=k.name, value=k.value, status=_get_kpi_status(k.value)) for k in dashboard.kpi_cards],
            sufficiency_percentage=dashboard.sufficiency.percentage,
            compliance_flags_count=len([f for f in dashboard.compliance_flags if f.severity in ["high", "medium"]]),
            missing_documents=missing_doc_keys[:5]  # Only evidence-based missing docs
        )
        
        ugc_summary = None
        if classification["category"] in ["ugc", "mixed"]:
            ugc_summary = RegulatorSummary(
                regulator="UGC",
                overall_score=dashboard.kpis.get("overall_score"),
                kpis=ugc_kpis,
                sufficiency_percentage=dashboard.sufficiency.percentage,
                compliance_flags_count=len(dashboard.compliance_flags),
                missing_documents=missing_doc_keys[:5]  # Only evidence-based missing docs
            )
        
        # Institution profile
        institution_profile = {
            "name": dashboard.institution_name or "Institution Name Not Available",
            "mode": batch.mode.upper(),
            "total_documents": dashboard.total_documents,
            "processed_documents": dashboard.processed_documents,
            "blocks_extracted": len([b for b in dashboard.block_cards if b.is_present]),
            "total_blocks": len(dashboard.block_cards),
        }
        
        # Generate observations
        observations = _generate_observations(dashboard, classification)
        
        # Calculate consolidated score
        valid_values = [k.value for k in dashboard.kpi_cards if k.value is not None]
        consolidated_score = sum(valid_values) / len(valid_values) if valid_values else 0
        
        # Final recommendation - use normalized readiness_score key from approval_requirements
        readiness_score = readiness_result.get("readiness_score") or readiness_result.get("approval_readiness_score", 0)
        if readiness_score >= 80 and dashboard.sufficiency.percentage >= 80:
            final_recommendation = "READY FOR APPROVAL - Institution meets minimum requirements"
        elif readiness_score >= 60:
            final_recommendation = "CONDITIONAL APPROVAL - Requires submission of missing documents"
        else:
            final_recommendation = "NOT ELIGIBLE - Significant gaps in documentation and compliance"
        
        # Build flattened missing document labels for UI
        missing_labels: List[str] = []
        for doc in readiness_result.get("missing_documents", []):
            label = doc.get("description") or doc.get("key")
            if label:
                missing_labels.append(str(label))
        for doc in readiness_result.get("unknown_documents", []):
            label = doc.get("description") or doc.get("key")
            if label:
                missing_labels.append(str(label))

        response = UnifiedReportResponse(
            batch_id=batch_id,
            institution_name=dashboard.institution_name,
            generated_at=datetime.now().isoformat(),
            classification=classification,
            institution_profile=institution_profile,
            aicte_summary=aicte_summary,
            ugc_summary=ugc_summary,
            unified_observations=observations,
            consolidated_kpi_score=round(consolidated_score, 2),
            approval_readiness_score=readiness_score,
            final_recommendation=final_recommendation,
            # Evidence-driven document lists (NO hardcoded defaults)
            present_documents=readiness_result.get("present_documents", []),
            missing_documents=readiness_result.get("missing_documents", []),
            unknown_documents=readiness_result.get("unknown_documents", []),
            all_missing_documents=missing_labels,
        )

        # Cache the serialized response for faster subsequent loads (15 min TTL)
        set_cached_payload("unified_report", batch_id, jsonable_encoder(response), ttl_seconds=900)

        return response
    except Exception as e:
        db.rollback()
        import traceback
        error_detail = f"Error generating unified report: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_detail)
        raise HTTPException(status_code=500, detail=f"Failed to generate unified report: {str(e)}")
    finally:
        close_db(db)
