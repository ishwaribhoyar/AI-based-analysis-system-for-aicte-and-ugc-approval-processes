"""Test analytics endpoints."""
import requests

BASE = "http://localhost:8000/api"

# Get completed batches
r = requests.get(f"{BASE}/batches/list")
batches = r.json()
completed = [b["batch_id"] for b in batches if b.get("status") == "completed"][:3]
print(f"Found {len(completed)} completed batches")

if len(completed) >= 1:
    ids = ",".join(completed)
    
    # Test multi-year
    print("\n=== Multi-Year Analytics ===")
    r = requests.get(f"{BASE}/analytics/multi_year", params={"batch_ids": ids, "years": 5})
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"Institution: {data.get('institution_name')}")
        print(f"Years: {data.get('available_years')}")
        print(f"Best year: {data.get('best_year')}")
        print(f"Insights: {data.get('insights', [])[:2]}")
    else:
        print(f"Error: {r.text[:200]}")
    
    # Test prediction
    print("\n=== Prediction Engine ===")
    r = requests.post(f"{BASE}/analytics/predict", json={
        "batch_ids": completed,
        "years_to_predict": 5,
        "metrics": ["fsr_score", "overall_score"]
    })
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"Has enough data: {data.get('has_enough_data')}")
        if data.get('has_enough_data'):
            print(f"Historical years: {data.get('historical_years')}")
            print(f"Prediction years: {data.get('prediction_years')}")
            for metric, forecast in data.get('forecasts', {}).items():
                print(f"  {metric}: trend={forecast.get('trend_direction')}, confidence={forecast.get('confidence'):.2f}")
        else:
            print(f"Error: {data.get('error_message')}")
    else:
        print(f"Error: {r.text[:200]}")
else:
    print("No completed batches found")
