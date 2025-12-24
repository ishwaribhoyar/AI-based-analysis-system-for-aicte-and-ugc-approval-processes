"""Test KPI details endpoint."""
import requests

BASE = "http://localhost:8000/api"

# Get completed batches
r = requests.get(f"{BASE}/batches/list")
batches = [b for b in r.json() if b.get("status") == "completed"][:1]

if not batches:
    print("No completed batches found")
else:
    bid = batches[0]["batch_id"]
    print(f"Testing batch: {bid}")
    
    r = requests.get(f"{BASE}/dashboard/kpi-details/{bid}")
    print(f"Status: {r.status_code}")
    
    if r.status_code == 200:
        d = r.json()
        print(f"Institution: {d.get('institution_name')}")
        print(f"Mode: {d.get('mode')}")
        
        fsr = d.get("fsr", {})
        print(f"\nFSR Score: {fsr.get('final_score')}")
        print(f"  Parameters: {len(fsr.get('parameters', []))}")
        print(f"  Formula steps: {len(fsr.get('formula_steps', []))}")
        print(f"  Missing: {fsr.get('missing_parameters', [])}")
        
        infra = d.get("infrastructure", {})
        print(f"\nInfrastructure Score: {infra.get('final_score')}")
        print(f"  Parameters: {len(infra.get('parameters', []))}")
        
        placement = d.get("placement", {})
        print(f"\nPlacement Score: {placement.get('final_score')}")
        
        overall = d.get("overall", {})
        print(f"\nOverall Score: {overall.get('final_score')}")
    else:
        print(f"Error: {r.text[:200]}")
