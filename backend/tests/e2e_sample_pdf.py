"""
End-to-End Integration Test for sample.pdf
Tests complete flow: batch creation → upload → processing → dashboard → assertions
"""

import sys
import os
from pathlib import Path
import requests
import time
import json

API_BASE = "http://localhost:8000"

def find_sample_pdf():
    """Find sample.pdf in repository"""
    repo_root = Path(__file__).parent.parent.parent
    sample_pdf = repo_root / "sample.pdf"
    
    # Also check /mnt/data/sample.pdf (as specified in requirements)
    if not sample_pdf.exists():
        sample_pdf = Path("/mnt/data/sample.pdf")
    
    if sample_pdf.exists() and sample_pdf.stat().st_size > 0:
        size_mb = sample_pdf.stat().st_size / (1024 * 1024)
        print(f"\n📄 Found sample.pdf ({size_mb:.2f} MB) at {sample_pdf}")
        return sample_pdf
    else:
        print("❌ sample.pdf not found")
        return None

def test_backend_api():
    """Test backend API"""
    print("\n🔍 Testing Backend API...")
    try:
        response = requests.get(f"{API_BASE}/", timeout=5)
        print(f"   ✓ Backend is reachable (status: {response.status_code})")
        return True
    except Exception as e:
        print(f"   ❌ Backend not reachable: {e}")
        return False

def create_batch(mode="aicte"):
    """Create batch via API"""
    print(f"\n📦 Creating batch via API (mode: {mode})...")
    try:
        response = requests.post(
            f"{API_BASE}/api/batches/create",
            json={"mode": mode},
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        batch_id = data.get("batch_id") or data.get("id")
        print(f"   ✓ Batch created: {batch_id}")
        return batch_id
    except Exception as e:
        print(f"   ❌ Failed to create batch: {e}")
        return None

def upload_file(batch_id, file_path):
    """Upload file via API"""
    try:
        with open(file_path, 'rb') as f:
            files = {'file': (file_path.name, f, 'application/pdf')}
            data = {'batch_id': batch_id}
            response = requests.post(
                f"{API_BASE}/api/documents/{batch_id}/upload",
                files=files,
                data=data,
                timeout=30
            )
            response.raise_for_status()
            return True
    except Exception as e:
        print(f"   ❌ Failed to upload {file_path.name}: {e}")
        return False

def start_processing(batch_id):
    """Start processing"""
    print(f"\n🚀 Starting processing for batch {batch_id}...")
    try:
        response = requests.post(
            f"{API_BASE}/api/processing/start",
            json={"batch_id": batch_id},
            timeout=10
        )
        response.raise_for_status()
        print(f"   ✓ Processing started")
        return True
    except Exception as e:
        print(f"   ❌ Failed to start processing: {e}")
        return False

def poll_status(batch_id, max_wait=600):
    """Poll processing status"""
    print(f"\n⏳ Polling processing status...")
    start_time = time.time()
    while time.time() - start_time < max_wait:
        try:
            response = requests.get(
                f"{API_BASE}/api/processing/status/{batch_id}",
                timeout=5
            )
            response.raise_for_status()
            status_data = response.json()
            status = status_data.get("status", "unknown")
            
            processed = status_data.get("processed_documents", 0)
            total = status_data.get("total_documents", 0)
            
            print(f"   Status: {status} ({processed}/{total} documents)", end='\r')
            
            if status == "completed":
                print(f"\n   ✓ Processing completed!")
                return True
            elif status == "failed":
                print(f"\n   ❌ Processing failed!")
                return False
            
            time.sleep(2)
        except Exception as e:
            print(f"\n   ⚠ Error polling: {e}")
            time.sleep(2)
    
    print(f"\n   ❌ Processing timeout")
    return False

def fetch_dashboard(batch_id):
    """Fetch and verify dashboard"""
    print(f"\n📊 Fetching dashboard data...")
    try:
        response = requests.get(
            f"{API_BASE}/api/dashboard/{batch_id}",
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        
        print(f"   ✓ Dashboard data retrieved")
        return True, data
        
    except Exception as e:
        print(f"   ❌ Failed to fetch dashboard: {e}")
        import traceback
        traceback.print_exc()
        return False, None

def assert_dashboard(data):
    """Assert dashboard data meets acceptance criteria"""
    print(f"\n✅ Running assertions...")
    failures = []
    
    # 1. Sufficiency >= 90
    sufficiency = None
    if isinstance(data.get("sufficiency"), dict):
        sufficiency = data["sufficiency"].get("percentage", 0)
    else:
        sufficiency = data.get("sufficiency", 0)
    
    if sufficiency < 90:
        failures.append(f"Sufficiency {sufficiency:.1f}% < 90%")
    else:
        print(f"   ✓ Sufficiency: {sufficiency:.1f}% >= 90%")
    
    # 2. Blocks length == 10
    blocks = data.get("blocks") or data.get("block_cards", [])
    if len(blocks) != 10:
        failures.append(f"Blocks count {len(blocks)} != 10")
    else:
        print(f"   ✓ Blocks: {len(blocks)} == 10")
    
    # 3. At least 4 KPI metrics are numeric (not None)
    kpis = data.get("kpis") or {}
    if isinstance(data.get("kpi_cards"), list):
        # Transform kpi_cards to kpis dict
        kpis = {}
        for card in data["kpi_cards"]:
            name = card.get("name", "")
            value = card.get("value")
            # Map to kpi keys
            if "FSR" in name:
                kpis["fsr_score"] = value
            elif "Infrastructure" in name:
                kpis["infrastructure_score"] = value
            elif "Placement" in name:
                kpis["placement_index"] = value
            elif "Lab" in name:
                kpis["lab_compliance_index"] = value
            elif "Overall" in name:
                kpis["overall_score"] = value
    
    numeric_kpis = sum(1 for v in kpis.values() if v is not None and isinstance(v, (int, float)))
    if numeric_kpis < 4:
        failures.append(f"Numeric KPIs {numeric_kpis} < 4")
    else:
        print(f"   ✓ Numeric KPIs: {numeric_kpis} >= 4")
    
    # 4. faculty_information.data.faculty_count_num == 82
    faculty_block = None
    for block in blocks:
        block_type = block.get("block_type", "")
        if block_type == "faculty_information":
            faculty_block = block
            break
    
    if not faculty_block:
        failures.append("faculty_information block not found")
    else:
        block_data = faculty_block.get("data", {})
        faculty_count_num = block_data.get("faculty_count_num") or block_data.get("total_faculty_num")
        if faculty_count_num != 82:
            failures.append(f"faculty_count_num {faculty_count_num} != 82")
        else:
            print(f"   ✓ faculty_count_num: {faculty_count_num} == 82")
    
    # 5. placement_information.data.placement_rate_num == 84.7
    placement_block = None
    for block in blocks:
        block_type = block.get("block_type", "")
        if block_type == "placement_information":
            placement_block = block
            break
    
    if not placement_block:
        failures.append("placement_information block not found")
    else:
        block_data = placement_block.get("data", {})
        placement_rate_num = block_data.get("placement_rate_num")
        if placement_rate_num is None:
            # Try parsing from raw value
            placement_rate = block_data.get("placement_rate")
            if placement_rate:
                from utils.parse_numeric import parse_numeric
                placement_rate_num = parse_numeric(str(placement_rate))
        
        if placement_rate_num is None or abs(placement_rate_num - 84.7) > 0.1:
            failures.append(f"placement_rate_num {placement_rate_num} != 84.7")
        else:
            print(f"   ✓ placement_rate_num: {placement_rate_num} == 84.7")
    
    # 6. overall_score is numeric
    overall_score = kpis.get("overall_score")
    if overall_score is None:
        failures.append("overall_score is None")
    else:
        print(f"   ✓ overall_score: {overall_score} (numeric)")
    
    return failures

def main():
    """Run complete e2e test"""
    print("=" * 70)
    print("E2E INTEGRATION TEST - sample.pdf")
    print("=" * 70)
    
    # Step 1: Test backend
    if not test_backend_api():
        print("\n❌ Backend not available")
        return False
    
    # Step 2: Find sample.pdf
    sample_pdf = find_sample_pdf()
    if not sample_pdf:
        return False
    
    # Step 3: Create batch
    batch_id = create_batch("aicte")
    if not batch_id:
        return False
    
    # Step 4: Upload sample.pdf
    print(f"\n📤 Uploading sample.pdf...")
    if not upload_file(batch_id, sample_pdf):
        return False
    print(f"   ✓ Uploaded: sample.pdf")
    
    # Step 5: Start processing
    if not start_processing(batch_id):
        return False
    
    # Step 6: Poll until complete
    if not poll_status(batch_id, max_wait=600):
        return False
    
    # Step 7: Fetch dashboard
    dashboard_ok, dashboard_data = fetch_dashboard(batch_id)
    if not dashboard_ok:
        return False
    
    # Step 8: Run assertions
    failures = assert_dashboard(dashboard_data)
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"✓ Batch: {batch_id}")
    print(f"✓ File: sample.pdf uploaded")
    print(f"✓ Processing: Completed")
    print(f"✓ Dashboard: Retrieved")
    
    if failures:
        print(f"\n❌ FAILURES ({len(failures)}):")
        for failure in failures:
            print(f"   - {failure}")
        return False
    else:
        print("\n✅ ALL ASSERTIONS PASSED - SAMPLE.PDF PASS")
        return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

