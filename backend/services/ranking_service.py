"""
Ranking service for Top-N institution comparison using real KPI scores.
Relies solely on persisted KPI results – no placeholders or dummy values.
"""

from typing import List, Dict, Any, Optional, Tuple
import math

from config.database import get_db, close_db, Batch
from routers.dashboard import get_dashboard_data
from utils.label_formatter import generate_short_label

# Canonical KPI keys stored inside batch.kpi_results
KPI_KEYS = [
    "fsr_score",
    "infrastructure_score",
    "placement_index",
    "lab_compliance_index",
    "overall_score",
]


def _is_number(val: Any) -> bool:
    return isinstance(val, (int, float)) and not isinstance(val, bool) and not math.isnan(val)


def _extract_kpis(kpi_results: Dict[str, Any]) -> Dict[str, Optional[float]]:
    """
    Extract canonical KPI scores from stored results.
    Only returns numeric values; missing or non-numeric entries become None.
    """
    if not isinstance(kpi_results, dict):
        return {key: None for key in KPI_KEYS}

    extracted: Dict[str, Optional[float]] = {}
    for key in KPI_KEYS:
        raw_val = kpi_results.get(key)
        if _is_number(raw_val) and raw_val > 0:
            extracted[key] = float(raw_val)
        else:
            extracted[key] = None
    return extracted


def _strengths_weaknesses(kpis: Dict[str, Optional[float]]) -> Tuple[List[str], List[str]]:
    """Generate high-level strengths/weaknesses from KPI scores."""
    scored = [(k, v) for k, v in kpis.items() if _is_number(v)]
    if not scored:
        return [], []

    scored.sort(key=lambda kv: kv[1], reverse=True)

    strengths = []
    for k, v in scored[:3]:
        if v >= 80:
            strengths.append(f"Excellent {k.replace('_', ' ').title()} ({v:.1f})")
        elif v >= 60:
            strengths.append(f"Good {k.replace('_', ' ').title()} ({v:.1f})")

    weaknesses = []
    for k, v in reversed(scored):
        if v < 60:
            weaknesses.append(f"{k.replace('_', ' ').title()} needs improvement ({v:.1f})")
        if len(weaknesses) >= 3:
            break

    return strengths, weaknesses


def _infer_name_and_label(batch_id: str, dashboard: Any) -> Tuple[str, str]:
    """Prefer real institution name; fall back to short label using batch id."""
    name = ""
    if dashboard and getattr(dashboard, "institution_name", None):
        candidate = str(dashboard.institution_name).strip()
        if len(candidate) > 3:
            name = candidate

    if not name and dashboard and getattr(dashboard, "block_cards", None):
        for block in dashboard.block_cards:
            data = getattr(block, "data", None)
            if not data:
                continue
            for key in ["institution_name", "name", "institute_name", "college_name"]:
                if data.get(key):
                    candidate = str(data[key]).strip()
                    if len(candidate) > 3:
                        name = candidate
                        break
            if name:
                break

    if not name:
        name = f"Institution {batch_id[-6:]}"

    short_label = generate_short_label(name, batch_id, "2024-25")
    return name, short_label


def _normalize_weights(kpi_weights: Dict[str, float]) -> Dict[str, float]:
    """Ensure weights only include canonical KPI keys and are non-negative floats."""
    normalized: Dict[str, float] = {}
    for key in KPI_KEYS:
        val = kpi_weights.get(key, 0) if kpi_weights else 0
        try:
            weight = float(val)
        except (TypeError, ValueError):
            weight = 0.0
        if weight < 0:
            weight = 0.0
        normalized[key] = weight
    return normalized


def rank_institutions(batch_ids: List[str], kpi_weights: Dict[str, float], top_n: int, ranking_type: str) -> Dict[str, Any]:
    """
    Rank institutions based on weighted KPI scores.

    - Only uses real KPI values from batch.kpi_results
    - Skips batches where any required KPI for weighting is missing
    """
    db = get_db()
    try:
        seen = set()
        unique_ids = [bid for bid in batch_ids if not (bid in seen or seen.add(bid))]
        weights = _normalize_weights(kpi_weights)
        required_keys = {k for k, w in weights.items() if w > 0}

        ranked_institutions: List[Dict[str, Any]] = []
        insufficient: List[Dict[str, str]] = []

        for bid in unique_ids:
            batch = db.query(Batch).filter(Batch.id == bid).first()
            if not batch:
                insufficient.append({"batch_id": bid, "reason": "batch_not_found"})
                continue
            if batch.status != "completed":
                insufficient.append({"batch_id": bid, "reason": f"status_{batch.status}"})
                continue

            kpi_results = batch.kpi_results or {}
            kpis = _extract_kpis(kpi_results)

            # If any required KPI is missing, mark insufficient
            if any(kpis.get(k) is None for k in required_keys):
                insufficient.append({"batch_id": bid, "reason": "insufficient_kpi_data"})
                continue

            # Compute weighted score using available KPIs
            ranking_score = 0.0
            for key, weight in weights.items():
                val = kpis.get(key)
                if weight > 0 and _is_number(val):
                    ranking_score += weight * float(val)

            # Skip if score cannot be computed
            if ranking_score == 0 and required_keys:
                insufficient.append({"batch_id": bid, "reason": "insufficient_kpi_data"})
                continue

            try:
                dashboard = get_dashboard_data(bid)
            except Exception:
                insufficient.append({"batch_id": bid, "reason": "missing_dashboard"})
                continue
            institution_name, short_label = _infer_name_and_label(bid, dashboard)
            strengths, weaknesses = _strengths_weaknesses(kpis)

            ranked_institutions.append({
                "batch_id": bid,
                "name": institution_name,
                "short_label": short_label,
                "ranking_score": ranking_score,
                "fsr_score": kpis.get("fsr_score"),
                "infrastructure_score": kpis.get("infrastructure_score"),
                "placement_index": kpis.get("placement_index"),
                "lab_compliance_index": kpis.get("lab_compliance_index"),
                "overall_score": kpis.get("overall_score"),
                "mode": batch.mode or "",
                "strengths": strengths,
                "weaknesses": weaknesses,
            })

        ranked_institutions.sort(key=lambda inst: inst["ranking_score"], reverse=True)

        return {
            "ranking_type": ranking_type,
            "top_n": top_n,
            "institutions": ranked_institutions[:top_n],
            "insufficient_batches": insufficient,
        }
    finally:
        close_db(db)

