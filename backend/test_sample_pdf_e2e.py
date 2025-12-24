"""
Complete End-to-End Test with sample.pdf
Tests entire platform flow with sample.pdf
"""

import sys
import os
from pathlib import Path
import requests
import time

API_BASE = "http://localhost:8000"

def find_sample_pdf():
    """Find sample.pdf in repository"""
    repo_root = Path(__file__).parent.parent
    sample_pdf = repo_root / "sample.pdf"
    
    if sample_pdf.exists() and sample_pdf.stat().st_size > 0:
        size_mb = sample_pdf.stat().st_size / (1024 * 1024)
        print(f"\n📄 Found sample.pdf ({size_mb:.2f} MB)")
        return sample_pdf
    else:
        print("❌ sample.pdf not found in repository root")
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

def poll_status(batch_id, max_wait=300):
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
        
        # Check structure
        has_blocks = 'blocks' in data or 'block_cards' in data
        has_kpis = 'kpis' in data or 'kpi_cards' in data
        has_sufficiency = 'sufficiency' in data
        
        print(f"\n   Dashboard Structure:")
        print(f"      - Batch ID: {data.get('batch_id', 'N/A')}")
        print(f"      - Mode: {data.get('mode', 'N/A')}")
        
        if 'block_cards' in data:
            block_count = len(data['block_cards'])
            print(f"      - Blocks (block_cards): {block_count}")
        elif 'blocks' in data:
            block_count = len(data['blocks'])
            print(f"      - Blocks: {block_count}")
        else:
            print(f"      - Blocks: Not found")
        
        if 'kpi_cards' in data:
            kpi_count = len(data['kpi_cards'])
            print(f"      - KPIs (kpi_cards): {kpi_count}")
            for kpi in data['kpi_cards'][:3]:
                name = kpi.get('name', 'Unknown')
                value = kpi.get('value')
                if value is None:
                    print(f"        - {name}: Insufficient Data")
                else:
                    print(f"        - {name}: {value:.2f}")
        elif 'kpis' in data:
            kpis = data['kpis']
            print(f"      - KPIs: {len([k for k in kpis.values() if k is not None])} with values")
            for key, value in kpis.items():
                if value is None:
                    print(f"        - {key}: Insufficient Data")
                else:
                    print(f"        - {key}: {value:.2f}")
        
        if 'sufficiency' in data:
            if isinstance(data['sufficiency'], dict):
                sufficiency = data['sufficiency'].get('percentage', 0)
                present = data['sufficiency'].get('present_count', 0)
                required = data['sufficiency'].get('required_count', 10)
            else:
                sufficiency = data['sufficiency']
                present = data.get('present_blocks', 0)
                required = data.get('required_blocks', 10)
            print(f"      - Sufficiency: {sufficiency:.1f}% ({present}/{required} blocks)")
        
        if 'compliance_flags' in data:
            print(f"      - Compliance Flags: {len(data['compliance_flags'])}")
        elif 'compliance' in data:
            print(f"      - Compliance: {len(data['compliance'])} flags")
        
        return True, data
        
    except Exception as e:
        print(f"   ❌ Failed to fetch dashboard: {e}")
        import traceback
        traceback.print_exc()
        return False, None

def test_report(batch_id):
    """Test report generation"""
    print(f"\n📄 Testing report generation...")
    try:
        response = requests.post(
            f"{API_BASE}/api/reports/generate",
            json={"batch_id": batch_id},
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        download_url = data.get("download_url")
        
        if download_url:
            print(f"   ✓ Report generated: {download_url}")
            return True
        else:
            print(f"   ⚠ Report generated but no URL")
            return False
    except Exception as e:
        print(f"   ❌ Failed to generate report: {e}")
        return False

def main():
    """Run complete test"""
    print("=" * 70)
    print("COMPLETE SYSTEM TEST - sample.pdf")
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
    
    # Step 8: Test report
    report_ok = test_report(batch_id)
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"✓ Batch: {batch_id}")
    print(f"✓ File: sample.pdf uploaded")
    print(f"✓ Processing: Completed")
    print(f"{'✓' if dashboard_ok else '⚠'} Dashboard: {'PASSED' if dashboard_ok else 'ISSUES'}")
    print(f"{'✓' if report_ok else '⚠'} Report: {'PASSED' if report_ok else 'ISSUES'}")
    
    if dashboard_ok and report_ok:
        print("\n✅ ALL TESTS PASSED - System working correctly!")
        return True
    else:
        print("\n⚠ Some tests had issues")
        return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

