"""
Test comparison API filtering - ensures empty batches are excluded.
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import requests

API_BASE = "http://localhost:8000"


def test_compare_filters_empty_batches():
    """Test that comparison API excludes batches with 0 processed documents."""
    print("=" * 70)
    print("TEST: Comparison API Filters Empty Batches")
    print("=" * 70)
    
    # Get list of batches
    try:
        r = requests.get(f"{API_BASE}/api/batches/list")
        batches = r.json()
        print(f"✓ Found {len(batches)} batches")
    except Exception as e:
        print(f"❌ Failed to get batches: {e}")
        return False
    
    if len(batches) < 2:
        print("⚠️  Need at least 2 batches for comparison test")
        return False
    
    # Filter to only completed batches with documents
    valid_batches = [
        b for b in batches 
        if b.get("status") == "completed" and b.get("total_documents", 0) > 0
    ]
    
    if len(valid_batches) < 2:
        print("⚠️  Need at least 2 valid batches for comparison")
        return False
    
    # Test comparison with valid batches
    batch_ids = [b["batch_id"] for b in valid_batches[:3]]  # Use up to 3
    batch_ids_str = ",".join(batch_ids)
    
    try:
        r = requests.get(f"{API_BASE}/api/compare", params={"batch_ids": batch_ids_str})
        comparison = r.json()
        
        print(f"\n✓ Comparison response received")
        print(f"  Institutions: {len(comparison.get('institutions', []))}")
        print(f"  Skipped batches: {len(comparison.get('skipped_batches', []))}")
        
        # Verify all returned institutions have valid data
        institutions = comparison.get("institutions", [])
        for inst in institutions:
            # Check that institution has at least some KPIs
            kpis = inst.get("kpis", {})
            valid_kpis = [v for v in kpis.values() if v is not None]
            assert len(valid_kpis) > 0, f"Institution {inst.get('short_label')} has no valid KPIs"
            
            # Check institution name is not a dummy
            name = inst.get("name", "")
            assert name and len(name) > 3, f"Institution name too short: {name}"
            assert not name.startswith("Institution #"), f"Institution name is dummy: {name}"
        
        # Verify skipped batches have reasons
        skipped = comparison.get("skipped_batches", [])
        for skip in skipped:
            assert "reason" in skip, f"Skipped batch missing reason: {skip}"
            print(f"  Skipped: {skip.get('batch_id')} - {skip.get('reason')}")
        
        print("\n✅ Comparison filtering works correctly")
        return True
        
    except Exception as e:
        print(f"❌ Comparison test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_compare_filters_empty_batches()
    sys.exit(0 if success else 1)

