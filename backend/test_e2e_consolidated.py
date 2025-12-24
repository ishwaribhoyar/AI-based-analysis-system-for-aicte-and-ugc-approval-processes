"""
E2E Test with INSTITUTE INFORMATION CONSOLIDATED REPORT.pdf
"""
import requests
import time
import json

BASE_URL = 'http://localhost:8000/api'

def run_test():
    # Step 1: Create a new batch
    print('='*60)
    print('Step 1: Creating new AICTE batch...')
    batch_response = requests.post(f'{BASE_URL}/batches/', json={
        'mode': 'aicte',
        'name': 'E2E Test - Consolidated Report'
    })
    batch_data = batch_response.json()
    batch_id = batch_data.get('batch_id') or batch_data.get('id')
    print(f'Batch ID: {batch_id}')
    print(f'Full response: {json.dumps(batch_data, indent=2)}')

    # Step 2: Upload the PDF
    print('='*60)
    print('Step 2: Uploading PDF...')
    pdf_path = r'c:\Users\datta\OneDrive\Desktop\sih 2\INSTITUTE INFORMATION CONSOLIDATED REPORT.pdf'
    with open(pdf_path, 'rb') as f:
        files = {'file': ('INSTITUTE INFORMATION CONSOLIDATED REPORT.pdf', f, 'application/pdf')}
        data = {'batch_id': batch_id}
        upload_response = requests.post(f'{BASE_URL}/documents/upload', files=files, data=data)
    print(f'Upload status: {upload_response.status_code}')
    print(f'Upload response: {json.dumps(upload_response.json(), indent=2)}')

    # Step 3: Start processing
    print('='*60)
    print('Step 3: Starting processing...')
    process_response = requests.post(f'{BASE_URL}/processing/start', json={'batch_id': batch_id})
    print(f'Process status: {process_response.status_code}')
    print(f'Process response: {json.dumps(process_response.json(), indent=2)}')

    # Step 4: Wait for processing and poll status
    print('='*60)
    print('Step 4: Waiting for processing to complete...')
    max_wait = 180  # 3 minutes max
    waited = 0
    while waited < max_wait:
        status_response = requests.get(f'{BASE_URL}/processing/status/{batch_id}')
        status_data = status_response.json()
        status = status_data.get('status')
        stage = status_data.get('current_stage')
        progress = status_data.get('progress')
        print(f'[{waited}s] Status: {status} - {stage} ({progress}%)')
        if status in ['completed', 'failed']:
            break
        time.sleep(5)
        waited += 5
    
    print('='*60)
    print(f'Final processing status: {json.dumps(status_data, indent=2)}')

    # Step 5: Get batch results (KPIs)
    print('='*60)
    print('Step 5: Getting batch results and KPIs...')
    batch_details = requests.get(f'{BASE_URL}/batches/{batch_id}')
    print(f'Batch details status: {batch_details.status_code}')
    if batch_details.status_code == 200:
        details = batch_details.json()
        print(f'Batch details: {json.dumps(details, indent=2)}')
        # Print KPIs specifically
        if 'kpi_results' in details:
            print('\n*** KPI RESULTS ***')
            print(json.dumps(details['kpi_results'], indent=2))
    else:
        print(f'Error: {batch_details.text}')

    # Step 6: Check dashboard for KPI metrics
    print('='*60)
    print('Step 6: Getting dashboard data...')
    dashboard_response = requests.get(f'{BASE_URL}/dashboard/{batch_id}')
    print(f'Dashboard status: {dashboard_response.status_code}')
    if dashboard_response.status_code == 200:
        dashboard = dashboard_response.json()
        print('\n*** KPI CARDS ***')
        for kpi in dashboard.get('kpi_cards', []):
            print(f"  {kpi['name']}: {kpi['value']} ({kpi.get('label', '')})")
        print('\n*** SUFFICIENCY ***')
        suff = dashboard.get('sufficiency', {})
        print(f"  Percentage: {suff.get('percentage')}%")
        print(f"  Present: {suff.get('present_count')}/{suff.get('required_count')}")
        print(f"  Missing: {suff.get('missing_blocks', [])}")
        print('\n*** BLOCKS ***')
        for block in dashboard.get('block_cards', []):
            status = 'PRESENT' if block['is_present'] else 'MISSING'
            print(f"  {block['block_name']}: {status} (confidence: {block.get('confidence', 0):.2f})")
    else:
        print(f'Dashboard error: {dashboard_response.text}')
    
    return batch_id

if __name__ == '__main__':
    run_test()
