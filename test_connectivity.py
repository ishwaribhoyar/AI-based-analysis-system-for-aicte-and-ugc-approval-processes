"""
Comprehensive Frontend-Backend Connectivity Test
Tests all API endpoints and verifies connectivity
"""

import requests
import json
from typing import Dict, List, Tuple

BASE_URL = "http://127.0.0.1:8000"
API_BASE = f"{BASE_URL}/api"

def test_endpoint(method: str, endpoint: str, data: dict = None, params: dict = None) -> Tuple[bool, str, dict]:
    """Test a single endpoint"""
    url = f"{API_BASE}{endpoint}" if endpoint.startswith("/") else f"{API_BASE}/{endpoint}"
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, params=params, timeout=5)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, timeout=5)
        elif method.upper() == "DELETE":
            response = requests.delete(url, timeout=5)
        else:
            return False, f"Unsupported method: {method}", {}
        
        success = response.status_code < 400
        status_text = f"Status: {response.status_code}"
        
        try:
            response_data = response.json()
        except:
            response_data = {"text": response.text[:200]}
        
        return success, status_text, response_data
    except requests.exceptions.ConnectionError:
        return False, "Connection refused - Backend not running", {}
    except requests.exceptions.Timeout:
        return False, "Request timeout", {}
    except Exception as e:
        return False, f"Error: {str(e)}", {}

def main():
    print("=" * 80)
    print("FRONTEND-BACKEND CONNECTIVITY TEST")
    print("=" * 80)
    print()
    
    # Test 1: Basic connectivity
    print("1. Testing Basic Connectivity...")
    print("-" * 80)
    
    health_success, health_msg, health_data = test_endpoint("GET", "/health")
    root_success, root_msg, root_data = test_endpoint("GET", "/")
    
    print(f"  Health Check: {'✓' if health_success else '✗'} {health_msg}")
    if health_data:
        print(f"    Response: {json.dumps(health_data, indent=2)[:100]}")
    
    print(f"  Root Endpoint: {'✓' if root_success else '✗'} {root_msg}")
    print()
    
    if not health_success:
        print("❌ Backend server is not running!")
        print("   Please start the backend server first:")
        print("   cd backend && python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload")
        return
    
    # Test 2: Batch endpoints
    print("2. Testing Batch Endpoints...")
    print("-" * 80)
    
    # Create a test batch
    create_success, create_msg, create_data = test_endpoint("POST", "/batches/create", {
        "mode": "aicte",
        "new_university": False
    })
    print(f"  POST /batches/create: {'✓' if create_success else '✗'} {create_msg}")
    
    batch_id = None
    if create_success and "batch_id" in create_data:
        batch_id = create_data["batch_id"]
        print(f"    Created batch: {batch_id}")
    
    # List batches
    list_success, list_msg, list_data = test_endpoint("GET", "/batches/list")
    print(f"  GET /batches/list: {'✓' if list_success else '✗'} {list_msg}")
    
    # Get batch
    if batch_id:
        get_success, get_msg, get_data = test_endpoint("GET", f"/batches/{batch_id}")
        print(f"  GET /batches/{batch_id}: {'✓' if get_success else '✗'} {get_msg}")
    print()
    
    # Test 3: Processing endpoints
    print("3. Testing Processing Endpoints...")
    print("-" * 80)
    
    if batch_id:
        status_success, status_msg, status_data = test_endpoint("GET", f"/processing/status/{batch_id}")
        print(f"  GET /processing/status/{batch_id}: {'✓' if status_success else '✗'} {status_msg}")
        
        start_success, start_msg, start_data = test_endpoint("POST", "/processing/start", {
            "batch_id": batch_id
        })
        print(f"  POST /processing/start: {'✓' if start_success else '✗'} {start_msg}")
    else:
        print("  ⚠ Skipping (no batch_id)")
    print()
    
    # Test 4: Dashboard endpoints
    print("4. Testing Dashboard Endpoints...")
    print("-" * 80)
    
    if batch_id:
        dashboard_success, dashboard_msg, dashboard_data = test_endpoint("GET", f"/dashboard/{batch_id}")
        print(f"  GET /dashboard/{batch_id}: {'✓' if dashboard_success else '✗'} {dashboard_msg}")
        
        kpi_success, kpi_msg, kpi_data = test_endpoint("GET", f"/dashboard/kpi-details/{batch_id}")
        print(f"  GET /dashboard/kpi-details/{batch_id}: {'✓' if kpi_success else '✗'} {kpi_msg}")
        
        trends_success, trends_msg, trends_data = test_endpoint("GET", f"/dashboard/trends/{batch_id}")
        print(f"  GET /dashboard/trends/{batch_id}: {'✓' if trends_success else '✗'} {trends_msg}")
    else:
        print("  ⚠ Skipping (no batch_id)")
    print()
    
    # Test 5: Document endpoints
    print("5. Testing Document Endpoints...")
    print("-" * 80)
    
    if batch_id:
        doc_list_success, doc_list_msg, doc_list_data = test_endpoint("GET", f"/documents/batch/{batch_id}")
        print(f"  GET /documents/batch/{batch_id}: {'✓' if doc_list_success else '✗'} {doc_list_msg}")
    else:
        print("  ⚠ Skipping (no batch_id)")
    print()
    
    # Test 6: Other endpoints
    print("6. Testing Other Endpoints...")
    print("-" * 80)
    
    if batch_id:
        approval_success, approval_msg, approval_data = test_endpoint("GET", f"/approval/{batch_id}")
        print(f"  GET /approval/{batch_id}: {'✓' if approval_success else '✗'} {approval_msg}")
        
        unified_success, unified_msg, unified_data = test_endpoint("GET", f"/unified-report/{batch_id}")
        print(f"  GET /unified-report/{batch_id}: {'✓' if unified_success else '✗'} {unified_msg}")
    else:
        print("  ⚠ Skipping (no batch_id)")
    print()
    
    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Backend URL: {BASE_URL}")
    print(f"API Base: {API_BASE}")
    print(f"Backend Status: {'✓ Running' if health_success else '✗ Not Running'}")
    print()
    print("Frontend should be configured to use:")
    print(f"  NEXT_PUBLIC_API_BASE={API_BASE}")
    print()
    
    # Check frontend configuration
    try:
        with open("frontend/lib/api.ts", "r") as f:
            api_content = f.read()
            if API_BASE in api_content or "127.0.0.1:8000" in api_content:
                print("✓ Frontend API configuration looks correct")
            else:
                print("⚠ Frontend API configuration may need updating")
    except:
        print("⚠ Could not verify frontend API configuration")
    
    print()
    print("=" * 80)

if __name__ == "__main__":
    main()
