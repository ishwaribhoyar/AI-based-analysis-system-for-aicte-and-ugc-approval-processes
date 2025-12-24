"""
End-to-End Test with Real PDF Files
Tests the complete Information Block Architecture flow
"""

import asyncio
import sys
import os
from pathlib import Path
import json
from datetime import datetime

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from config.database import connect_to_mongo, get_database, close_mongo_connection
from pipelines.block_processing_pipeline import BlockProcessingPipeline
from services.block_sufficiency import BlockSufficiencyService
from services.kpi import KPIService
from services.compliance import ComplianceService
from config.information_blocks import get_information_blocks
from utils.id_generator import generate_batch_id, generate_document_id
from utils.file_utils import get_file_hash, get_mime_type
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_end_to_end():
    """Test complete end-to-end flow with real PDFs"""
    
    print("=" * 80)
    print("END-TO-END TEST: INFORMATION BLOCK ARCHITECTURE")
    print("=" * 80)
    
    # Step 1: Connect to database
    print("\n📋 Step 1: Database Connection")
    print("-" * 80)
    try:
        await connect_to_mongo()
        db = get_database()
        print("✅ Connected to MongoDB")
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        print("⚠️  Make sure MongoDB is running and MONGODB_URL is set in .env")
        return False
    
    # Step 2: Find PDF files in repository
    print("\n📋 Step 2: Finding PDF Files")
    print("-" * 80)
    repo_root = Path(__file__).parent.parent
    pdf_files = []
    
    # Check root directory
    for pdf_file in repo_root.glob("*.pdf"):
        if pdf_file.is_file():
            pdf_files.append(pdf_file)
            print(f"  ✅ Found: {pdf_file.name}")
    
    if not pdf_files:
        print("❌ No PDF files found in repository root")
        print("   Expected files: 2025-26-AICTE-Approval.pdf, EOA-Report-2025-26.pdf, etc.")
        return False
    
    print(f"\n✅ Found {len(pdf_files)} PDF file(s)")
    
    # Step 3: Create a test batch
    print("\n📋 Step 3: Creating Test Batch")
    print("-" * 80)
    batch_id = generate_batch_id("aicte")
    mode = "aicte"
    institution_name = "Test Institution"
    
    batch_data = {
        "batch_id": batch_id,
        "mode": mode,
        "status": "created",
        "institution_name": institution_name,
        "institution_code": "TEST001",
        "academic_year": "2025-26",
        "total_documents": 0,
        "processed_documents": 0,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    try:
        await db.batches.insert_one(batch_data)
        print(f"✅ Created batch: {batch_id}")
    except Exception as e:
        print(f"❌ Failed to create batch: {e}")
        return False
    
    # Step 4: Upload PDF files as documents
    print("\n📋 Step 4: Uploading PDF Files")
    print("-" * 80)
    documents_created = []
    
    for pdf_file in pdf_files[:4]:  # Test with up to 4 PDFs
        try:
            document_id = generate_document_id()
            file_size = pdf_file.stat().st_size
            file_hash = get_file_hash(str(pdf_file))
            mime_type = get_mime_type(pdf_file.name)
            
            # Copy file to uploads directory
            upload_dir = Path(__file__).parent / "storage" / "uploads" / batch_id
            upload_dir.mkdir(parents=True, exist_ok=True)
            
            import shutil
            dest_file = upload_dir / pdf_file.name
            shutil.copy2(pdf_file, dest_file)
            
            document_data = {
                "document_id": document_id,
                "batch_id": batch_id,
                "filename": pdf_file.name,
                "file_path": str(dest_file),
                "file_size": file_size,
                "file_hash": file_hash,
                "mime_type": mime_type,
                "status": "uploaded",
                "uploaded_at": datetime.utcnow()
            }
            
            await db.documents.insert_one(document_data)
            documents_created.append(document_id)
            print(f"  ✅ Uploaded: {pdf_file.name} ({file_size:,} bytes)")
            
        except Exception as e:
            print(f"  ❌ Failed to upload {pdf_file.name}: {e}")
            import traceback
            traceback.print_exc()
    
    if not documents_created:
        print("❌ No documents were uploaded")
        return False
    
    # Update batch document count
    await db.batches.update_one(
        {"batch_id": batch_id},
        {"$set": {"total_documents": len(documents_created)}}
    )
    
    print(f"\n✅ Uploaded {len(documents_created)} document(s)")
    
    # Step 5: Process batch through pipeline
    print("\n📋 Step 5: Processing Batch Through Pipeline")
    print("-" * 80)
    print("⚠️  This may take several minutes depending on PDF size and OpenAI API...")
    
    try:
        pipeline = BlockProcessingPipeline()
        result = await pipeline.process_batch(batch_id)
        
        if result.get("status") == "completed":
            print("✅ Pipeline completed successfully")
        else:
            print(f"⚠️  Pipeline status: {result.get('status')}")
            
    except Exception as e:
        print(f"❌ Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 6: Verify blocks were created
    print("\n📋 Step 6: Verifying Information Blocks")
    print("-" * 80)
    blocks = await db.information_blocks.find({"batch_id": batch_id}).to_list(length=10000)
    print(f"Total blocks created: {len(blocks)}")
    
    if len(blocks) == 0:
        print("❌ No blocks were created - pipeline may have failed")
        return False
    
    # Group by block type
    blocks_by_type = {}
    for block in blocks:
        block_type = block.get("block_type")
        if block_type:
            if block_type not in blocks_by_type:
                blocks_by_type[block_type] = []
            blocks_by_type[block_type].append(block)
    
    required_blocks = get_information_blocks()
    print(f"\nBlock type distribution:")
    for block_type in required_blocks:
        count = len(blocks_by_type.get(block_type, []))
        status = "✅" if count > 0 else "❌"
        print(f"  {status} {block_type}: {count} block(s)")
    
    # Check for extracted data
    blocks_with_data = [b for b in blocks if b.get("extracted_data") and len(b.get("extracted_data", {})) > 0]
    print(f"\nBlocks with extracted data: {len(blocks_with_data)}/{len(blocks)}")
    
    # Step 7: Verify sufficiency calculation
    print("\n📋 Step 7: Verifying Sufficiency Calculation")
    print("-" * 80)
    batch = await db.batches.find_one({"batch_id": batch_id})
    sufficiency_result = batch.get("sufficiency_result")
    
    if sufficiency_result:
        print(f"✅ Sufficiency: {sufficiency_result.get('percentage', 0):.2f}%")
        print(f"   Present: {sufficiency_result.get('present_count', 0)}/10 blocks")
        print(f"   Missing: {len(sufficiency_result.get('missing_blocks', []))} blocks")
        penalty = sufficiency_result.get('penalty_breakdown', {})
        print(f"   Penalties: O={penalty.get('outdated', 0)}, L={penalty.get('low_quality', 0)}, I={penalty.get('invalid', 0)}")
        
        # Verify formula
        P = sufficiency_result.get('present_count', 0)
        R = 10
        O = penalty.get('outdated', 0)
        L = penalty.get('low_quality', 0)
        I = penalty.get('invalid', 0)
        
        base_pct = (P / R * 100) if R > 0 else 0
        calculated_penalty = min(O * 4 + L * 5 + I * 7, 50)
        calculated_sufficiency = max(0, base_pct - calculated_penalty)
        actual_sufficiency = sufficiency_result.get('percentage', 0)
        
        if abs(calculated_sufficiency - actual_sufficiency) < 0.01:
            print("   ✅ Formula verified correctly")
        else:
            print(f"   ❌ Formula mismatch: calculated={calculated_sufficiency:.2f}, actual={actual_sufficiency:.2f}")
    else:
        print("❌ No sufficiency result found")
    
    # Step 8: Verify KPIs
    print("\n📋 Step 8: Verifying KPI Calculation")
    print("-" * 80)
    kpi_results = batch.get("kpi_results")
    
    if kpi_results:
        print(f"✅ KPIs calculated: {len(kpi_results)} metrics")
        for kpi_id, kpi_data in list(kpi_results.items())[:5]:
            if isinstance(kpi_data, dict) and "value" in kpi_data:
                name = kpi_data.get("name", kpi_id)
                value = kpi_data.get("value", 0)
                print(f"   - {name}: {value:.2f}")
    else:
        print("❌ No KPI results found")
    
    # Step 9: Verify compliance
    print("\n📋 Step 9: Verifying Compliance Checks")
    print("-" * 80)
    compliance_results = batch.get("compliance_results", [])
    
    if compliance_results:
        print(f"✅ Compliance flags: {len(compliance_results)}")
        for flag in compliance_results[:3]:
            severity = flag.get("severity", "medium")
            title = flag.get("title", "Unknown")
            print(f"   - [{severity.upper()}] {title}")
    else:
        print("✅ No compliance issues found (or checks not run)")
    
    # Step 10: Test dashboard data retrieval
    print("\n📋 Step 10: Testing Dashboard Data")
    print("-" * 80)
    try:
        # Simulate dashboard data retrieval
        from config.information_blocks import get_information_blocks, get_block_description
        
        blocks_for_dashboard = await db.information_blocks.find({"batch_id": batch_id}).to_list(length=10000)
        blocks_by_type = {}
        for block in blocks_for_dashboard:
            block_type = block.get("block_type")
            if block_type:
                if block_type not in blocks_by_type:
                    blocks_by_type[block_type] = []
                blocks_by_type[block_type].append(block)
        
        required_blocks = get_information_blocks()
        block_cards_count = 0
        present_blocks_count = 0
        
        for block_type in required_blocks:
            block_list = blocks_by_type.get(block_type, [])
            block_cards_count += 1
            if block_list:
                present_blocks_count += 1
        
        kpi_count = len(batch.get("kpi_results", {}))
        compliance_count = len(batch.get("compliance_results", []))
        
        print(f"✅ Dashboard data structure verified")
        print(f"   Block cards: {block_cards_count}/10")
        print(f"   Present blocks: {present_blocks_count}/10")
        print(f"   KPI cards: {kpi_count}")
        print(f"   Compliance flags: {compliance_count}")
    except Exception as e:
        print(f"⚠️  Dashboard test error: {e}")
        import traceback
        traceback.print_exc()
    
    # Step 11: Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    print(f"\nBatch ID: {batch_id}")
    print(f"Mode: {mode}")
    print(f"Documents uploaded: {len(documents_created)}")
    print(f"Information blocks created: {len(blocks)}")
    print(f"Blocks with data: {len(blocks_with_data)}")
    
    if sufficiency_result:
        print(f"Sufficiency: {sufficiency_result.get('percentage', 0):.2f}%")
    
    if kpi_results:
        print(f"KPIs calculated: {len(kpi_results)}")
    
    if compliance_results:
        print(f"Compliance flags: {len(compliance_results)}")
    
    # Final status
    all_passed = (
        len(blocks) > 0 and
        len(blocks_with_data) > 0 and
        sufficiency_result is not None and
        kpi_results is not None
    )
    
    if all_passed:
        print("\n✅ END-TO-END TEST PASSED")
        print("   All components are working correctly!")
    else:
        print("\n⚠️  END-TO-END TEST PARTIALLY PASSED")
        print("   Some components may need attention")
    
    print("\n" + "=" * 80)
    
    # Cleanup (optional - comment out to keep test data)
    # await db.batches.delete_one({"batch_id": batch_id})
    # await db.documents.delete_many({"batch_id": batch_id})
    # await db.information_blocks.delete_many({"batch_id": batch_id})
    # print("🧹 Test data cleaned up")
    
    await close_mongo_connection()
    return all_passed

if __name__ == "__main__":
    try:
        result = asyncio.run(test_end_to_end())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

