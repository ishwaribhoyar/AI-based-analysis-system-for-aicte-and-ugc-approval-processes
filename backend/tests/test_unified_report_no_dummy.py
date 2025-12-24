"""
Test unified report - ensures no hardcoded dummy missing-docs lists.
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import requests

API_BASE = "http://localhost:8000"


def test_unified_report_no_dummy():
    """Test that unified report uses only evidence-driven document lists."""
    print("=" * 70)
    print("TEST: Unified Report No Dummy Data")
    print("=" * 70)
    
    # Find a completed batch
    try:
        r = requests.get(f"{API_BASE}/api/batches/list?filter=valid")
        batches = r.json()
        
        if not batches:
            print("⚠️  No valid batches found")
            return False
        
        batch_id = batches[0]["batch_id"]
        print(f"✓ Testing with batch: {batch_id}")
    except Exception as e:
        print(f"❌ Failed to get batches: {e}")
        return False
    
    # Get unified report
    try:
        r = requests.get(f"{API_BASE}/api/unified-report/{batch_id}")
        report = r.json()
        
        print(f"\n✓ Unified report retrieved")
        
        # Check document sections
        present_docs = report.get("present_documents", [])
        missing_docs = report.get("missing_documents", [])
        unknown_docs = report.get("unknown_documents", [])
        
        print(f"  Present: {len(present_docs)}")
        print(f"  Missing: {len(missing_docs)}")
        print(f"  Unknown: {len(unknown_docs)}")
        
        # Verify present documents have evidence
        for doc in present_docs:
            assert "evidence" in doc, f"Present doc missing evidence: {doc.get('key')}"
            evidence = doc.get("evidence", {})
            # Should have snippet or value
            assert "snippet" in evidence or "value" in evidence, "Evidence missing snippet/value"
            assert "confidence" in evidence, "Evidence missing confidence"
        
        # Verify missing documents have reason and examined flag
        for doc in missing_docs:
            assert "reason" in doc, f"Missing doc missing reason: {doc.get('key')}"
            assert doc.get("examined") is True, f"Missing doc should be examined: {doc.get('key')}"
        
        # Verify unknown documents have reason
        for doc in unknown_docs:
            assert "reason" in doc, f"Unknown doc missing reason: {doc.get('key')}"
            reason = doc.get("reason", "")
            assert "No relevant block" in reason or "not examined" in reason.lower(), \
                f"Unknown doc reason should mention no block: {reason}"
        
        # Check that regulator summaries don't have hardcoded missing_documents
        aicte_summary = report.get("aicte_summary")
        if aicte_summary:
            aicte_missing = aicte_summary.get("missing_documents", [])
            # Should be a subset of the main missing_documents (evidence-based)
            assert len(aicte_missing) <= len(missing_docs), "AICTE missing docs should be subset"
        
        ugc_summary = report.get("ugc_summary")
        if ugc_summary:
            ugc_missing = ugc_summary.get("missing_documents", [])
            assert len(ugc_missing) <= len(missing_docs), "UGC missing docs should be subset"
        
        # Verify no hardcoded strings in missing documents
        # Common dummy strings to check for
        dummy_strings = [
            "Sample Document",
            "Example Certificate",
            "Placeholder",
            "Dummy",
            "Test Document"
        ]
        
        all_doc_text = " ".join([
            str(doc.get("description", "")) + " " + str(doc.get("reason", ""))
            for doc in missing_docs + unknown_docs
        ]).lower()
        
        for dummy in dummy_strings:
            assert dummy.lower() not in all_doc_text, f"Found dummy string: {dummy}"
        
        print("\n✅ Unified report is evidence-driven (no dummy data)")
        return True
        
    except Exception as e:
        print(f"❌ Unified report test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_unified_report_no_dummy()
    sys.exit(0 if success else 1)

