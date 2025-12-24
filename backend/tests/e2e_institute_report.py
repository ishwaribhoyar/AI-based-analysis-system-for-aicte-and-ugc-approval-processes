"""
E2E test for INSTITUTE INFORMATION CONSOLIDATED REPORT.pdf
Creates a batch, uploads the PDF, runs processing, then prints dashboard JSON.
"""

import sys
import time
from pathlib import Path

import requests

API_BASE = "http://localhost:8000"


def find_pdf() -> Path | None:
    repo_root = Path(__file__).parent.parent.parent
    candidate = repo_root / "INSTITUTE INFORMATION CONSOLIDATED REPORT.pdf"
    if candidate.exists() and candidate.stat().st_size > 0:
        return candidate
    return None


def main() -> int:
    print("=" * 70)
    print("E2E TEST – INSTITUTE INFORMATION CONSOLIDATED REPORT.pdf")
    print("=" * 70)

    # Backend check
    try:
        r = requests.get(f"{API_BASE}/", timeout=5)
        print(f"Backend reachable (status {r.status_code})")
    except Exception as e:
        print(f"Backend NOT reachable: {e}")
        return 1

    pdf_path = find_pdf()
    if not pdf_path:
        print("❌ PDF not found in repo root.")
        return 1
    print(f"Using PDF: {pdf_path} ({pdf_path.stat().st_size/1024:.1f} KB)")

    # Create batch
    try:
        r = requests.post(
            f"{API_BASE}/api/batches/create",
            json={"mode": "aicte"},
            timeout=10,
        )
        r.raise_for_status()
        data = r.json()
        batch_id = data.get("batch_id") or data.get("id")
        print(f"Created batch: {batch_id}")
    except Exception as e:
        print(f"Failed to create batch: {e}")
        return 1

    # Upload PDF
    try:
        with open(pdf_path, "rb") as f:
            files = {"file": (pdf_path.name, f, "application/pdf")}
            r = requests.post(
                f"{API_BASE}/api/documents/{batch_id}/upload",
                files=files,
                data={"batch_id": batch_id},
                timeout=60,
            )
            r.raise_for_status()
        print("Upload: OK")
    except Exception as e:
        print(f"Upload failed: {e}")
        return 1

    # Start processing
    try:
        r = requests.post(
            f"{API_BASE}/api/processing/start",
            json={"batch_id": batch_id},
            timeout=10,
        )
        r.raise_for_status()
        print("Processing started.")
    except Exception as e:
        print(f"Failed to start processing: {e}")
        return 1

    # Poll status
    start = time.time()
    while True:
        if time.time() - start > 600:
            print("❌ Timeout waiting for processing.")
            return 1
        try:
            r = requests.get(f"{API_BASE}/api/processing/status/{batch_id}", timeout=10)
            r.raise_for_status()
            s = r.json()
            status = s.get("status")
            processed = s.get("processed_documents", 0)
            total = s.get("total_documents", 0)
            print(f"Status: {status} ({processed}/{total})", end="\r")
            if status == "completed":
                print("\nProcessing completed.")
                break
            if status == "failed":
                print("\nProcessing FAILED.")
                return 1
            time.sleep(2)
        except Exception as e:
            print(f"\nError polling status: {e}")
            time.sleep(2)

    # Dashboard
    try:
        r = requests.get(f"{API_BASE}/api/dashboard/{batch_id}", timeout=20)
        r.raise_for_status()
        dash = r.json()
    except Exception as e:
        print(f"Failed to fetch dashboard: {e}")
        return 1

    print("\n=== DASHBOARD SUMMARY ===")
    print(f"Batch: {dash.get('batch_id')}")
    print(f"Mode:  {dash.get('mode')}")

    suff = dash.get("sufficiency")
    if isinstance(suff, dict):
        pct = suff.get("percentage", 0)
        present = suff.get("present_count", 0)
        required = suff.get("required_count", 0)
        print(f"Sufficiency: {pct:.2f}% ({present}/{required})")
    else:
        print(f"Sufficiency: {suff}")

    # Blocks / KPIs
    block_cards = dash.get("block_cards") or dash.get("blocks") or []
    kpi_cards = dash.get("kpi_cards") or []
    print(f"Blocks: {len(block_cards)}")
    print(f"KPIs:   {len(kpi_cards)}")

    if kpi_cards:
        print("KPIs:")
        for k in kpi_cards:
            name = k.get("name", "KPI")
            val = k.get("value")
            print(f"  - {name}: {val}")

    # Print faculty + placement numeric highlights if present
    fac_block = next(
        (b for b in block_cards if b.get("block_type") == "faculty_information"),
        None,
    )
    place_block = next(
        (b for b in block_cards if b.get("block_type") == "placement_information"),
        None,
    )
    if fac_block:
        data = fac_block.get("data") or {}
        print("\nFaculty block snapshot:")
        print(f"  total_faculty: {data.get('total_faculty')}")
        print(f"  total_faculty_num: {data.get('total_faculty_num')}")
        print(f"  department_wise_faculty: {data.get('department_wise_faculty')}")
    if place_block:
        data = place_block.get("data") or {}
        print("\nPlacement block snapshot:")
        print(f"  eligible_students: {data.get('eligible_students')}")
        print(f"  eligible_students_num: {data.get('eligible_students_num')}")
        print(f"  students_placed: {data.get('students_placed')}")
        print(f"  students_placed_num: {data.get('students_placed_num')}")
        print(f"  placement_rate: {data.get('placement_rate')}")
        print(f"  placement_rate_num: {data.get('placement_rate_num')}")
        print(f"  top_recruiters: {data.get('top_recruiters')}")

    # Dump raw JSON path for the user to inspect via API
    print("\nYou can inspect full dashboard JSON at:")
    print(f"  GET {API_BASE}/api/dashboard/{batch_id}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())


