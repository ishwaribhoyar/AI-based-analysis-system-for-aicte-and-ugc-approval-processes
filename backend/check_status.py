"""Quick check of batch statuses."""
import requests

r = requests.get('http://localhost:8000/api/batches/list')
batches = r.json()[:5]

print("Recent batches:")
for b in batches:
    print(f"  {b.get('batch_id')}: status={b.get('status')}, docs={b.get('total_documents')}")
    
    # Get processing status
    bid = b.get('batch_id')
    r2 = requests.get(f'http://localhost:8000/api/processing/status/{bid}')
    if r2.status_code == 200:
        s = r2.json()
        print(f"    -> processing_status={s.get('status')}, errors={s.get('errors', [])}")
