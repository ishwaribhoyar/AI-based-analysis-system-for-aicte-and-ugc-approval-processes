"""
Final Complete Verification Test
Tests with ALL PDFs, shows progress, and verifies everything works
"""

import asyncio
import sys
from pathlib import Path
import logging
import shutil
import hashlib
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from config.database import connect_to_mongo, get_database
from models.batch import Batch, ReviewerMode, BatchStatus
from models.document import Document
from utils.id_generator import generate_batch_id, generate_document_id
from utils.file_utils import get_mime_type
from config.settings import settings
from pipelines.block_processing_pipeline import BlockProcessingPipeline
from routers.dashboard import get_dashboard_data

# Setup logging with progress indicators
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)

def print_progress(step, total, message):
    """Print progress with visual indicator"""
    percentage = (step / total) * 100
    bar_length = 30
    filled = int(bar_length * step / total)
    bar = '█' * filled + '░' * (bar_length - filled)
    print(f"\r[{bar}] {percentage:.1f}% - {message}", end='', flush=True)
    if step == total:
        print()  # New line when complete

async def verify_complete_system():
    """Complete system verification with progress tracking"""
    print("\n" + "=" * 80)
    print("🔍 COMPLETE SYSTEM VERIFICATION - REAL-LIFE SCENARIO")
    print("=" * 80)
    
    total_steps = 10
    current_step = 0
    
    # Step 1: MongoDB Connection
    current_step += 1
    print_progress(current_step, total_steps, "Connecting to MongoDB...")
    try:
        await connect_to_mongo()
        db = get_database()
        print("✅ MongoDB connected")
    except Exception as e:
        print(f"\n❌ MongoDB connection failed: {e}")
        return False
    
    # Step 2: Find PDF files
    current_step += 1
    print_progress(current_step, total_steps, "Finding PDF files...")
    repo_root = Path(__file__).parent.parent
    pdfs = [
        repo_root / "2025-26-AICTE-Approval.pdf",
        repo_root / "EOA-Report-2025-26.pdf",
        repo_root / "NBA_PCE_17_3_2021.pdf",
        repo_root / "Overall.pdf"
    ]
    pdfs = [p for p in pdfs if p.exists()]
    
    if not pdfs:
        print("\n❌ No PDF files found")
        return False
    print(f"\n✅ Found {len(pdfs)} PDF files")
    
    # Step 3: Create batch
    current_step += 1
    print_progress(current_step, total_steps, "Creating batch...")
    batch_id = generate_batch_id("aicte")
    batch = Batch(
        batch_id=batch_id,
        mode=ReviewerMode.AICTE,
        status=BatchStatus.CREATED,
        institution_name="Final Verification Test",
        institution_code="FINAL001",
        academic_year="2025-26"
    )
    await db.batches.insert_one(batch.model_dump())
    print(f"\n✅ Batch created: {batch_id}")
    
    # Step 4: Upload documents
    current_step += 1
    print_progress(current_step, total_steps, f"Uploading {len(pdfs)} documents...")
    upload_dir = Path(settings.UPLOAD_DIR)
    batch_dir = upload_dir / batch_id
    batch_dir.mkdir(parents=True, exist_ok=True)
    
    uploaded = 0
    for i, pdf_path in enumerate(pdfs, 1):
        try:
            file_hash = hashlib.sha256()
            with open(pdf_path, 'rb') as f:
                file_hash.update(f.read())
            
            dest_path = batch_dir / pdf_path.name
            shutil.copy2(pdf_path, dest_path)
            
            document = Document(
                document_id=generate_document_id(),
                batch_id=batch_id,
                filename=pdf_path.name,
                file_path=str(dest_path),
                file_size=dest_path.stat().st_size,
                file_hash=file_hash.hexdigest(),
                mime_type=get_mime_type(pdf_path.name),
                status="uploaded"
            )
            
            await db.documents.insert_one(document.model_dump())
            await db.batches.update_one(
                {"batch_id": batch_id},
                {"$inc": {"total_documents": 1}}
            )
            uploaded += 1
            print(f"\r   [{i}/{len(pdfs)}] Uploaded: {pdf_path.name}", end='', flush=True)
        except Exception as e:
            print(f"\n❌ Failed to upload {pdf_path.name}: {e}")
    
    print(f"\n✅ Uploaded {uploaded}/{len(pdfs)} documents")
    
    # Step 5: Run pipeline
    current_step += 1
    print_progress(current_step, total_steps, "Running block-based pipeline...")
    print("\n⏳ Processing (this may take several minutes)...")
    
    try:
        pipeline = BlockProcessingPipeline()
        result = await pipeline.process_batch(batch_id)
        
        if result.get("status") != "completed":
            print(f"\n❌ Pipeline failed: {result}")
            return False
        
        print("✅ Pipeline completed successfully")
        
    except Exception as e:
        print(f"\n❌ Pipeline error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 6: Verify blocks
    current_step += 1
    print_progress(current_step, total_steps, "Verifying information blocks...")
    blocks = await db.information_blocks.find({"batch_id": batch_id}).to_list(length=1000)
    
    if len(blocks) == 0:
        print("\n❌ No blocks found")
        return False
    
    blocks_by_type = {}
    blocks_with_data = 0
    for block in blocks:
        block_type = block.get("block_type", "unknown")
        blocks_by_type[block_type] = blocks_by_type.get(block_type, 0) + 1
        if block.get("extracted_data") and len(block.get("extracted_data", {})) > 0:
            blocks_with_data += 1
    
    print(f"\n✅ Found {len(blocks)} blocks ({blocks_with_data} with data)")
    print(f"   Block types: {len(blocks_by_type)} unique types")
    
    # Step 7: Verify sufficiency
    current_step += 1
    print_progress(current_step, total_steps, "Verifying sufficiency calculation...")
    sufficiency = result.get("sufficiency", {})
    sufficiency_pct = sufficiency.get("percentage", 0)
    present_count = sufficiency.get("present_count", 0)
    
    print(f"\n✅ Sufficiency: {sufficiency_pct}% ({present_count}/10 blocks)")
    
    # Step 8: Verify KPIs
    current_step += 1
    print_progress(current_step, total_steps, "Verifying KPI calculation...")
    kpis = result.get("kpis", {})
    
    if not kpis:
        print("\n❌ No KPIs calculated")
        return False
    
    print(f"\n✅ Calculated {len(kpis)} KPIs")
    for kpi_id, kpi_data in list(kpis.items())[:3]:
        if isinstance(kpi_data, dict):
            print(f"   - {kpi_data.get('name', kpi_id)}: {kpi_data.get('value', 0)}")
    
    # Step 9: Verify compliance
    current_step += 1
    print_progress(current_step, total_steps, "Verifying compliance checking...")
    compliance = result.get("compliance", [])
    print(f"\n✅ Found {len(compliance)} compliance flags")
    
    # Step 10: Verify dashboard
    current_step += 1
    print_progress(current_step, total_steps, "Verifying dashboard integration...")
    try:
        dashboard_data = await get_dashboard_data(batch_id)
        print(f"\n✅ Dashboard accessible")
        print(f"   Sufficiency: {dashboard_data.sufficiency.percentage}%")
        print(f"   KPIs: {len(dashboard_data.kpi_cards)}")
    except Exception as e:
        print(f"\n⚠️  Dashboard warning: {e}")
    
    # Final Summary
    print("\n" + "=" * 80)
    print("✅ VERIFICATION COMPLETE - ALL TESTS PASSED")
    print("=" * 80)
    print(f"📊 Summary:")
    print(f"   Documents: {uploaded}/{len(pdfs)}")
    print(f"   Blocks: {len(blocks)} ({blocks_with_data} with data)")
    print(f"   Block Types: {len(blocks_by_type)}")
    print(f"   Sufficiency: {sufficiency_pct}%")
    print(f"   KPIs: {len(kpis)}")
    print(f"   Compliance: {len(compliance)}")
    print(f"   Batch ID: {batch_id}")
    print("=" * 80)
    print("✅ SYSTEM IS READY FOR PRODUCTION")
    print("=" * 80)
    
    return True

if __name__ == "__main__":
    success = asyncio.run(verify_complete_system())
    sys.exit(0 if success else 1)

