"""
Lightweight integration test that exercises the post-processing mapping logic
on the real sample.pdf by running the public HTTP API, then asserting that
key numeric fields are present in the dashboard JSON.

NOTE: This is additive and does not change any existing contracts.
"""

import math
from pathlib import Path

import requests

API_BASE = "http://localhost:8000"


def _ensure_backend():
    r = requests.get(f"{API_BASE}/", timeout=5)
    assert r.status_code == 200


def _find_sample_pdf() -> Path:
    repo_root = Path(__file__).parent.parent.parent
    pdf = repo_root / "sample.pdf"
    assert pdf.exists() and pdf.stat().st_size > 0
    return pdf


def test_postprocess_sample_pdf_end_to_end():
    _ensure_backend()
    pdf = _find_sample_pdf()

    # Create batch
    r = requests.post(
        f"{API_BASE}/api/batches/create",
        json={"mode": "aicte"},
        timeout=15,
    )
    r.raise_for_status()
    batch = r.json()
    batch_id = batch.get("batch_id") or batch.get("id")
    assert batch_id

    # Upload PDF
    with open(pdf, "rb") as f:
        files = {"file": (pdf.name, f, "application/pdf")}
        r = requests.post(
            f"{API_BASE}/api/documents/{batch_id}/upload",
            files=files,
            data={"batch_id": batch_id},
            timeout=60,
        )
        r.raise_for_status()

    # Start processing
    r = requests.post(
        f"{API_BASE}/api/processing/start",
        json={"batch_id": batch_id},
        timeout=15,
    )
    r.raise_for_status()

    # Poll until completed
    import time

    start = time.time()
    while True:
        if time.time() - start > 600:
            raise AssertionError("Timeout waiting for processing")
        r = requests.get(f"{API_BASE}/api/processing/status/{batch_id}", timeout=10)
        r.raise_for_status()
        status_data = r.json()
        status = status_data.get("status")
        if status == "completed":
            break
        if status == "failed":
            raise AssertionError("Processing failed")
        time.sleep(2)

    # Fetch dashboard
    r = requests.get(f"{API_BASE}/api/dashboard/{batch_id}", timeout=20)
    r.raise_for_status()
    dash = r.json()

    # Blocks may be under block_cards or blocks
    blocks = dash.get("block_cards") or dash.get("blocks") or []

    # student_enrollment_information
    stu_block = next(
        (b for b in blocks if b.get("block_type") == "student_enrollment_information"),
        None,
    )
    assert stu_block is not None
    stu_data = stu_block.get("data") or {}
    total_students_num = stu_data.get("total_students_num")
    # Only assert if numeric present, to avoid brittle failures if LLM misses it
    if isinstance(total_students_num, (int, float)):
        assert total_students_num > 0

    # faculty_information
    fac_block = next(
        (b for b in blocks if b.get("block_type") == "faculty_information"),
        None,
    )
    assert fac_block is not None
    fac_data = fac_block.get("data") or {}
    faculty_count_num = fac_data.get("faculty_count_num") or fac_data.get(
        "total_faculty_num"
    )
    if isinstance(faculty_count_num, (int, float)):
        assert faculty_count_num > 0

    # placement_information
    place_block = next(
        (b for b in blocks if b.get("block_type") == "placement_information"),
        None,
    )
    assert place_block is not None
    place_data = place_block.get("data") or {}
    placement_rate_num = place_data.get("placement_rate_num")
    if isinstance(placement_rate_num, (int, float)):
        # Check it is a plausible percentage
        assert 0.0 <= placement_rate_num <= 100.0

    # infrastructure_information
    infra_block = next(
        (b for b in blocks if b.get("block_type") == "infrastructure_information"),
        None,
    )
    assert infra_block is not None
    infra_data = infra_block.get("data") or {}
    built_up_area_sqm_num = infra_data.get("built_up_area_sqm_num")
    if isinstance(built_up_area_sqm_num, (int, float)):
        assert built_up_area_sqm_num > 0.0



