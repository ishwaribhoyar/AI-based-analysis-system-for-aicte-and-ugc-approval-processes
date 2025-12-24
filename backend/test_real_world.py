"""
Real-World End-to-End Test
Tests the complete system with actual PDF files from repository
"""

import asyncio
import sys
import os
from pathlib import Path
import json
from datetime import datetime
import traceback

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from config.database import connect_to_mongo, get_database, close_mongo_connection
    from pipelines.block_processing_pipeline import BlockProcessingPipeline
    from services.block_sufficiency import BlockSufficiencyService
    from services.kpi import KPIService
    from services.compliance import ComplianceService
    from config.information_blocks import get_information_blocks
    from utils.id_generator import generate_batch_id, generate_document_id
    from utils.file_utils import get_file_hash, get_mime_type
    from config.settings import settings
    import logging
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("⚠️  Make sure you're in the virtual environment:")
    print("   cd backend")
    print("   venv\\Scripts\\activate  # Windows")
    print("   source venv/bin/activate  # Linux/Mac")
    sys.exit(1)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_real_world():
    """Complete real-world end-to-end test"""
    
    print("=" * 80)
    print("REAL-WORLD END-TO-END TEST")
    print("Information Block Architecture - Complete Flow Test")
    print("=" * 80)
    
    # Pre-flight checks
    print("\n📋 Pre-Flight Checks")
    print("-" * 80)
    
    # Check OpenAI API key
    if not settings.OPENAI_API_KEY:
        print("❌ OPENAI_API_KEY not set in .env file")
        print("   Please set OPENAI_API_KEY in .env file")
        return False
    else:
        print("✅ OPENAI_API_KEY is set")
    
    # Check MongoDB
    try:
        await connect_to_mongo()
        db = get_database()
        # Test connection
        await db.batches.find_one({})
        print("✅ MongoDB connection successful")
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        print("   Please ensure MongoDB is running:")
        print("   - Check MONGODB_URL in .env file")
        print("   - Start MongoDB service")
        return False
    
    # Find PDF files
    print("\n📋 Step 1: Finding PDF Files")
    print("-" * 80)
    repo_root = Path(__file__).parent.parent
    pdf_files = []
    
    # Check root directory for PDFs
    for pdf_file in repo_root.glob("*.pdf"):
        if pdf_file.is_file() and pdf_file.name not in ["README.pdf", "LICENSE.pdf"]:
            pdf_files.append(pdf_file)
            print(f"  ✅ Found: {pdf_file.name} ({pdf_file.stat().st_size:,} bytes)")
    
    if not pdf_files:
        print("❌ No PDF files found in repository root")
        print("   Expected files: 2025-26-AICTE-Approval.pdf, EOA-Report-2025-26.pdf, etc.")
        return False
    
    print(f"\n✅ Found {len(pdf_files)} PDF file(s) for testing")
    
    # Create test batch
    print("\n📋 Step 2: Creating Test Batch")
    print("-" * 80)
    batch_id = generate_batch_id("aicte")
    mode = "aicte"
    institution_name = "Test Institution - Real World Test"
    
    batch_data = {
        "batch_id": batch_id,
        "mode": mode,
        "status": "created",
        "institution_name": institution_name,
        "institution_code": "TEST_RW_001",
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
    
    # Upload PDF files
    print("\n📋 Step 3: Uploading PDF Files")
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
    
    # Process batch
    print("\n📋 Step 4: Processing Batch Through Pipeline")
    print("-" * 80)
    print("⚠️  This will take several minutes...")
    print("   - Preprocessing PDFs")
    print("   - Classifying blocks")
    print("   - Extracting data")
    print("   - Calculating metrics")
    
    try:
        pipeline = BlockProcessingPipeline()
        print(f"\n🚀 Starting pipeline for batch {batch_id}...")
        result = await pipeline.process_batch(batch_id)
        
        if result.get("status") == "completed":
            print("\n✅ Pipeline completed successfully!")
        else:
            print(f"\n⚠️  Pipeline status: {result.get('status')}")
            
    except Exception as e:
        print(f"\n❌ Pipeline failed: {e}")
        traceback.print_exc()
        return False
    
    # Verify results
    print("\n📋 Step 5: Verifying Results")
    print("-" * 80)
    
    # Get updated batch
    batch = await db.batches.find_one({"batch_id": batch_id})
    if not batch:
        print("❌ Batch not found after processing")
        return False
    
    # Check blocks
    blocks = await db.information_blocks.find({"batch_id": batch_id}).to_list(length=10000)
    print(f"\n📊 Information Blocks:")
    print(f"   Total blocks created: {len(blocks)}")
    
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
    print(f"\n   Block type distribution:")
    present_count = 0
    for block_type in required_blocks:
        count = len(blocks_by_type.get(block_type, []))
        blocks_with_data = sum(1 for b in blocks_by_type.get(block_type, []) 
                              if b.get("extracted_data") and len(b.get("extracted_data", {})) > 0)
        status = "✅" if blocks_with_data > 0 else "❌"
        if blocks_with_data > 0:
            present_count += 1
        print(f"   {status} {block_type}: {count} block(s), {blocks_with_data} with data")
    
    # Check sufficiency
    sufficiency_result = batch.get("sufficiency_result")
    if sufficiency_result:
        print(f"\n📈 Sufficiency:")
        print(f"   Score: {sufficiency_result.get('percentage', 0):.2f}%")
        print(f"   Present: {sufficiency_result.get('present_count', 0)}/10 blocks")
        missing = sufficiency_result.get('missing_blocks', [])
        if missing:
            print(f"   Missing: {len(missing)} blocks")
            for mb in missing[:3]:
                print(f"     - {mb}")
        penalty = sufficiency_result.get('penalty_breakdown', {})
        print(f"   Penalties: O={penalty.get('outdated', 0)}, L={penalty.get('low_quality', 0)}, I={penalty.get('invalid', 0)}")
    else:
        print("\n❌ No sufficiency result")
    
    # Check KPIs
    kpi_results = batch.get("kpi_results")
    if kpi_results:
        print(f"\n📊 KPIs:")
        print(f"   Calculated: {len(kpi_results)} metrics")
        for kpi_id, kpi_data in list(kpi_results.items())[:5]:
            if isinstance(kpi_data, dict) and "value" in kpi_data:
                name = kpi_data.get("name", kpi_id)
                value = kpi_data.get("value", 0)
                print(f"   - {name}: {value:.2f}")
    else:
        print("\n❌ No KPI results")
    
    # Check compliance
    compliance_results = batch.get("compliance_results", [])
    if compliance_results:
        print(f"\n⚠️  Compliance Flags:")
        print(f"   Total: {len(compliance_results)}")
        for flag in compliance_results[:3]:
            severity = flag.get("severity", "medium")
            title = flag.get("title", "Unknown")
            print(f"   [{severity.upper()}] {title}")
    else:
        print(f"\n✅ No compliance issues found")
    
    # Final summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    print(f"\nBatch ID: {batch_id}")
    print(f"Mode: {mode.upper()}")
    print(f"Documents: {len(documents_created)}")
    print(f"Information Blocks: {len(blocks)}")
    print(f"Present Blocks: {present_count}/10")
    
    if sufficiency_result:
        print(f"Sufficiency: {sufficiency_result.get('percentage', 0):.2f}%")
    
    if kpi_results:
        print(f"KPIs: {len(kpi_results)} calculated")
    
    if compliance_results:
        print(f"Compliance Flags: {len(compliance_results)}")
    
    # Success criteria
    success = (
        len(blocks) > 0 and
        present_count > 0 and
        sufficiency_result is not None and
        kpi_results is not None
    )
    
    if success:
        print("\n✅ REAL-WORLD TEST PASSED!")
        print("   All components working correctly with actual PDF files")
        print(f"\n   View results at: http://localhost:3000/dashboard?batch_id={batch_id}")
    else:
        print("\n⚠️  REAL-WORLD TEST PARTIALLY PASSED")
        print("   Some components may need attention")
    
    print("\n" + "=" * 80)
    
    await close_mongo_connection()
    return success

if __name__ == "__main__":
    try:
        result = asyncio.run(test_real_world())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        traceback.print_exc()
        sys.exit(1)

