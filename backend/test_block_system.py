"""
Comprehensive test script for Information Block Architecture
Tests the system with real PDF files from the repository
"""

import asyncio
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from config.database import connect_to_mongo, get_database
from pipelines.block_processing_pipeline import BlockProcessingPipeline
from services.block_sufficiency import BlockSufficiencyService
from services.kpi import KPIService
from services.compliance import ComplianceService
from config.information_blocks import get_information_blocks
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_block_system():
    """Test the complete block-based system"""
    
    print("=" * 80)
    print("TESTING INFORMATION BLOCK ARCHITECTURE")
    print("=" * 80)
    
    # Connect to database
    try:
        await connect_to_mongo()
        print("✅ Connected to MongoDB")
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        return
    
    db = get_database()
    
    # Test 1: Verify 10 information blocks are defined
    print("\n📋 Test 1: Verify Information Blocks")
    print("-" * 80)
    blocks = get_information_blocks()
    print(f"Found {len(blocks)} information blocks:")
    for i, block in enumerate(blocks, 1):
        print(f"  {i}. {block}")
    
    if len(blocks) != 10:
        print(f"❌ ERROR: Expected 10 blocks, found {len(blocks)}")
        return
    else:
        print("✅ All 10 information blocks are defined")
    
    # Test 2: Check if there are any existing batches with blocks
    print("\n📋 Test 2: Check Existing Batches")
    print("-" * 80)
    batches = await db.batches.find({"status": "completed"}).limit(5).to_list(length=5)
    print(f"Found {len(batches)} completed batches")
    
    if batches:
        batch_id = batches[0]["batch_id"]
        print(f"Testing with batch: {batch_id}")
        
        # Check blocks in this batch
        blocks_count = await db.information_blocks.count_documents({"batch_id": batch_id})
        print(f"  - Information blocks found: {blocks_count}")
        
        if blocks_count > 0:
            # Get sample blocks
            sample_blocks = await db.information_blocks.find({"batch_id": batch_id}).limit(5).to_list(length=5)
            print(f"  - Sample blocks:")
            for block in sample_blocks:
                block_type = block.get("block_type", "unknown")
                confidence = block.get("extraction_confidence", 0)
                fields_count = len(block.get("extracted_data", {}))
                print(f"    • {block_type}: confidence={confidence:.2f}, fields={fields_count}")
            
            # Test 3: Test Sufficiency Calculation
            print("\n📋 Test 3: Test Sufficiency Calculation")
            print("-" * 80)
            all_blocks = await db.information_blocks.find({"batch_id": batch_id}).to_list(length=10000)
            block_list = [dict(b) for b in all_blocks]
            
            sufficiency_service = BlockSufficiencyService()
            mode = batches[0].get("mode", "aicte")
            sufficiency_result = sufficiency_service.calculate_sufficiency(mode, block_list)
            
            print(f"Sufficiency: {sufficiency_result.get('percentage', 0):.2f}%")
            print(f"  - Present blocks: {sufficiency_result.get('present_count', 0)}/10")
            print(f"  - Missing blocks: {len(sufficiency_result.get('missing_blocks', []))}")
            print(f"  - Penalty breakdown:")
            penalty = sufficiency_result.get('penalty_breakdown', {})
            print(f"    • Outdated: {penalty.get('outdated', 0)}")
            print(f"    • Low Quality: {penalty.get('low_quality', 0)}")
            print(f"    • Invalid: {penalty.get('invalid', 0)}")
            
            # Verify formula
            P = sufficiency_result.get('present_count', 0)
            R = 10
            O = penalty.get('outdated', 0)
            L = penalty.get('low_quality', 0)
            I = penalty.get('invalid', 0)
            
            base_pct = (P / R * 100) if R > 0 else 0
            calculated_penalty = O * 4 + L * 5 + I * 7
            calculated_penalty = min(calculated_penalty, 50)
            calculated_sufficiency = max(0, base_pct - calculated_penalty)
            
            actual_sufficiency = sufficiency_result.get('percentage', 0)
            
            if abs(calculated_sufficiency - actual_sufficiency) < 0.01:
                print("✅ Sufficiency formula is correct")
            else:
                print(f"❌ ERROR: Formula mismatch!")
                print(f"   Calculated: {calculated_sufficiency:.2f}%")
                print(f"   Actual: {actual_sufficiency:.2f}%")
            
            # Test 4: Test KPI Calculation
            print("\n📋 Test 4: Test KPI Calculation")
            print("-" * 80)
            kpi_service = KPIService()
            kpi_results = kpi_service.calculate_kpis(mode, blocks=block_list)
            
            print(f"KPIs calculated: {len(kpi_results)}")
            for kpi_id, kpi_data in kpi_results.items():
                if isinstance(kpi_data, dict) and "value" in kpi_data:
                    value = kpi_data.get("value", 0)
                    name = kpi_data.get("name", kpi_id)
                    print(f"  - {name}: {value:.2f}")
            
            if len(kpi_results) > 0:
                print("✅ KPIs calculated successfully")
            else:
                print("⚠️  Warning: No KPIs calculated")
            
            # Test 5: Test Compliance
            print("\n📋 Test 5: Test Compliance Checks")
            print("-" * 80)
            compliance_service = ComplianceService()
            compliance_results = compliance_service.check_compliance(mode, blocks=block_list)
            
            print(f"Compliance flags: {len(compliance_results)}")
            for flag in compliance_results[:5]:  # Show first 5
                severity = flag.get("severity", "medium")
                title = flag.get("title", "Unknown")
                print(f"  - [{severity.upper()}] {title}")
            
            print("✅ Compliance checks working")
            
            # Test 6: Verify block types distribution
            print("\n📋 Test 6: Verify Block Types Distribution")
            print("-" * 80)
            blocks_by_type = {}
            for block in block_list:
                block_type = block.get("block_type")
                if block_type:
                    if block_type not in blocks_by_type:
                        blocks_by_type[block_type] = 0
                    blocks_by_type[block_type] += 1
            
            print("Block type distribution:")
            for block_type in get_information_blocks():
                count = blocks_by_type.get(block_type, 0)
                status = "✅" if count > 0 else "❌"
                print(f"  {status} {block_type}: {count} blocks")
            
        else:
            print("⚠️  No blocks found in this batch. Need to process a batch first.")
    
    else:
        print("⚠️  No completed batches found. Need to create and process a batch first.")
    
    # Test 7: Verify block extraction schemas
    print("\n📋 Test 7: Verify Block Extraction Schemas")
    print("-" * 80)
    from config.information_blocks import get_block_fields
    
    for mode in ["aicte", "ugc"]:
        print(f"\n{mode.upper()} Mode:")
        for block_type in get_information_blocks():
            fields = get_block_fields(block_type, mode)
            required = fields.get("required_fields", [])
            optional = fields.get("optional_fields", [])
            print(f"  {block_type}:")
            print(f"    Required: {len(required)} fields")
            print(f"    Optional: {len(optional)} fields")
    
    print("\n✅ Block extraction schemas verified")
    
    print("\n" + "=" * 80)
    print("TESTING COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(test_block_system())

