"""
Test CSV/Excel Block Mapping.
Verifies that CSV/Excel files produce real AICTE/UGC blocks.
"""

import os
import sys
import tempfile
import pandas as pd
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.csv_block_mapper import map_file, map_csv_file, map_excel_file


def test_faculty_csv_mapping():
    """Test mapping CSV with faculty data."""
    # Create test CSV
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("faculty_count,phd_count,assistant_professor,associate_professor\n")
        f.write("45,12,20,13\n")
        csv_path = f.name
    
    try:
        blocks = map_csv_file(csv_path, mode="aicte")
        
        assert len(blocks) > 0, "Should produce at least one block"
        block = blocks[0]
        
        assert block["block_type"] == "faculty_information", f"Expected faculty_information, got {block['block_type']}"
        assert "data" in block, "Block should have data"
        assert block["confidence"] >= 0.85, f"Confidence should be >= 0.85, got {block['confidence']}"
        
        data = block["data"]
        assert "faculty_count" in data or "faculty_count_num" in data, "Should have faculty_count"
        
        print(f"✅ Faculty CSV mapping test passed: {block['block_type']} (confidence: {block['confidence']:.2f})")
        return True
    finally:
        os.unlink(csv_path)


def test_student_enrollment_csv_mapping():
    """Test mapping CSV with student enrollment data."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("total_students,male_students,female_students,intake\n")
        f.write("1200,650,550,1200\n")
        csv_path = f.name
    
    try:
        blocks = map_csv_file(csv_path, mode="aicte")
        
        assert len(blocks) > 0, "Should produce at least one block"
        block = blocks[0]
        
        assert block["block_type"] == "student_enrollment_information", f"Expected student_enrollment_information, got {block['block_type']}"
        
        data = block["data"]
        assert "total_students" in data or "total_students_num" in data, "Should have total_students"
        
        print(f"✅ Student enrollment CSV mapping test passed: {block['block_type']} (confidence: {block['confidence']:.2f})")
        return True
    finally:
        os.unlink(csv_path)


def test_infrastructure_excel_mapping():
    """Test mapping Excel with infrastructure data."""
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
        excel_path = f.name
    
    try:
        # Create Excel file with infrastructure data
        df = pd.DataFrame({
            "built_up_area": [15000],
            "classrooms": [42],
            "library_area": [800],
            "lab_area": [1200],
            "hostel_capacity": [500]
        })
        df.to_excel(excel_path, index=False)
        
        blocks = map_excel_file(excel_path, mode="aicte")
        
        assert len(blocks) > 0, "Should produce at least one block"
        block = blocks[0]
        
        assert block["block_type"] == "infrastructure_information", f"Expected infrastructure_information, got {block['block_type']}"
        
        data = block["data"]
        assert "built_up_area" in data or "built_up_area_num" in data, "Should have built_up_area"
        assert "classrooms" in data or "classrooms_num" in data, "Should have classrooms"
        
        print(f"✅ Infrastructure Excel mapping test passed: {block['block_type']} (confidence: {block['confidence']:.2f})")
        return True
    finally:
        if os.path.exists(excel_path):
            os.unlink(excel_path)


def test_placement_csv_mapping():
    """Test mapping CSV with placement data."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("students_placed,students_eligible,avg_salary,highest_salary\n")
        f.write("850,1000,8.5,15.2\n")
        csv_path = f.name
    
    try:
        blocks = map_csv_file(csv_path, mode="aicte")
        
        assert len(blocks) > 0, "Should produce at least one block"
        block = blocks[0]
        
        assert block["block_type"] == "placement_information", f"Expected placement_information, got {block['block_type']}"
        
        data = block["data"]
        assert "students_placed" in data or "students_placed_num" in data, "Should have students_placed"
        assert "placement_rate" in data or "placement_rate_num" in data, "Should calculate placement_rate"
        
        print(f"✅ Placement CSV mapping test passed: {block['block_type']} (confidence: {block['confidence']:.2f})")
        return True
    finally:
        os.unlink(csv_path)


def test_mixed_data_excel():
    """Test Excel with multiple sheets mapping to different blocks."""
    excel_path = None
    try:
        # Create Excel with multiple sheets
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
            excel_path = f.name
        
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            # Faculty sheet
            pd.DataFrame({
                "faculty_count": [45],
                "phd_count": [12]
            }).to_excel(writer, sheet_name="Faculty", index=False)
            
            # Infrastructure sheet
            pd.DataFrame({
                "built_up_area": [15000],
                "classrooms": [42]
            }).to_excel(writer, sheet_name="Infrastructure", index=False)
        
        # Now map it
        blocks = map_excel_file(excel_path, mode="aicte")
        
        assert len(blocks) >= 2, f"Should produce at least 2 blocks, got {len(blocks)}"
        
        block_types = [b["block_type"] for b in blocks]
        assert "faculty_information" in block_types, "Should have faculty_information block"
        assert "infrastructure_information" in block_types, "Should have infrastructure_information block"
        
        print(f"✅ Mixed Excel mapping test passed: {len(blocks)} blocks created")
        return True
    finally:
        if excel_path and os.path.exists(excel_path):
            try:
                import time
                import gc
                gc.collect()  # Force garbage collection to release file handles
                time.sleep(0.2)  # Give system time to release the file
                os.unlink(excel_path)
            except (PermissionError, OSError):
                # File still locked, skip cleanup (Windows issue)
                # This is acceptable - the test passed, cleanup is just a nicety
                pass


def run_all_tests():
    """Run all CSV/Excel mapping tests."""
    print("=" * 60)
    print("TESTING CSV/EXCEL BLOCK MAPPING")
    print("=" * 60)
    
    tests = [
        test_faculty_csv_mapping,
        test_student_enrollment_csv_mapping,
        test_infrastructure_excel_mapping,
        test_placement_csv_mapping,
        test_mixed_data_excel,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ {test.__name__} failed: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

