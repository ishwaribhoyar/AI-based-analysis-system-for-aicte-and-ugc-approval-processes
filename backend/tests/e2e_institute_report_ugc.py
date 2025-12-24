"""
E2E test for INSTITUTE INFORMATION CONSOLIDATED REPORT.pdf in UGC mode.
Creates a batch, uploads the PDF, runs processing, then prints dashboard
summary and report URL.
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
    print("E2E TEST – INSTITUTE INFORMATION CONSOLIDATED REPORT.pdf (UGC MODE)")
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

    # Create batch (UGC)
    try:
        r = requests.post(
            f"{API_BASE}/api/batches/create",
            json={"mode": "ugc"},
            timeout=10,
        )
        r.raise_for_status()
        data = r.json()
        batch_id = data.get("batch_id") or data.get("id")
        print(f"Created UGC batch: {batch_id}")
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

    print("\n=== DASHBOARD SUMMARY (UGC) ===")
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

    # Generate report
    try:
        r = requests.post(
            f"{API_BASE}/api/reports/generate",
            json={"batch_id": batch_id},
            timeout=60,
        )
        r.raise_for_status()
        rep = r.json()
        print("\nReport generated:")
        print(f"  report_path: {rep.get('report_path')}")
        print(f"  download_url: {rep.get('download_url')}")
    except Exception as e:
        print(f"Failed to generate report: {e}")
        return 1

    print("\nYou can open the report at:")
    print(f"  {API_BASE}{rep.get('download_url')}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())


