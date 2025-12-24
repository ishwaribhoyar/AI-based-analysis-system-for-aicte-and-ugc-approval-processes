"""
KPI Details Service.
Generates parameter-level breakdown for each KPI showing:
- Raw extracted values
- Normalized values
- Step-by-step formula computation
- Missing parameter detection
"""

from typing import Dict, List, Optional, Any, Tuple
from schemas.kpi_details import (
    ParameterBreakdown, FormulaStep, KPIBreakdown, KPIDetailsResponse
)
from config.database import get_db, close_db, Batch, Block


# Aliases for parameter extraction
PARAMETER_ALIASES = {
    "total_faculty": ["faculty_count", "total_teaching_staff", "teaching_staff", "no_of_faculty"],
    "total_students": ["student_count", "total_enrollment", "enrolled_students"],
    "ug_enrollment": ["ug_students", "undergraduate_enrollment", "ug_intake"],
    "pg_enrollment": ["pg_students", "postgraduate_enrollment", "pg_intake"],
    "built_up_area": ["total_built_up_area", "building_area", "built_area"],
    "classrooms": ["classroom_count", "number_of_classrooms", "no_of_classrooms"],
    "library_area": ["library_size", "library_space"],
    "lab_area": ["laboratory_area", "lab_space", "total_lab_area"],
    "placed_students": ["students_placed", "placements", "placed_count"],
    "eligible_students": ["students_eligible", "eligible_for_placement"],
    "placement_rate": ["placement_percentage", "placement_ratio"],
    "highest_package": ["max_package", "highest_salary", "max_salary_lpa"],
    "average_package": ["avg_package", "average_salary", "mean_salary_lpa"],
}


def _find_parameter(data: Dict, param_name: str) -> Optional[Any]:
    """Find a parameter value using aliases."""
    # Direct lookup
    if param_name in data and data[param_name] is not None:
        return data[param_name]
    
    # Alias lookup
    aliases = PARAMETER_ALIASES.get(param_name, [])
    for alias in aliases:
        if alias in data and data[alias] is not None:
            return data[alias]
    
    # Nested search
    for key, val in data.items():
        if isinstance(val, dict):
            result = _find_parameter(val, param_name)
            if result is not None:
                return result
    
    return None


def _to_float(value: Any) -> Optional[float]:
    """Convert value to float, handling various formats."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        # Remove commas, spaces
        clean = value.replace(",", "").replace(" ", "").strip()
        # Handle LPA/Cr
        if "lpa" in clean.lower():
            clean = clean.lower().replace("lpa", "")
            try:
                return float(clean)
            except:
                return None
        if "cr" in clean.lower() or "crore" in clean.lower():
            clean = clean.lower().replace("crore", "").replace("cr", "")
            try:
                return float(clean) * 100  # Convert crore to lpa
            except:
                return None
        try:
            return float(clean)
        except:
            return None
    return None


def _sqft_to_sqm(sqft: float) -> float:
    """Convert square feet to square meters."""
    return sqft * 0.092903


def compute_fsr_breakdown(data: Dict) -> KPIBreakdown:
    """Compute FSR (Faculty-Student Ratio) breakdown."""
    params = []
    steps = []
    missing = []
    
    # Extract parameters
    total_faculty = _to_float(_find_parameter(data, "total_faculty"))
    total_students = _to_float(_find_parameter(data, "total_students"))
    
    # Fallback: sum UG + PG if total_students missing
    if total_students is None:
        ug = _to_float(_find_parameter(data, "ug_enrollment")) or 0
        pg = _to_float(_find_parameter(data, "pg_enrollment")) or 0
        if ug + pg > 0:
            total_students = ug + pg
    
    params.append(ParameterBreakdown(
        parameter_name="total_faculty",
        display_name="Total Faculty",
        raw_value=total_faculty,
        normalized_value=total_faculty,
        unit="persons",
        weight=1.0,
        missing=total_faculty is None,
    ))
    
    params.append(ParameterBreakdown(
        parameter_name="total_students",
        display_name="Total Students",
        raw_value=total_students,
        normalized_value=total_students,
        unit="persons",
        weight=1.0,
        missing=total_students is None,
    ))
    
    if total_faculty is None:
        missing.append("total_faculty")
    if total_students is None:
        missing.append("total_students")
    
    # Compute score
    final_score = 0.0
    ratio = None
    
    if total_faculty and total_students and total_faculty > 0:
        ratio = total_students / total_faculty
        ideal_ratio = 15.0  # AICTE norm
        
        steps.append(FormulaStep(
            step_number=1,
            description="Calculate student-faculty ratio",
            formula="ratio = total_students / total_faculty",
            result=round(ratio, 2)
        ))
        
        if ratio <= ideal_ratio:
            final_score = 100.0
        else:
            final_score = max(0, min(100, (ideal_ratio / ratio) * 100))
        
        steps.append(FormulaStep(
            step_number=2,
            description="Compare with ideal ratio (15:1 for AICTE)",
            formula="score = min(100, (ideal_ratio / actual_ratio) * 100)" if ratio > ideal_ratio else "score = 100 (ratio ≤ 15 is excellent)",
            result=round(final_score, 2)
        ))
    
    return KPIBreakdown(
        kpi_key="fsr_score",
        kpi_name="Faculty-Student Ratio Score",
        final_score=round(final_score, 2),
        parameters=params,
        formula_steps=steps,
        formula_text="fsr_score = min(100, max(0, (ideal_ratio / actual_ratio) * 100))",
        missing_parameters=missing,
        data_quality="complete" if not missing else ("partial" if final_score > 0 else "insufficient"),
        confidence=1.0 if not missing else (0.7 if final_score > 0 else 0.3)
    )


def compute_infrastructure_breakdown(data: Dict) -> KPIBreakdown:
    """Compute Infrastructure Score breakdown with weighted components."""
    params = []
    steps = []
    missing = []
    
    # Infrastructure parameters with weights
    infra_components = [
        ("built_up_area", "Built-up Area", 0.40, 10000),  # sqm norm
        ("classrooms", "Classrooms", 0.25, 30),  # count norm
        ("library_area", "Library Area", 0.15, 500),  # sqm norm
        ("lab_area", "Lab Area", 0.10, 1000),  # sqm norm
        ("digital_resources", "Digital Resources", 0.10, 1),  # boolean
    ]
    
    total_contribution = 0.0
    step_num = 1
    
    for param_name, display_name, weight, norm in infra_components:
        raw_val = _find_parameter(data, param_name)
        normalized = _to_float(raw_val)
        
        # Convert sqft to sqm if area parameter
        if normalized and "area" in param_name:
            if raw_val and isinstance(raw_val, str) and ("sq.ft" in raw_val.lower() or "sqft" in raw_val.lower()):
                normalized = _sqft_to_sqm(normalized)
        
        # Calculate component score
        component_score = 0.0
        if normalized is not None and normalized > 0:
            component_score = min(100, (normalized / norm) * 100)
        
        contribution = (component_score * weight)
        total_contribution += contribution
        
        params.append(ParameterBreakdown(
            parameter_name=param_name,
            display_name=display_name,
            raw_value=raw_val,
            normalized_value=round(normalized, 2) if normalized else None,
            unit="sqm" if "area" in param_name else ("count" if "classroom" in param_name else ""),
            weight=weight,
            score=round(component_score, 2),
            contribution=round(contribution, 2),
            missing=normalized is None,
        ))
        
        if normalized is None:
            missing.append(param_name)
        
        steps.append(FormulaStep(
            step_number=step_num,
            description=f"Calculate {display_name} contribution",
            formula=f"contribution = (value / norm) * {weight*100}%",
            result=round(contribution, 2)
        ))
        step_num += 1
    
    final_score = min(100, total_contribution)
    
    steps.append(FormulaStep(
        step_number=step_num,
        description="Sum all contributions",
        formula="infrastructure_score = sum(contributions)",
        result=round(final_score, 2)
    ))
    
    return KPIBreakdown(
        kpi_key="infrastructure_score",
        kpi_name="Infrastructure Score",
        final_score=round(final_score, 2),
        parameters=params,
        formula_steps=steps,
        formula_text="infrastructure_score = Σ(component_score × weight)",
        missing_parameters=missing,
        data_quality="complete" if len(missing) == 0 else ("partial" if len(missing) <= 2 else "insufficient"),
        confidence=1.0 - (len(missing) * 0.15)
    )


def compute_placement_breakdown(data: Dict) -> KPIBreakdown:
    """Compute Placement Index breakdown."""
    params = []
    steps = []
    missing = []
    
    placed = _to_float(_find_parameter(data, "placed_students"))
    eligible = _to_float(_find_parameter(data, "eligible_students"))
    placement_rate = _to_float(_find_parameter(data, "placement_rate"))
    avg_package = _to_float(_find_parameter(data, "average_package"))
    highest_package = _to_float(_find_parameter(data, "highest_package"))
    
    # Compute placement rate if missing
    if placement_rate is None and placed is not None and eligible is not None and eligible > 0:
        placement_rate = (placed / eligible) * 100
    
    params.append(ParameterBreakdown(
        parameter_name="placed_students",
        display_name="Students Placed",
        raw_value=placed,
        normalized_value=placed,
        unit="count",
        weight=0.0,
        missing=placed is None,
    ))
    
    params.append(ParameterBreakdown(
        parameter_name="eligible_students",
        display_name="Eligible Students",
        raw_value=eligible,
        normalized_value=eligible,
        unit="count",
        weight=0.0,
        missing=eligible is None,
    ))
    
    params.append(ParameterBreakdown(
        parameter_name="placement_rate",
        display_name="Placement Rate",
        raw_value=placement_rate,
        normalized_value=placement_rate,
        unit="%",
        weight=0.60,
        score=min(100, placement_rate) if placement_rate else 0,
        contribution=min(100, placement_rate) * 0.6 if placement_rate else 0,
        missing=placement_rate is None,
    ))
    
    params.append(ParameterBreakdown(
        parameter_name="average_package",
        display_name="Average Package",
        raw_value=avg_package,
        normalized_value=avg_package,
        unit="LPA",
        weight=0.25,
        score=min(100, (avg_package / 10) * 100) if avg_package else 0,
        contribution=min(100, (avg_package / 10) * 100) * 0.25 if avg_package else 0,
        missing=avg_package is None,
    ))
    
    params.append(ParameterBreakdown(
        parameter_name="highest_package",
        display_name="Highest Package",
        raw_value=highest_package,
        normalized_value=highest_package,
        unit="LPA",
        weight=0.15,
        score=min(100, (highest_package / 20) * 100) if highest_package else 0,
        contribution=min(100, (highest_package / 20) * 100) * 0.15 if highest_package else 0,
        missing=highest_package is None,
    ))
    
    # Identify missing
    if placement_rate is None:
        missing.append("placement_rate")
    if avg_package is None:
        missing.append("average_package")
    if highest_package is None:
        missing.append("highest_package")
    
    # Calculate final score
    final_score = 0.0
    step_num = 1
    
    if placement_rate is not None:
        rate_contrib = min(100, placement_rate) * 0.6
        final_score += rate_contrib
        steps.append(FormulaStep(
            step_number=step_num,
            description="Placement rate contribution (60% weight)",
            formula="rate_contribution = min(100, placement_rate) × 0.6",
            result=round(rate_contrib, 2)
        ))
        step_num += 1
    
    if avg_package is not None:
        pkg_contrib = min(100, (avg_package / 10) * 100) * 0.25
        final_score += pkg_contrib
        steps.append(FormulaStep(
            step_number=step_num,
            description="Average package contribution (25% weight, 10 LPA = 100)",
            formula="avg_pkg_contribution = min(100, (avg_package / 10) × 100) × 0.25",
            result=round(pkg_contrib, 2)
        ))
        step_num += 1
    
    if highest_package is not None:
        high_contrib = min(100, (highest_package / 20) * 100) * 0.15
        final_score += high_contrib
        steps.append(FormulaStep(
            step_number=step_num,
            description="Highest package contribution (15% weight, 20 LPA = 100)",
            formula="high_pkg_contribution = min(100, (highest_package / 20) × 100) × 0.15",
            result=round(high_contrib, 2)
        ))
        step_num += 1
    
    steps.append(FormulaStep(
        step_number=step_num,
        description="Sum all contributions",
        formula="placement_index = rate_contrib + avg_pkg_contrib + high_pkg_contrib",
        result=round(final_score, 2)
    ))
    
    return KPIBreakdown(
        kpi_key="placement_index",
        kpi_name="Placement Index",
        final_score=round(final_score, 2),
        parameters=params,
        formula_steps=steps,
        formula_text="placement_index = (placement_rate × 0.6) + (avg_package_score × 0.25) + (highest_package_score × 0.15)",
        missing_parameters=missing,
        data_quality="complete" if len(missing) == 0 else ("partial" if placement_rate else "insufficient"),
        confidence=0.9 if placement_rate else 0.4
    )


def compute_lab_compliance_breakdown(data: Dict) -> KPIBreakdown:
    """Compute Lab Compliance Index breakdown."""
    params = []
    steps = []
    missing = []
    
    lab_components = [
        ("computer_labs", "Computer Labs", 0.30, 5),
        ("science_labs", "Science Labs", 0.25, 4),
        ("engineering_labs", "Engineering Labs", 0.25, 6),
        ("lab_equipment", "Lab Equipment Status", 0.20, 1),
    ]
    
    total_contribution = 0.0
    step_num = 1
    
    for param_name, display_name, weight, norm in lab_components:
        raw_val = _find_parameter(data, param_name)
        normalized = _to_float(raw_val) if raw_val else None
        
        # Boolean check for equipment
        if param_name == "lab_equipment":
            if raw_val is not None:
                normalized = 1.0 if str(raw_val).lower() in ["yes", "true", "available", "1", "operational"] else 0.0
        
        component_score = 0.0
        if normalized is not None:
            component_score = min(100, (normalized / norm) * 100)
        
        contribution = component_score * weight
        total_contribution += contribution
        
        params.append(ParameterBreakdown(
            parameter_name=param_name,
            display_name=display_name,
            raw_value=raw_val,
            normalized_value=normalized,
            unit="count" if "labs" in param_name else "status",
            weight=weight,
            score=round(component_score, 2),
            contribution=round(contribution, 2),
            missing=normalized is None,
        ))
        
        if normalized is None:
            missing.append(param_name)
        
        steps.append(FormulaStep(
            step_number=step_num,
            description=f"Calculate {display_name} contribution",
            formula=f"contribution = (count / {norm}) × {weight*100}%",
            result=round(contribution, 2)
        ))
        step_num += 1
    
    final_score = min(100, total_contribution)
    
    steps.append(FormulaStep(
        step_number=step_num,
        description="Sum all contributions",
        formula="lab_compliance_index = sum(contributions)",
        result=round(final_score, 2)
    ))
    
    return KPIBreakdown(
        kpi_key="lab_compliance_index",
        kpi_name="Lab Compliance Index",
        final_score=round(final_score, 2),
        parameters=params,
        formula_steps=steps,
        formula_text="lab_compliance_index = Σ(component_score × weight)",
        missing_parameters=missing,
        data_quality="complete" if len(missing) == 0 else ("partial" if len(missing) <= 2 else "insufficient"),
        confidence=1.0 - (len(missing) * 0.2)
    )


def compute_overall_breakdown(fsr: KPIBreakdown, infra: KPIBreakdown, placement: KPIBreakdown, lab: KPIBreakdown) -> KPIBreakdown:
    """Compute Overall Score from component KPIs."""
    params = []
    steps = []
    
    components = [
        (fsr, "FSR Score", 0.25),
        (infra, "Infrastructure Score", 0.25),
        (placement, "Placement Index", 0.30),
        (lab, "Lab Compliance Index", 0.20),
    ]
    
    total_score = 0.0
    step_num = 1
    
    for kpi, display_name, weight in components:
        contribution = kpi.final_score * weight
        total_score += contribution
        
        params.append(ParameterBreakdown(
            parameter_name=kpi.kpi_key,
            display_name=display_name,
            raw_value=kpi.final_score,
            normalized_value=kpi.final_score,
            unit="score",
            weight=weight,
            score=kpi.final_score,
            contribution=round(contribution, 2),
            missing=kpi.data_quality == "insufficient",
        ))
        
        steps.append(FormulaStep(
            step_number=step_num,
            description=f"{display_name} contribution ({weight*100}% weight)",
            formula=f"contribution = {kpi.final_score} × {weight}",
            result=round(contribution, 2)
        ))
        step_num += 1
    
    steps.append(FormulaStep(
        step_number=step_num,
        description="Sum all KPI contributions",
        formula="overall_score = Σ(kpi_score × weight)",
        result=round(total_score, 2)
    ))
    
    missing = [p.parameter_name for p in params if p.missing]
    
    return KPIBreakdown(
        kpi_key="overall_score",
        kpi_name="Overall Score",
        final_score=round(total_score, 2),
        parameters=params,
        formula_steps=steps,
        formula_text="overall_score = (FSR × 0.25) + (Infrastructure × 0.25) + (Placement × 0.30) + (Lab × 0.20)",
        missing_parameters=missing,
        data_quality="complete" if len(missing) == 0 else "partial",
        confidence=sum(kpi.confidence for kpi, _, _ in components) / 4
    )


def get_kpi_details(batch_id: str) -> KPIDetailsResponse:
    """Get full KPI breakdown for a batch."""
    db = get_db()
    try:
        batch = db.query(Batch).filter(Batch.id == batch_id).first()
        if not batch:
            raise ValueError(f"Batch {batch_id} not found")
        
        blocks = db.query(Block).filter(Block.batch_id == batch_id).all()
        
        # Aggregate all block data
        aggregated_data = {}
        institution_name = "Unknown Institution"
        
        for block in blocks:
            if block.data:
                aggregated_data.update(block.data)
                # Try to find institution name
                for key in ["institution_name", "name", "institute_name", "college_name"]:
                    if key in block.data and block.data[key]:
                        institution_name = str(block.data[key])
                        break
        
        # Compute each KPI breakdown
        fsr = compute_fsr_breakdown(aggregated_data)
        infra = compute_infrastructure_breakdown(aggregated_data)
        placement = compute_placement_breakdown(aggregated_data)
        lab = compute_lab_compliance_breakdown(aggregated_data)
        overall = compute_overall_breakdown(fsr, infra, placement, lab)
        
        return KPIDetailsResponse(
            batch_id=batch_id,
            institution_name=institution_name,
            mode=batch.mode or "unknown",
            fsr=fsr,
            infrastructure=infra,
            placement=placement,
            lab_compliance=lab,
            overall=overall,
        )
    finally:
        close_db(db)
