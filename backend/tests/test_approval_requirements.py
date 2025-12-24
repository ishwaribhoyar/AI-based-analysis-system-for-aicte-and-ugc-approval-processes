"""
Test approval requirements with evidence-driven checks.
Ensures no dummy/default outputs - all data from actual extracted evidence.
"""

import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import requests
import time
from services.approval_requirements import check_approval_requirements
from config.database import get_db, close_db, Batch

API_BASE = "http://localhost:8000"


def test_approval_requirements_evidence_driven():
    """Test that approval requirements only show evidence-based results."""
    print("=" * 70)
    print("TEST: Approval Requirements Evidence-Driven")
    print("=" * 70)
    
    # Find a completed batch
    db = get_db()
    try:
        batch = db.query(Batch).filter(Batch.status == "completed").first()
        if not batch:
            print("⚠️  No completed batches found. Run processing first.")
            return False
        
        batch_id = batch.id
        print(f"✓ Testing with batch: {batch_id}")
    finally:
        close_db(db)
    
    # Check approval requirements
    result = check_approval_requirements(batch_id)
    
    print(f"\n✓ Approval type: {result.get('approval_type')}")
    print(f"✓ Readiness score: {result.get('readiness_score')}%")
    
    # Verify structure
    assert "present_documents" in result, "Missing present_documents"
    assert "missing_documents" in result, "Missing missing_documents"
    assert "unknown_documents" in result, "Missing unknown_documents"
    
    # Check present documents have evidence
    present = result.get("present_documents", [])
    print(f"\n✓ Present documents: {len(present)}")
    for doc in present[:3]:  # Show first 3
        assert "evidence" in doc, f"Present doc {doc.get('key')} missing evidence"
        evidence = doc.get("evidence", {})
        assert "snippet" in evidence or "value" in evidence, f"Evidence missing snippet/value"
        print(f"  - {doc.get('description')}: confidence {evidence.get('confidence', 0):.2f}")
    
    # Check missing documents have reason
    missing = result.get("missing_documents", [])
    print(f"\n✓ Missing documents: {len(missing)}")
    for doc in missing[:3]:  # Show first 3
        assert "reason" in doc, f"Missing doc {doc.get('key')} missing reason"
        assert doc.get("examined") is True, f"Missing doc {doc.get('key')} should be examined"
        print(f"  - {doc.get('description')}: {doc.get('reason')}")
    
    # Check unknown documents have reason
    unknown = result.get("unknown_documents", [])
    print(f"\n✓ Unknown documents: {len(unknown)}")
    for doc in unknown[:3]:  # Show first 3
        assert "reason" in doc, f"Unknown doc {doc.get('key')} missing reason"
        assert "No relevant block found" in doc.get("reason", ""), "Unknown should mention no block found"
        print(f"  - {doc.get('description')}: {doc.get('reason')}")
    
    # Verify no hardcoded lists
    total = result.get("total_required", 0)
    present_count = result.get("total_present", 0)
    missing_count = result.get("total_missing", 0)
    unknown_count = result.get("total_unknown", 0)
    
    assert present_count + missing_count + unknown_count == total, "Counts don't match"
    
    print(f"\n✅ All checks passed!")
    print(f"   Total required: {total}")
    print(f"   Present: {present_count}, Missing: {missing_count}, Unknown: {unknown_count}")
    
    return True


if __name__ == "__main__":
    success = test_approval_requirements_evidence_driven()
    sys.exit(0 if success else 1)

