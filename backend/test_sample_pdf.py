"""
Test script to upload and process sample.pdf, checking for errors.
"""

import requests
import time
import os
import sys
from pathlib import Path

API_BASE = "http://localhost:8000"

def test_sample_pdf():
    """Test processing sample.pdf end-to-end."""
    print("=" * 70)
    print("TESTING SAMPLE.PDF PROCESSING")
    print("=" * 70)
    
    # Check if backend is running
    try:
        r = requests.get(f"{API_BASE}/api/batches/list", timeout=5)
        # Any response (even 200 or 404) means backend is running
        print("[OK] Backend is reachable")
    except Exception as e:
        print(f"[ERROR] Backend is not reachable: {e}")
        print("   Please start the backend server first")
        return False
    
    # Find sample.pdf
    project_root = Path(__file__).parent.parent
    sample_pdf = project_root / "sample.pdf"
    
    if not sample_pdf.exists():
        print(f"[ERROR] sample.pdf not found at {sample_pdf}")
        return False
    
    print(f"[OK] Found sample.pdf ({sample_pdf.stat().st_size / 1024:.2f} KB)")
    
    # Create batch
    try:
        r = requests.post(
            f"{API_BASE}/api/batches/",
            json={"mode": "aicte", "new_university": False}
        )
        r.raise_for_status()
        batch_data = r.json()
        batch_id = batch_data["batch_id"]
        print(f"[OK] Created batch: {batch_id}")
    except Exception as e:
        print(f"[ERROR] Failed to create batch: {e}")
        return False
    
    # Upload sample.pdf
    try:
        with open(sample_pdf, "rb") as f:
            files = {"file": ("sample.pdf", f, "application/pdf")}
            r = requests.post(
                f"{API_BASE}/api/documents/{batch_id}/upload",
                files=files
            )
            r.raise_for_status()
            print("[OK] Uploaded sample.pdf")
    except Exception as e:
        print(f"[ERROR] Failed to upload: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   Response: {e.response.text}")
        return False
    
    # Start processing
    try:
        r = requests.post(
            f"{API_BASE}/api/processing/start",
            json={"batch_id": batch_id}
        )
        r.raise_for_status()
        print("[OK] Processing started")
    except Exception as e:
        print(f"[ERROR] Failed to start processing: {e}")
        return False
    
    # Poll for status
    print("\n[INFO] Polling processing status...")
    max_wait = 300  # 5 minutes max
    start_time = time.time()
    last_status = None
    
    while time.time() - start_time < max_wait:
        try:
            r = requests.get(f"{API_BASE}/api/processing/status/{batch_id}")
            r.raise_for_status()
            status_data = r.json()
            
            status = status_data.get("status", "unknown")
            progress = status_data.get("progress", 0)
            current_stage = status_data.get("current_stage", "")
            error = status_data.get("error")
            
            # Print status if it changed
            if status != last_status:
                print(f"   Status: {status} ({progress}%) - {current_stage}")
                last_status = status
            
            if status == "completed":
                print("\n[SUCCESS] Processing completed successfully!")
                
                # Check results
                print("\n[INFO] Checking results...")
                
                # Get dashboard data
                try:
                    r = requests.get(f"{API_BASE}/api/dashboard/{batch_id}")
                    r.raise_for_status()
                    dashboard = r.json()
                    
                    print(f"   [OK] Sufficiency: {dashboard.get('sufficiency', {}).get('percentage', 0):.1f}%")
                    print(f"   [OK] KPIs: {len(dashboard.get('kpis', {}))} metrics")
                    print(f"   [OK] Compliance flags: {len(dashboard.get('compliance_flags', []))}")
                    
                    # Check approval readiness
                    approval = dashboard.get('approval_readiness', {})
                    if approval:
                        print(f"   [OK] Approval readiness: {approval.get('readiness_score', 0):.1f}%")
                        print(f"     Present docs: {approval.get('present_documents', 0)}")
                        print(f"     Missing docs: {len(approval.get('missing_documents', []))}")
                    
                except Exception as e:
                    print(f"   [WARN] Could not fetch dashboard: {e}")
                
                return True
            
            elif status == "failed":
                print(f"\n[ERROR] Processing failed!")
                if error:
                    print(f"   Error: {error}")
                
                # Try to get more details from logs
                print("\n[INFO] Checking error details...")
                try:
                    r = requests.get(f"{API_BASE}/api/processing/status/{batch_id}")
                    status_data = r.json()
                    print(f"   Full status: {status_data}")
                    if "error_details" in status_data:
                        print(f"   Details: {status_data['error_details']}")
                    if "error" in status_data:
                        print(f"   Error message: {status_data['error']}")
                    
                    # Also check batch errors from database
                    r2 = requests.get(f"{API_BASE}/api/batches/{batch_id}")
                    if r2.status_code == 200:
                        batch_info = r2.json()
                        if "errors" in batch_info:
                            print(f"   Batch errors: {batch_info['errors']}")
                except Exception as e:
                    print(f"   Could not get error details: {e}")
                
                return False
            
            time.sleep(2)
            
        except Exception as e:
            print(f"[ERROR] Error polling status: {e}")
            return False
    
    print(f"\n[TIMEOUT] Timeout after {max_wait} seconds")
    return False


if __name__ == "__main__":
    success = test_sample_pdf()
    sys.exit(0 if success else 1)
