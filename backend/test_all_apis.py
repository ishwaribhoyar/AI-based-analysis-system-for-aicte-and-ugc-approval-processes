"""
Comprehensive Backend API Test Suite
Tests all endpoints to ensure they work correctly.
"""

import requests
import json
import time
import sys

BASE_URL = "http://localhost:8000/api"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def log_success(msg):
    print(f"{Colors.GREEN}✓ {msg}{Colors.END}")

def log_error(msg):
    print(f"{Colors.RED}✗ {msg}{Colors.END}")

def log_info(msg):
    print(f"{Colors.BLUE}→ {msg}{Colors.END}")

def log_warning(msg):
    print(f"{Colors.YELLOW}⚠ {msg}{Colors.END}")

results = {"passed": 0, "failed": 0, "warnings": 0}

def test_endpoint(name, method, endpoint, expected_status=200, data=None, check_fields=None):
    """Test an API endpoint."""
    global results
    url = f"{BASE_URL}{endpoint}"
    try:
        if method == "GET":
            r = requests.get(url, timeout=30)
        elif method == "POST":
            r = requests.post(url, json=data, timeout=30)
        else:
            log_error(f"Unknown method: {method}")
            return None
        
        if r.status_code == expected_status:
            log_success(f"{name} - Status {r.status_code}")
            results["passed"] += 1
            
            # Check response fields if specified
            if check_fields and r.status_code == 200:
                try:
                    resp = r.json()
                    missing = [f for f in check_fields if f not in resp]
                    if missing:
                        log_warning(f"  Missing fields: {missing}")
                        results["warnings"] += 1
                except:
                    pass
            
            return r.json() if r.status_code == 200 else None
        else:
            log_error(f"{name} - Expected {expected_status}, got {r.status_code}")
            if r.status_code >= 400:
                try:
                    print(f"  Error: {r.json().get('detail', r.text[:200])}")
                except:
                    print(f"  Response: {r.text[:200]}")
            results["failed"] += 1
            return None
    except requests.exceptions.ConnectionError:
        log_error(f"{name} - Connection refused (is backend running?)")
        results["failed"] += 1
        return None
    except Exception as e:
        log_error(f"{name} - Exception: {str(e)}")
        results["failed"] += 1
        return None

def main():
    print("\n" + "="*60)
    print("🔍 COMPREHENSIVE BACKEND API TEST")
    print("="*60 + "\n")
    
    # 1. Health Check
    print("📋 1. HEALTH CHECK")
    print("-"*40)
    test_endpoint("Health Check", "GET", "/health", check_fields=["status"])
    print()
    
    # 2. Batch APIs
    print("📋 2. BATCH APIs")
    print("-"*40)
    
    # List batches
    batches = test_endpoint("List Batches", "GET", "/batches/list", check_fields=[])
    batch_ids = []
    if batches and isinstance(batches, list):
        log_info(f"  Found {len(batches)} batches")
        batch_ids = [b.get("batch_id") for b in batches[:3] if b.get("batch_id")]
    
    # Create batch
    new_batch = test_endpoint(
        "Create AICTE Batch", "POST", "/batches/create",
        data={"mode": "aicte"},
        check_fields=["batch_id", "mode", "status"]
    )
    if new_batch:
        log_info(f"  Created: {new_batch.get('batch_id')}")
    
    # Create UGC batch
    ugc_batch = test_endpoint(
        "Create UGC Batch", "POST", "/batches/create",
        data={"mode": "ugc"},
        check_fields=["batch_id"]
    )
    
    # Create Mixed batch
    mixed_batch = test_endpoint(
        "Create Mixed Batch", "POST", "/batches/create",
        data={"mode": "mixed"},
        check_fields=["batch_id"]
    )
    print()
    
    # 3. Dashboard API
    print("📋 3. DASHBOARD API")
    print("-"*40)
    
    if batch_ids:
        bid = batch_ids[0]
        dashboard = test_endpoint(
            f"Dashboard ({bid[:20]}...)", "GET", f"/dashboard/{bid}",
            check_fields=["batch_id", "kpis", "sufficiency", "compliance_flags"]
        )
        if dashboard:
            log_info(f"  KPIs: {list(dashboard.get('kpis', {}).keys())[:5]}")
            log_info(f"  Sufficiency: {dashboard.get('sufficiency', {}).get('percentage', 'N/A')}%")
            log_info(f"  Compliance Flags: {len(dashboard.get('compliance_flags', []))}")
    else:
        log_warning("No batches available to test dashboard")
        results["warnings"] += 1
    print()
    
    # 4. Compare API
    print("📋 4. COMPARE API")
    print("-"*40)
    
    if len(batch_ids) >= 2:
        compare_ids = ",".join(batch_ids[:2])
        comparison = test_endpoint(
            "Compare Institutions", "GET", f"/compare?batch_ids={compare_ids}",
            check_fields=["institutions", "comparison_matrix", "winner_institution", "category_winners"]
        )
        if comparison:
            insts = comparison.get("institutions", [])
            log_info(f"  Institutions compared: {len(insts)}")
            for inst in insts:
                label = inst.get("short_label", "???")
                score = inst.get("overall_score", 0)
                log_info(f"    - {label}: {score:.1f}")
            winner = comparison.get("winner_label")
            if winner:
                log_info(f"  Winner: {winner}")
    else:
        log_warning("Need at least 2 batches to test comparison")
        results["warnings"] += 1
    print()
    
    # 5. Approval API
    print("📋 5. APPROVAL API")
    print("-"*40)
    
    if batch_ids:
        bid = batch_ids[0]
        approval = test_endpoint(
            f"Approval Status ({bid[:20]}...)", "GET", f"/approval/{bid}",
            check_fields=["batch_id", "classification", "required_documents", "readiness_score"]
        )
        if approval:
            log_info(f"  Category: {approval.get('classification', {}).get('category', 'N/A')}")
            log_info(f"  Subtype: {approval.get('classification', {}).get('subtype', 'N/A')}")
            log_info(f"  Readiness: {approval.get('readiness_score', 0)}%")
            log_info(f"  Missing Docs: {len(approval.get('missing_documents', []))}")
    else:
        log_warning("No batches available to test approval")
        results["warnings"] += 1
    print()
    
    # 6. Unified Report API
    print("📋 6. UNIFIED REPORT API")
    print("-"*40)
    
    if batch_ids:
        bid = batch_ids[0]
        unified = test_endpoint(
            f"Unified Report ({bid[:20]}...)", "GET", f"/unified-report/{bid}",
            check_fields=["batch_id", "aicte_summary", "ugc_summary"]
        )
        if unified:
            aicte_summary = unified.get('aicte_summary') or {}
            ugc_summary = unified.get('ugc_summary') or {}
            log_info(f"  AICTE Score: {aicte_summary.get('overall_score', 'N/A')}")
            log_info(f"  UGC Score: {ugc_summary.get('overall_score', 'N/A')}")
    else:
        log_warning("No batches available to test unified report")
        results["warnings"] += 1
    print()
    
    # 7. Chatbot API
    print("📋 7. CHATBOT API")
    print("-"*40)
    
    if batch_ids:
        bid = batch_ids[0]
        chat_resp = test_endpoint(
            "Chatbot Query", "POST", "/chatbot/chat",
            data={"batch_id": bid, "message": "What is the overall score?"},
            check_fields=["response"]
        )
        if chat_resp:
            response = chat_resp.get("response", "")
            log_info(f"  Response: {response[:100]}...")
    else:
        log_warning("No batches available to test chatbot")
        results["warnings"] += 1
    print()
    
    # 8. Reports API
    print("📋 8. REPORTS API")
    print("-"*40)
    
    if batch_ids:
        bid = batch_ids[0]
        report = test_endpoint(
            "Generate Report", "POST", "/reports/generate",
            data={"batch_id": bid, "include_evidence": True, "include_trends": True},
            check_fields=["batch_id", "download_url"]
        )
        if report:
            log_info(f"  Download URL: {report.get('download_url', 'N/A')[:50]}...")
    else:
        log_warning("No batches available to test reports")
        results["warnings"] += 1
    print()
    
    # 9. Processing API
    print("📋 9. PROCESSING API")
    print("-"*40)
    
    if batch_ids:
        bid = batch_ids[0]
        status = test_endpoint(
            f"Processing Status ({bid[:20]}...)", "GET", f"/processing/status/{bid}",
            check_fields=["batch_id", "status"]
        )
        if status:
            log_info(f"  Status: {status.get('status', 'N/A')}")
            log_info(f"  Progress: {status.get('progress', 0)}%")
    else:
        log_warning("No batches available to test processing status")
        results["warnings"] += 1
    print()
    
    # Summary
    print("="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    print(f"{Colors.GREEN}Passed: {results['passed']}{Colors.END}")
    print(f"{Colors.RED}Failed: {results['failed']}{Colors.END}")
    print(f"{Colors.YELLOW}Warnings: {results['warnings']}{Colors.END}")
    
    total = results['passed'] + results['failed']
    if total > 0:
        success_rate = (results['passed'] / total) * 100
        print(f"\nSuccess Rate: {success_rate:.1f}%")
        
        if results['failed'] == 0:
            print(f"\n{Colors.GREEN}🎉 ALL TESTS PASSED!{Colors.END}")
        elif results['failed'] <= 2:
            print(f"\n{Colors.YELLOW}⚠️ Some tests failed - review above{Colors.END}")
        else:
            print(f"\n{Colors.RED}❌ Multiple failures - needs attention{Colors.END}")
    
    print("\n")
    return results['failed']

if __name__ == "__main__":
    sys.exit(main())
