"""Quick test script for new features."""
import requests

BASE = "http://localhost:8000"

print("=" * 50)
print("1. Testing batches/list with filter=valid")
r = requests.get(f"{BASE}/api/batches/list", params={"filter": "valid"})
batches = r.json()
print(f"   Valid batches: {len(batches)}")

if batches:
    bid = batches[0]["batch_id"]
    print(f"   Using batch: {bid}")
    
    print()
    print("2. Testing KPI drilldown endpoint")
    r2 = requests.get(f"{BASE}/api/dashboard/{bid}/kpi-details/fsr")
    print(f"   Status: {r2.status_code}")
    if r2.status_code == 200:
        d = r2.json()
        print(f"   KPI: {d.get('kpi_name')}")
        print(f"   Score: {d.get('final_score')}")
        print(f"   Parameters: {len(d.get('parameters', []))}")
        print(f"   Insights: {d.get('insights', [])[:2]}")
    
    print()
    print("3. Testing trends endpoint")
    r3 = requests.get(f"{BASE}/api/dashboard/trends/{bid}")
    print(f"   Status: {r3.status_code}")
    if r3.status_code == 200:
        t = r3.json()
        print(f"   Has historical data: {t.get('has_historical_data')}")
        print(f"   Years: {t.get('years_available')}")

print()
print("4. Testing parse_numeric_with_metadata")
from utils.parse_numeric import parse_numeric_with_metadata
tests = ["85.5%", "4.2 LPA", "18500 sq.ft", "1,290"]
for t in tests:
    r = parse_numeric_with_metadata(t)
    print(f"   {t} -> value={r['value']}, unit={r['unit']}")

print()
print("5. Testing forgery detection")
from services.forgery_detection import run_forgery_checks
result = run_forgery_checks(
    metadata={"creator": "Adobe"},
    extracted_data={"placement_rate_num": 85, "total_students_num": 1000}
)
print(f"   Status: {result['authenticity_status']}")
print(f"   Passed: {result['passed_checks']}")

print()
print("=" * 50)
print("ALL TESTS COMPLETED!")
