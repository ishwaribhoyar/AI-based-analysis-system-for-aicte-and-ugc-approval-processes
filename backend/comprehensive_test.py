"""
Comprehensive Backend Test Script
Tests all features with multiple PDFs
"""
import sys
import os
import time
import requests
from pathlib import Path

API_BASE = "http://localhost:8000"

def check_server():
    """Check if server is running"""
    try:
        r = requests.get(f"{API_BASE}/", timeout=3)
        return r.status_code == 200
    except:
        return False

def wait_for_server(max_wait=30):
    """Wait for server to be ready"""
    for i in range(max_wait):
        if check_server():
            return True
        time.sleep(1)
        print(f"⏳ Waiting for server... ({i+1}/{max_wait})")
    return False

def test_sample_pdf():
    """Test with sample.pdf"""
    print("\n" + "="*70)
    print("TEST 1: sample.pdf (AICTE)")
    print("="*70)
    
    # Create batch
    r = requests.post(f"{API_BASE}/api/batches/create", json={"mode": "aicte"})
    batch_id = r.json().get("batch_id")
    print(f"✓ Batch created: {batch_id}")
    
    # Upload
    pdf_path = Path(__file__).parent.parent / "sample.pdf"
    if not pdf_path.exists():
        print(f"⚠️  sample.pdf not found at {pdf_path}")
        return False
    
    with open(pdf_path, 'rb') as f:
        files = {'file': ('sample.pdf', f, 'application/pdf')}
        data = {'batch_id': batch_id}
        r = requests.post(f"{API_BASE}/api/documents/{batch_id}/upload", files=files, data=data)
        print(f"✓ Uploaded: sample.pdf")
    
    # Start processing
    r = requests.post(f"{API_BASE}/api/processing/start", json={"batch_id": batch_id})
    print(f"✓ Processing started")
    
    # Poll status
    max_wait = 600
    start_time = time.time()
    while time.time() - start_time < max_wait:
        r = requests.get(f"{API_BASE}/api/processing/status/{batch_id}")
        status = r.json()
        progress = status.get("progress", 0)
        stage = status.get("current_stage", "unknown")
        print(f"  Status: {stage} ({progress}%)")
        
        if status.get("status") == "completed":
            print("✓ Processing completed!")
            break
        elif status.get("status") == "failed":
            print("❌ Processing failed!")
            return False
        
        time.sleep(5)
    else:
        print("❌ Processing timeout!")
        return False
    
    # Check dashboard
    r = requests.get(f"{API_BASE}/api/dashboard/{batch_id}")
    dashboard = r.json()
    sufficiency = dashboard.get("sufficiency", {}).get("percentage", 0)
    kpis = dashboard.get("kpis", {})
    
    print(f"\n✓ Dashboard retrieved:")
    print(f"  Sufficiency: {sufficiency}%")
    print(f"  KPIs: {len(kpis)} metrics")
    
    # Verify expected values
    assert sufficiency >= 90, f"Sufficiency {sufficiency}% < 90%"
    assert "overall_score" in kpis or "aicte_overall_score" in kpis, "Missing overall score"
    
    print("✅ TEST 1 PASSED")
    return True

def test_consolidated_report():
    """Test with consolidated report"""
    print("\n" + "="*70)
    print("TEST 2: INSTITUTE INFORMATION CONSOLIDATED REPORT.pdf (AICTE)")
    print("="*70)
    
    r = requests.post(f"{API_BASE}/api/batches/create", json={"mode": "aicte"})
    batch_id = r.json().get("batch_id")
    
    pdf_path = Path(__file__).parent.parent / "INSTITUTE INFORMATION CONSOLIDATED REPORT.pdf"
    if not pdf_path.exists():
        print(f"⚠️  Consolidated report not found")
        return False
    
    with open(pdf_path, 'rb') as f:
        files = {'file': (pdf_path.name, f, 'application/pdf')}
        data = {'batch_id': batch_id}
        requests.post(f"{API_BASE}/api/documents/{batch_id}/upload", files=files, data=data)
    
    requests.post(f"{API_BASE}/api/processing/start", json={"batch_id": batch_id})
    
    # Poll
    start_time = time.time()
    while time.time() - start_time < 600:
        r = requests.get(f"{API_BASE}/api/processing/status/{batch_id}")
        status = r.json()
        if status.get("status") == "completed":
            print("✓ Processing completed!")
            break
        elif status.get("status") == "failed":
            print("❌ Processing failed!")
            return False
        time.sleep(5)
    else:
        print("❌ Timeout!")
        return False
    
    r = requests.get(f"{API_BASE}/api/dashboard/{batch_id}")
    dashboard = r.json()
    print(f"✓ Sufficiency: {dashboard.get('sufficiency', {}).get('percentage', 0)}%")
    print("✅ TEST 2 PASSED")
    return True

def test_ugc_mode():
    """Test UGC mode"""
    print("\n" + "="*70)
    print("TEST 3: Consolidated Report (UGC MODE)")
    print("="*70)
    
    r = requests.post(f"{API_BASE}/api/batches/create", json={"mode": "ugc"})
    batch_id = r.json().get("batch_id")
    
    pdf_path = Path(__file__).parent.parent / "INSTITUTE INFORMATION CONSOLIDATED REPORT.pdf"
    if not pdf_path.exists():
        return False
    
    with open(pdf_path, 'rb') as f:
        files = {'file': (pdf_path.name, f, 'application/pdf')}
        data = {'batch_id': batch_id}
        requests.post(f"{API_BASE}/api/documents/{batch_id}/upload", files=files, data=data)
    
    requests.post(f"{API_BASE}/api/processing/start", json={"batch_id": batch_id})
    
    start_time = time.time()
    while time.time() - start_time < 600:
        r = requests.get(f"{API_BASE}/api/processing/status/{batch_id}")
        status = r.json()
        if status.get("status") == "completed":
            print("✓ Processing completed!")
            break
        elif status.get("status") == "failed":
            return False
        time.sleep(5)
    else:
        return False
    
    print("✅ TEST 3 PASSED")
    return True

if __name__ == "__main__":
    print("="*70)
    print("COMPREHENSIVE BACKEND TEST SUITE")
    print("="*70)
    
    if not wait_for_server():
        print("❌ Server not available. Please start backend server first.")
        print("   Run: cd backend && python -m uvicorn main:app --host 127.0.0.1 --port 8000")
        sys.exit(1)
    
    print("✅ Server is running")
    
    results = []
    results.append(("Sample PDF (AICTE)", test_sample_pdf()))
    results.append(("Consolidated Report (AICTE)", test_consolidated_report()))
    results.append(("Consolidated Report (UGC)", test_ugc_mode()))
    
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED!")
        sys.exit(0)
    else:
        print("⚠️  Some tests failed")
        sys.exit(1)

