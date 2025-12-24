"""
Comprehensive E2E test comparing actual outputs with expected outputs
for sample.pdf and INSTITUTE INFORMATION CONSOLIDATED REPORT.pdf
"""

import sys
import time
import json
from pathlib import Path
from typing import Dict, Any, Optional
import requests

# Add parent directory to path
BASE_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "backend"))

API_BASE = "http://127.0.0.1:8010/api"

# Expected outputs
EXPECTED_SAMPLE = {
    "kpis": {
        "fsr_score": 100.00,
        "infrastructure_score": 14.34,  # Approximate
        "placement_index": 84.70,
        "lab_compliance_index": 100.00,
        "overall_score": 94.90  # Approximate
    },
    "sufficiency": {
        "present_blocks": 10,
        "required_blocks": 10,
        "percentage": 96.0  # 96-100%
    },
    "blocks": {
        "faculty_information": {
            "total_faculty": 82,
            "professors": 14,
            "associate_professors": 22,
            "assistant_professors": 46,
            "phd_faculty": 38,
            "non_teaching_staff": 12,
            "year": 2024
        },
        "student_enrollment_information": {
            "total_students": 1290,
            "male": 780,
            "female": 510,
            "academic_year": "2023-24"
        },
        "infrastructure_information": {
            "built_up_area_sqm": 18500,
            "classrooms": 42,
            "tutorial_rooms": 16,
            "seminar_halls": 4,
            "library_area_sqm": 750,
            "library_seating": 120
        },
        "lab_equipment_information": {
            "total_labs": 31,
            "computer_labs": 7
        },
        "placement_information": {
            "eligible_students": 420,
            "students_placed": 356,
            "placement_rate": 84.7,
            "median_salary_lpa": 4.2,
            "highest_salary_lpa": 12.0,
            "year": "2023-24"  # This should mark it as outdated
        },
        "research_innovation_information": {
            "publications": 64,
            "patents_filed": 4,
            "patents_granted": 1,
            "funded_projects": 6
        }
    }
}

EXPECTED_CONSOLIDATED = {
    "kpis": {
        "fsr_score": None,  # Insufficient data
        "infrastructure_score": 27.0,  # Approximate (27-35)
        "placement_index": 86.19,
        "lab_compliance_index": 100.00,
        "overall_score": 60.0  # Approximate (60-75)
    },
    "sufficiency": {
        "present_blocks": 9,
        "required_blocks": 10,
        "percentage": 90.0
    },
    "blocks": {
        "faculty_information": {
            "total_faculty": 112,
            "permanent_faculty": 98,
            "visiting_faculty": 14,
            "phd_faculty": 52,
            "non_phd_faculty": 60,
            "supporting_staff": 23
        },
        "student_enrollment_information": {
            "total_students": 1840,
            "ug_enrollment": 1520,
            "pg_enrollment": 320,
            "intake_capacity_ug": 1600,
            "intake_capacity_pg": 350,
            "foreign_students": 28
        },
        "infrastructure_information": {
            "built_up_area_sqm": 17187,  # 185,000 sq.ft → 17,187 sqm
            "total_classrooms": 34,
            "smart_classrooms": 22,
            "library_books": 32500,
            "digital_library_resources": 1240,
            "computers_available": 485,
            "hostel_capacity": 800
        },
        "lab_equipment_information": {
            "total_labs": 48,
            "advanced_labs": 12,
            "major_equipment_count": 152,
            "computers_in_labs": 320,
            "annual_lab_budget_raw": 6500000
        },
        "placement_information": {
            "eligible_students": 420,
            "students_placed": 362,
            "placement_rate": 86.19,
            "average_salary": 6.5,
            "highest_salary_lpa": 18.0
        },
        "research_innovation_information": {
            "publications": 128,
            "patents_filed": 6,
            "patents_granted": 2,
            "funded_projects": 11,
            "research_funding_raw": 28000000  # 2.8 Cr
        }
    }
}


def find_pdf(filename: str) -> Optional[Path]:
    """Find PDF in repo root"""
    repo_root = Path(__file__).parent.parent.parent
    candidate = repo_root / filename
    if candidate.exists() and candidate.stat().st_size > 0:
        return candidate
    return None


def run_full_pipeline(pdf_path: Path, pdf_name: str) -> Dict[str, Any]:
    """Run complete pipeline: create batch, upload, process, get dashboard"""
    print(f"\n{'='*70}")
    print(f"Testing: {pdf_name}")
    print(f"{'='*70}\n")
    
    # Check backend
    try:
        r = requests.get(f"{API_BASE.replace('/api', '')}/", timeout=10)
        print(f"[OK] Backend reachable at {API_BASE.replace('/api', '')}")
    except Exception as e:
        print(f"[ERROR] Backend NOT reachable at {API_BASE.replace('/api', '')}: {e}")
        print(f"[INFO] Waiting 15 seconds for backend to start...")
        time.sleep(15)
        try:
            r = requests.get(f"{API_BASE.replace('/api', '')}/", timeout=10)
            print(f"[OK] Backend reachable after wait")
        except Exception as e2:
            print(f"[ERROR] Backend still NOT reachable: {e2}")
            return {}
    
    # Step 1: Create batch
    print("Step 1: Creating batch...")
    try:
        r = requests.post(
            f"{API_BASE}/batches/create",
            json={"mode": "aicte"},
            timeout=10,
        )
        r.raise_for_status()
        batch_data = r.json()
        batch_id = batch_data.get("batch_id") or batch_data.get("id")
        print(f"[OK] Batch created: {batch_id}")
    except Exception as e:
        print(f"[ERROR] Failed to create batch: {e}")
        return {}
    
    # Step 2: Upload PDF
    print("Step 2: Uploading PDF...")
    try:
        with open(pdf_path, "rb") as f:
            files = {"file": (pdf_path.name, f, "application/pdf")}
            r = requests.post(
                f"{API_BASE}/documents/{batch_id}/upload",
                files=files,
                timeout=30,
            )
        r.raise_for_status()
        upload_data = r.json()
        print(f"[OK] PDF uploaded: {upload_data.get('filename')}")
    except Exception as e:
        print(f"[ERROR] Failed to upload: {e}")
        return {}
    
    # Step 3: Start processing
    print("Step 3: Starting processing...")
    try:
        r = requests.post(
            f"{API_BASE}/processing/start",
            json={"batch_id": batch_id},
            timeout=10,
        )
        r.raise_for_status()
        print(f"[OK] Processing started")
    except Exception as e:
        print(f"[ERROR] Failed to start processing: {e}")
        return {}
    
    # Step 4: Wait for completion
    print("Step 4: Waiting for processing...")
    max_wait = 300  # 5 minutes
    waited = 0
    while waited < max_wait:
        try:
            r = requests.get(f"{API_BASE}/processing/status/{batch_id}", timeout=10)
            r.raise_for_status()
            status_data = r.json()
            status = status_data.get("status")
            progress = status_data.get("progress", 0)
            stage = status_data.get("current_stage", "")
            
            print(f"  [{waited}s] {status} - {stage} ({progress}%)")
            
            if status == "completed":
                print(f"[OK] Processing completed")
                break
            elif status == "failed":
                print(f"[ERROR] Processing failed")
                return {}
            
            time.sleep(5)
            waited += 5
        except Exception as e:
            print(f"[ERROR] Error checking status: {e}")
            return {}
    
    if waited >= max_wait:
        print(f"[ERROR] Processing timeout")
        return {}
    
    # Step 5: Get dashboard
    print("Step 5: Fetching dashboard...")
    try:
        r = requests.get(f"{API_BASE}/dashboard/{batch_id}", timeout=10)
        r.raise_for_status()
        dashboard = r.json()
        print(f"[OK] Dashboard retrieved")
        return dashboard
    except Exception as e:
        print(f"[ERROR] Failed to get dashboard: {e}")
        return {}


def compare_value(actual: Any, expected: Any, field_name: str, tolerance: float = 0.1) -> tuple[bool, str]:
    """Compare actual vs expected value with tolerance for floats"""
    if expected is None:
        if actual is None:
            return True, "[OK]"
        return False, f"Expected None, got {actual}"
    
    if actual is None:
        return False, f"Expected {expected}, got None"
    
    # Handle numeric comparison with tolerance
    if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
        if abs(actual - expected) <= tolerance:
            return True, "[OK]"
        return False, f"Expected {expected}, got {actual} (diff: {abs(actual - expected):.2f})"
    
    # Handle string comparison (case-insensitive)
    if isinstance(expected, str) and isinstance(actual, str):
        if expected.lower() == actual.lower():
            return True, "[OK]"
        return False, f"Expected '{expected}', got '{actual}'"
    
    # Exact match
    if actual == expected:
        return True, "[OK]"
    return False, f"Expected {expected}, got {actual}"


def compare_block(actual_block: Dict, expected_block: Dict, block_name: str) -> Dict[str, Any]:
    """Compare a single block's values"""
    results = {
        "block_name": block_name,
        "matches": [],
        "mismatches": [],
        "missing": []
    }
    
    for field, expected_value in expected_block.items():
        actual_value = actual_block.get(field)
        
        # Check for numeric variants
        if actual_value is None and isinstance(expected_value, (int, float)):
            actual_value = actual_block.get(f"{field}_num")
        
        if actual_value is None:
            results["missing"].append(f"{field} (expected: {expected_value})")
        else:
            match, msg = compare_value(actual_value, expected_value, field)
            if match:
                results["matches"].append(f"{field}: {msg}")
            else:
                results["mismatches"].append(f"{field}: {msg}")
    
    return results


def analyze_results(dashboard: Dict[str, Any], expected: Dict[str, Any], pdf_name: str):
    """Compare dashboard results with expected values"""
    print(f"\n{'='*70}")
    print(f"ANALYSIS: {pdf_name}")
    print(f"{'='*70}\n")
    
    # Compare KPIs
    print("📊 KPI COMPARISON:")
    print("-" * 70)
    actual_kpis = dashboard.get("kpis", {})
    expected_kpis = expected.get("kpis", {})
    
    for kpi_name, expected_value in expected_kpis.items():
        actual_value = actual_kpis.get(kpi_name)
        if expected_value is None:
            if actual_value is None:
                print(f"  [OK] {kpi_name}: None (as expected)")
            else:
                print(f"  [MISMATCH] {kpi_name}: Expected None, got {actual_value}")
        else:
            tolerance = 5.0 if "score" in kpi_name or "index" in kpi_name else 0.1
            match, msg = compare_value(actual_value, expected_value, kpi_name, tolerance)
            if match:
                print(f"  [OK] {kpi_name}: {actual_value} (expected: {expected_value})")
            else:
                print(f"  [MISMATCH] {kpi_name}: {msg}")
    
    # Compare Sufficiency
    print(f"\n📈 SUFFICIENCY COMPARISON:")
    print("-" * 70)
    actual_suff = dashboard.get("sufficiency", {})
    expected_suff = expected.get("sufficiency", {})
    # Normalize keys for comparison
    if "present_blocks" not in actual_suff and "present_count" in actual_suff:
        actual_suff = {**actual_suff, "present_blocks": actual_suff.get("present_count")}
    if "required_blocks" not in actual_suff and "required_count" in actual_suff:
        actual_suff = {**actual_suff, "required_blocks": actual_suff.get("required_count")}
    if "percentage" not in actual_suff and "percentage" in actual_suff:
        actual_suff = {**actual_suff, "percentage": actual_suff.get("percentage")}
    
    for field in ["present_blocks", "required_blocks", "percentage"]:
        actual_val = actual_suff.get(field)
        expected_val = expected_suff.get(field)
        match, msg = compare_value(actual_val, expected_val, field, tolerance=5.0)
        if match:
            print(f"  [OK] {field}: {actual_val} (expected: {expected_val})")
        else:
            print(f"  [MISMATCH] {field}: {msg}")
    
    # Compare Blocks
    print(f"\n📋 BLOCK COMPARISON:")
    print("-" * 70)
    # Use block_type for reliable matching
    actual_blocks = {b.get("block_type"): b for b in dashboard.get("blocks", [])}
    expected_blocks = expected.get("blocks", {})
    
    for block_name, expected_block_data in expected_blocks.items():
        actual_block = actual_blocks.get(block_name)
        if not actual_block:
            print(f"  [ERROR] {block_name}: Block not found in results")
            continue
        
        block_data = actual_block.get("data", {})
        results = compare_block(block_data, expected_block_data, block_name)
        
        print(f"\n  {block_name}:")
        if results["matches"]:
            print(f"    [OK] Matches: {len(results['matches'])} fields")
        if results["mismatches"]:
            print(f"    [MISMATCH] Mismatches ({len(results['mismatches'])}):")
            for mismatch in results["mismatches"][:5]:  # Show first 5
                print(f"      - {mismatch}")
        if results["missing"]:
            print(f"    [MISSING] Missing ({len(results['missing'])}):")
            for missing in results["missing"][:5]:  # Show first 5
                print(f"      - {missing}")
    
    # Save full dashboard JSON for inspection
    output_file = BASE_DIR / "backend" / "tests" / f"dashboard_{pdf_name.replace('.pdf', '').replace(' ', '_')}.json"
    with open(output_file, "w") as f:
        json.dump(dashboard, f, indent=2)
    print(f"\n💾 Full dashboard saved to: {output_file}")


def main():
    """Run tests for both PDFs"""
    print("=" * 70)
    print("COMPREHENSIVE E2E TEST - Expected vs Actual Outputs")
    print("=" * 70)
    
    # Test sample.pdf
    sample_pdf = find_pdf("sample.pdf")
    if sample_pdf:
        dashboard_sample = run_full_pipeline(sample_pdf, "sample.pdf")
        if dashboard_sample:
            analyze_results(dashboard_sample, EXPECTED_SAMPLE, "sample.pdf")
    else:
        print("[ERROR] sample.pdf not found")
    
    # Test consolidated report
    consolidated_pdf = find_pdf("INSTITUTE INFORMATION CONSOLIDATED REPORT.pdf")
    if consolidated_pdf:
        dashboard_consolidated = run_full_pipeline(consolidated_pdf, "INSTITUTE INFORMATION CONSOLIDATED REPORT.pdf")
        if dashboard_consolidated:
            analyze_results(dashboard_consolidated, EXPECTED_CONSOLIDATED, "INSTITUTE INFORMATION CONSOLIDATED REPORT.pdf")
    else:
        print("[ERROR] INSTITUTE INFORMATION CONSOLIDATED REPORT.pdf not found")
    
    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()

