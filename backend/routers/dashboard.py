"""
Dashboard data router - SQLite version
"""

from fastapi import APIRouter, HTTPException
from schemas.dashboard import (
    DashboardResponse,
    KPICard,
    SufficiencyCard,
    ComplianceFlag,
    TrendDataPoint,
    BlockCard,
    BlockWithData,
    ApprovalClassification,
    ApprovalReadiness,
)
from schemas.kpi_details import KPIDetailsResponse
from config.information_blocks import get_information_blocks, get_block_description
from config.database import get_db, Batch, Block, ComplianceFlag as ComplianceFlagModel, close_db

router = APIRouter()


@router.get("/kpi-details/{batch_id}", response_model=KPIDetailsResponse)
def get_kpi_details_endpoint(batch_id: str):
    """Get detailed KPI breakdown for a batch."""
    from services.kpi_details import get_kpi_details
    try:
        return get_kpi_details(batch_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/trends/{batch_id}")
def get_yearwise_trends(batch_id: str):
    """Get year-wise KPI trends for a batch."""
    from services.yearwise_kpi import process_yearwise_kpis
    
    db = get_db()
    try:
        batch = db.query(Batch).filter(Batch.id == batch_id).first()
        if not batch:
            raise HTTPException(status_code=404, detail="Batch not found")
        
        blocks = db.query(Block).filter(Block.batch_id == batch_id).all()
        block_list = [{"data": b.data or {}} for b in blocks]
        
        result = process_yearwise_kpis(block_list)
        return result
    finally:
        close_db(db)


VALID_KPI_NAMES = ["fsr", "infrastructure", "placement", "placementindex", "lab", "labcompliance", "overall"]

KPI_NORMS = {
    "fsr": "AICTE Handbook 2024: Ideal Faculty-Student Ratio = 1:15",
    "infrastructure": "AICTE Norms: Min Built-up = 10000 sqm, Classrooms = 30, Library = 500 sqm",
    "placement": "Industry Benchmark: Target 80% placement rate, 10 LPA avg package",
    "lab": "AICTE Requirements: Min 5 Computer Labs, 4 Science Labs, 6 Engineering Labs",
    "overall": "Weighted average: FSR(25%) + Infrastructure(25%) + Placement(30%) + Lab(20%)"
}


def _generate_insights(kpi_breakdown, kpi_type: str):
    """Generate human-readable insights for a KPI."""
    insights = []
    
    if kpi_breakdown.final_score >= 80:
        insights.append(f"✅ {kpi_breakdown.kpi_name} is excellent (≥80)")
    elif kpi_breakdown.final_score >= 60:
        insights.append(f"⚠️ {kpi_breakdown.kpi_name} is adequate but has room for improvement")
    else:
        insights.append(f"❌ {kpi_breakdown.kpi_name} needs significant improvement (<60)")
    
    # Check missing parameters
    if kpi_breakdown.missing_parameters:
        insights.append(f"⚠️ Missing data: {', '.join(kpi_breakdown.missing_parameters)}")
    
    # Check low-contributing parameters
    for param in kpi_breakdown.parameters:
        if param.missing:
            continue
        if hasattr(param, 'contribution') and param.contribution is not None:
            if param.score < 50 and param.weight >= 0.2:
                insights.append(f"📉 {param.display_name} is underperforming ({param.score:.0f}%)")
            elif param.score >= 90:
                insights.append(f"📈 {param.display_name} exceeds requirements ({param.score:.0f}%)")
    
    return insights


@router.get("/{batch_id}/kpi-details/{kpi_name}")
def get_single_kpi_details(batch_id: str, kpi_name: str):
    """
    Get detailed breakdown for a specific KPI.
    
    kpi_name: fsr, infrastructure, placement, placementindex, lab, labcompliance, overall
    """
    from services.kpi_details import get_kpi_details
    
    # Normalize kpi_name
    kpi_key = kpi_name.lower().replace("_", "").replace("-", "")
    if kpi_key not in VALID_KPI_NAMES:
        raise HTTPException(status_code=400, detail=f"Invalid KPI name. Valid options: {VALID_KPI_NAMES}")
    
    try:
        full_details = get_kpi_details(batch_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    # Map to correct attribute
    kpi_map = {
        "fsr": full_details.fsr,
        "infrastructure": full_details.infrastructure,
        "placement": full_details.placement,
        "placementindex": full_details.placement,
        "lab": full_details.lab_compliance,
        "labcompliance": full_details.lab_compliance,
        "overall": full_details.overall,
    }
    
    kpi_breakdown = kpi_map.get(kpi_key)
    if not kpi_breakdown:
        raise HTTPException(status_code=404, detail=f"KPI data not available")
    
    # Get evidence from blocks
    db = get_db()
    try:
        blocks = db.query(Block).filter(Block.batch_id == batch_id).all()
        
        # Collect evidence snippets for each parameter
        parameters_with_evidence = []
        for param in kpi_breakdown.parameters:
            param_dict = {
                "name": param.parameter_name,
                "display_name": param.display_name,
                "extracted_value": param.raw_value,
                "norm_value": _get_norm_for_param(param.parameter_name, kpi_key),
                "score_contribution": param.contribution if hasattr(param, 'contribution') else param.score,
                "weight_percent": param.weight * 100,
                "calculation": f"score = min(100, ({param.raw_value} / norm) × 100) = {param.score}" if param.raw_value else "N/A",
                "evidence_snippet": None,
                "evidence_page": None,
                "missing": param.missing,
            }
            
            # Find evidence for this parameter
            for block in blocks:
                if block.evidence_snippet and param.parameter_name in str(block.data):
                    param_dict["evidence_snippet"] = block.evidence_snippet[:200]
                    param_dict["evidence_page"] = block.evidence_page
                    break
            
            parameters_with_evidence.append(param_dict)
        
        # Generate insights
        insights = _generate_insights(kpi_breakdown, kpi_key)
        
        # Generate overall explanation
        explanation = f"{kpi_breakdown.kpi_name} is {kpi_breakdown.final_score:.1f}/100. "
        if kpi_breakdown.missing_parameters:
            explanation += f"Some parameters are missing ({', '.join(kpi_breakdown.missing_parameters)}). "
        if kpi_breakdown.final_score < 60:
            explanation += "Score is below the acceptable threshold of 60. "
        
        return {
            "kpi_name": kpi_breakdown.kpi_name,
            "kpi_key": kpi_breakdown.kpi_key,
            "final_score": kpi_breakdown.final_score,
            "data_quality": kpi_breakdown.data_quality,
            "confidence": kpi_breakdown.confidence,
            "formula_used": kpi_breakdown.formula_text,
            "formula_steps": [
                {
                    "step": s.step_number,
                    "description": s.description,
                    "formula": s.formula,
                    "result": s.result
                }
                for s in kpi_breakdown.formula_steps
            ],
            "parameters": parameters_with_evidence,
            "norms_reference": KPI_NORMS.get(kpi_key, "AICTE/UGC Handbook 2024"),
            "overall_explanation": explanation,
            "insights": insights,
            "missing_parameters": kpi_breakdown.missing_parameters,
        }
    finally:
        close_db(db)


def _get_norm_for_param(param_name: str, kpi_type: str):
    """Get the norm value for a parameter."""
    norms = {
        # FSR
        "total_faculty": "As per intake",
        "total_students": "As per sanctioned intake",
        # Infrastructure
        "built_up_area": 10000,
        "classrooms": 30,
        "library_area": 500,
        "lab_area": 1000,
        "digital_resources": 1,
        # Placement
        "placement_rate": 80,
        "average_package": 10,
        "highest_package": 20,
        # Labs
        "computer_labs": 5,
        "science_labs": 4,
        "engineering_labs": 6,
        "lab_equipment": 1,
    }
    return norms.get(param_name, "As per norms")


@router.get("/{batch_id}", response_model=DashboardResponse)
def get_dashboard_data(batch_id: str):
    """Get complete dashboard data for a batch"""
    db = get_db()
    
    try:
        batch = db.query(Batch).filter(Batch.id == batch_id).first()
        if not batch:
            raise HTTPException(status_code=404, detail="Batch not found")
        
        # Get KPI cards
        kpi_results = batch.kpi_results or {}
        kpi_cards = []
        kpis_map = {}
        if kpi_results and isinstance(kpi_results, dict):
            for kpi_id, kpi_data in kpi_results.items():
                if isinstance(kpi_data, dict) and "value" in kpi_data:
                    value = kpi_data.get("value", 0)
                    name = kpi_data.get("name", kpi_id.replace("_", " ").title())
                    # Handle None values - display as "Insufficient Data"
                    if value is None:
                        kpi_cards.append(KPICard(
                            name=name,
                            value=None,
                            label="Insufficient Data",
                            color="gray"
                        ))
                    else:
                        kpi_cards.append(KPICard(
                            name=name,
                            value=float(value),
                            label=name,
                            color="blue" if value >= 70 else "orange" if value >= 50 else "red"
                        ))
                    # also populate simplified map
                    kpis_map[kpi_id] = value if value is None else float(value)
    
        # Get sufficiency
        sufficiency_result = batch.sufficiency_result or {}
        if not sufficiency_result:
            # Calculate on-the-fly if not stored
            from services.block_sufficiency import BlockSufficiencyService
            blocks = db.query(Block).filter(Block.batch_id == batch_id).all()
            block_list = [{
                "block_type": b.block_type,
                "extracted_data": b.data or {},
                "is_outdated": bool(b.is_outdated),
                "is_low_quality": bool(b.is_low_quality),
                "is_invalid": bool(b.is_invalid)
            } for b in blocks]
            sufficiency_service = BlockSufficiencyService()
            sufficiency_result = sufficiency_service.calculate_sufficiency(batch.mode, block_list)
        
        sufficiency = SufficiencyCard(
            percentage=sufficiency_result.get("percentage", 0),
            present_count=sufficiency_result.get("present_count", 0),
            required_count=sufficiency_result.get("required_count", 10),
            missing_blocks=sufficiency_result.get("missing_blocks", []),
            penalty_breakdown=sufficiency_result.get("penalty_breakdown", {}),
            color=sufficiency_result.get("color", "red")
        )
    
        # Get information blocks
        blocks = db.query(Block).filter(Block.batch_id == batch_id).all()
        
        # Group blocks by type
        blocks_by_type = {}
        for block in blocks:
            block_type = block.block_type
            if block_type:
                if block_type not in blocks_by_type:
                    blocks_by_type[block_type] = []
                blocks_by_type[block_type].append(block)
        
        # Create block cards for all required blocks (mode-specific)
        new_university = bool(batch.new_university) if batch.new_university else False
        required_blocks = get_information_blocks(batch.mode, new_university)  # Get mode-specific blocks (conditional for UGC)
        block_cards = []
        blocks_with_data: list[BlockWithData] = []
        for block_type in required_blocks:
            block_list = blocks_by_type.get(block_type, [])
            block_desc = get_block_description(block_type)
            
            # Find best block (highest confidence, not invalid)
            best_block = None
            if block_list:
                valid_blocks = [b for b in block_list if not b.is_invalid]
                if valid_blocks:
                    best_block = max(valid_blocks, key=lambda b: b.extraction_confidence)
                else:
                    best_block = max(block_list, key=lambda b: b.extraction_confidence)
            
            if best_block:
                card = BlockCard(
                    block_id=best_block.id,
                    block_type=block_type,
                    block_name=block_desc.get("name", block_type.replace("_", " ").title()),
                    is_present=True,
                    is_outdated=bool(best_block.is_outdated),
                    is_low_quality=bool(best_block.is_low_quality),
                    is_invalid=bool(best_block.is_invalid),
                    confidence=best_block.extraction_confidence,
                    extracted_fields_count=len(best_block.data or {}),
                    evidence_snippet=best_block.evidence_snippet,
                    evidence_page=best_block.evidence_page,
                    source_doc=best_block.source_doc
                )
                block_cards.append(card)
                blocks_with_data.append(BlockWithData(**card.model_dump(), data=best_block.data or {}))
            else:
                # Missing block
                card = BlockCard(
                    block_id="",
                    block_type=block_type,
                    block_name=block_desc.get("name", block_type.replace("_", " ").title()),
                    is_present=False,
                    is_outdated=False,
                    is_low_quality=False,
                    is_invalid=False,
                    confidence=0.0,
                    extracted_fields_count=0
                )
                block_cards.append(card)
                blocks_with_data.append(BlockWithData(**card.model_dump(), data={}))
        
        # Get compliance flags
        compliance_flags_db = db.query(ComplianceFlagModel).filter(ComplianceFlagModel.batch_id == batch_id).all()
        compliance_flags = [
            ComplianceFlag(
                severity=flag.severity,
                title=flag.title,
                reason=flag.reason,
                evidence_page=None,
                evidence_snippet=None,
                recommendation=flag.recommendation
            )
            for flag in compliance_flags_db
        ]
        
        # Get trend data
        trend_results = batch.trend_results or {}
        trend_data = []
        if trend_results.get("has_trend_data"):
            trend_data = [
                TrendDataPoint(
                    year=point.get("year", ""),
                    kpi_name=point.get("kpi_name", ""),
                    value=point.get("value", 0)
                )
                for point in trend_results.get("trend_data", [])
            ]
        
        # Get file count
        from config.database import File
        file_count = db.query(File).filter(File.batch_id == batch_id).count()

        # Convert dict to Pydantic models if present
        approval_classification = None
        if batch.approval_classification:
            if isinstance(batch.approval_classification, dict):
                try:
                    approval_classification = ApprovalClassification(
                        category=batch.approval_classification.get("category", "unknown"),
                        subtype=batch.approval_classification.get("subtype", "unknown"),
                        signals=batch.approval_classification.get("signals", []) if isinstance(batch.approval_classification.get("signals"), list) else []
                    )
                except Exception as e:
                    logger.warning(f"Error converting approval_classification: {e}")
                    approval_classification = None
        
        approval_readiness = None
        if batch.approval_readiness:
            if isinstance(batch.approval_readiness, dict):
                try:
                    classification_dict = batch.approval_readiness.get("classification", {})
                    if not isinstance(classification_dict, dict):
                        classification_dict = {}
                    
                    approval_readiness = ApprovalReadiness(
                        approval_category=classification_dict.get("category", batch.mode or "aicte"),
                        approval_readiness_score=batch.approval_readiness.get("readiness_score", 0.0),
                        present=batch.approval_readiness.get("present_documents", 0),
                        required=batch.approval_readiness.get("required_documents", 0),
                        approval_missing_documents=batch.approval_readiness.get("missing_documents", []) if isinstance(batch.approval_readiness.get("missing_documents"), list) else [],
                        recommendation="Ready" if batch.approval_readiness.get("readiness_score", 0) >= 80 else "Needs improvement"
                    )
                except Exception as e:
                    logger.warning(f"Error converting approval_readiness: {e}")
                    approval_readiness = None
        
        return DashboardResponse(
            batch_id=batch_id,
            mode=batch.mode,
            institution_name=None,
            kpi_cards=kpi_cards,
            kpis=kpis_map,
            block_cards=block_cards,
            blocks=blocks_with_data,
            sufficiency=sufficiency,
            compliance_flags=compliance_flags,
            trend_data=trend_data,
            total_documents=file_count,
            processed_documents=file_count if batch.status == "completed" else 0,
            approval_classification=approval_classification,
            approval_readiness=approval_readiness,
        )
    finally:
        close_db(db)
