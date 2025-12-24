"""Quick test on completed batches with actual data."""
import requests

BASE = "http://localhost:8000/api"

# Get completed batches
r = requests.get(f"{BASE}/batches/list")
batches = r.json()
completed = [b for b in batches if b.get("status") == "completed" and b.get("processed_documents", 0) > 0]
print(f"Found {len(completed)} completed batches with documents")

if completed:
    bid = completed[0]["batch_id"]
    print(f"\n=== Testing with: {bid} ===\n")
    
    # Dashboard
    r = requests.get(f"{BASE}/dashboard/{bid}")
    if r.status_code == 200:
        d = r.json()
        kpis = list(d.get("kpis", {}).keys())
        print(f"Dashboard OK:")
        print(f"  KPIs: {kpis}")
        print(f"  Sufficiency: {d.get('sufficiency', {}).get('percentage', 0):.1f}%")
        print(f"  Blocks: {len(d.get('block_cards', []))}")
        print(f"  Compliance Flags: {len(d.get('compliance_flags', []))}")
        
        # Show KPI values
        for k, v in d.get("kpis", {}).items():
            print(f"    {k}: {v}")
    else:
        print(f"Dashboard FAILED: {r.status_code}")
    
    print()
    
    # Approval
    r = requests.get(f"{BASE}/approval/{bid}")
    if r.status_code == 200:
        a = r.json()
        print(f"Approval OK:")
        print(f"  Category: {a.get('classification', {}).get('category')}")
        print(f"  Subtype: {a.get('classification', {}).get('subtype')}")
        print(f"  Readiness: {a.get('readiness_score', 0):.1f}%")
        print(f"  Found: {len(a.get('documents_found', []))} docs")
        print(f"  Missing: {len(a.get('missing_documents', []))} docs")
        for doc in a.get("documents_found", [])[:5]:
            print(f"    ✓ {doc}")
        for doc in a.get("missing_documents", [])[:5]:
            print(f"    ✗ {doc}")
    else:
        print(f"Approval FAILED: {r.status_code}")
    
    print()
    
    # Reports
    r = requests.post(f"{BASE}/reports/generate", json={"batch_id": bid, "include_evidence": True})
    if r.status_code == 200:
        print(f"Report OK: Generated successfully")
    else:
        print(f"Report: {r.status_code}")

# Compare two completed batches
print("\n=== Comparison Test ===\n")
if len(completed) >= 2:
    ids = f"{completed[0]['batch_id']},{completed[1]['batch_id']}"
    r = requests.get(f"{BASE}/compare?batch_ids={ids}")
    if r.status_code == 200:
        c = r.json()
        print(f"Compare OK: {len(c.get('institutions', []))} institutions")
        for inst in c.get("institutions", []):
            print(f"  {inst.get('short_label')}: score={inst.get('overall_score', 0):.1f}, suff={inst.get('sufficiency_percent', 0):.1f}%, flags={inst.get('compliance_count', 0)}")
        print(f"  Winner: {c.get('winner_label', 'N/A')}")
        
        # Category winners
        print("\n  Category Leaders:")
        for cw in c.get("interpretation", {}).get("category_winners", [])[:5]:
            print(f"    {cw.get('kpi_name')}: {cw.get('winner_label')} ({cw.get('winner_value', 0):.1f})")
    else:
        print(f"Compare FAILED: {r.status_code}")
else:
    print("Need at least 2 completed batches for comparison")

print("\n=== Test Complete ===")
