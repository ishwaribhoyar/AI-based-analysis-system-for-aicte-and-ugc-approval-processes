"""
Complete System Test - Real World Scenario
Tests entire flow with actual PDF files from repository
Handles Docling + One-Shot Extraction
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import shutil
import traceback

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

def find_pdf_files():
    """Find all PDF files in the repository root"""
    repo_root = Path(__file__).parent.parent
    pdf_files = []
    
    # Check root directory for PDFs
    for pdf_file in repo_root.glob("*.pdf"):
        if pdf_file.is_file() and pdf_file.stat().st_size > 0:
            # Skip sample.pdf if it's too small
            if pdf_file.name.lower() != "sample.pdf" or pdf_file.stat().st_size > 10000:
                pdf_files.append(pdf_file)
    
    print(f"\nFound {len(pdf_files)} PDF files:")
    for pdf in pdf_files:
        size_mb = pdf.stat().st_size / (1024 * 1024)
        print(f"   [OK] {pdf.name} ({size_mb:.2f} MB)")
    
    return pdf_files

def check_dependencies():
    """Check if all required dependencies are installed"""
    print("\nChecking dependencies...")
    
    missing = []
    
    # Check SQLite/SQLAlchemy
    try:
        from sqlalchemy import create_engine
        print("   [OK] SQLAlchemy")
    except ImportError:
        missing.append("sqlalchemy")
        print("   [FAIL] SQLAlchemy")
    
    # Check Docling
    try:
        from docling.document_converter import DocumentConverter
        print("   [OK] Docling")
    except ImportError:
        missing.append("docling")
        print("   [SKIP] Docling (optional - will use fallback)")
    
    # Check PaddleOCR
    try:
        from paddleocr import PaddleOCR
        print("   ✓ PaddleOCR")
    except ImportError:
        missing.append("paddleocr")
        print("   [SKIP] PaddleOCR (optional - fallback OCR)")
    
    # Check OpenAI
    try:
        import openai
        print("   [OK] OpenAI")
    except ImportError:
        missing.append("openai")
        print("   [FAIL] OpenAI")
    
    # Check pdf2image
    try:
        from pdf2image import convert_from_path
        print("   [OK] pdf2image")
    except ImportError:
        missing.append("pdf2image")
        print("   [SKIP] pdf2image (optional - for OCR)")
    
    if missing:
        print(f"\n[WARN] Missing dependencies: {', '.join(missing)}")
        print("   Install with: pip install " + " ".join(missing))
        return False
    
    return True

def test_database():
    """Test database connection and initialization"""
    print("\nTesting database...")
    
    try:
        from config.database import init_db, get_db, close_db, Batch
        init_db()
        print("   [OK] Database initialized")
        
        db = get_db()
        # Test query
        count = db.query(Batch).count()
        print(f"   [OK] Database connection working ({count} batches)")
        close_db(db)
        return True
    except Exception as e:
        print(f"   [FAIL] Database error: {e}")
        traceback.print_exc()
        return False

def test_docling_service():
    """Test Docling service"""
    print("\nTesting Docling service...")
    
    try:
        from services.docling_service import DoclingService
        service = DoclingService()
        print("   [OK] DoclingService initialized")
        return True
    except ImportError as e:
        print(f"   [WARN] Docling not available: {e}")
        print("   Will use fallback methods")
        return True  # Not critical
    except Exception as e:
        print(f"   [FAIL] Docling error: {e}")
        return False

def create_batch_and_upload_files(mode="aicte"):
    """Create a batch and upload PDF files"""
    from config.database import get_db, Batch, File, close_db
    from utils.id_generator import generate_batch_id, generate_document_id
    from config.settings import settings
    
    db = get_db()
    
    try:
        # Create batch
        batch_id = generate_batch_id(mode)
        batch = Batch(
            id=batch_id,
            mode=mode,
            status="created",
            created_at=datetime.utcnow()
        )
        db.add(batch)
        db.commit()
        print(f"\n[OK] Created batch: {batch_id}")
        
        # Find PDF files
        pdf_files = find_pdf_files()
        if not pdf_files:
            print("[FAIL] No PDF files found in repository root")
            return None, []
        
        # Create upload directory
        upload_dir = Path(settings.UPLOAD_DIR) / batch_id
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy files and create file records
        file_records = []
        for pdf_file in pdf_files:
            try:
                # Copy file to upload directory
                dest_path = upload_dir / pdf_file.name
                shutil.copy2(pdf_file, dest_path)
                
                # Create file record
                file_id = generate_document_id()
                file_record = File(
                    id=file_id,
                    batch_id=batch_id,
                    filename=pdf_file.name,
                    filepath=str(dest_path),
                    file_size=pdf_file.stat().st_size,
                    uploaded_at=datetime.utcnow()
                )
                db.add(file_record)
                file_records.append(file_record)
                print(f"   [OK] Uploaded: {pdf_file.name}")
            except Exception as e:
                print(f"   [FAIL] Failed to upload {pdf_file.name}: {e}")
        
        db.commit()
        print(f"\n[OK] Uploaded {len(file_records)} files to batch {batch_id}")
        
        return batch_id, file_records
    
    except Exception as e:
        print(f"\n[FAIL] Error creating batch/uploading files: {e}")
        traceback.print_exc()
        db.rollback()
        return None, []
    finally:
        close_db(db)

def run_pipeline(batch_id):
    """Run the complete processing pipeline"""
    print(f"\nStarting pipeline for batch {batch_id}")
    print("=" * 80)
    
    try:
        from pipelines.block_processing_pipeline import BlockProcessingPipeline
        pipeline = BlockProcessingPipeline()
        result = pipeline.process_batch(batch_id)
        print(f"\n[OK] Pipeline completed: {result.get('status')}")
        return result
    except Exception as e:
        print(f"\n[FAIL] Pipeline error: {e}")
        traceback.print_exc()
        return None

def verify_results(batch_id):
    """Verify all results are correctly stored"""
    print(f"\nVerifying results for batch {batch_id}")
    print("=" * 80)
    
    from config.database import get_db, Batch, Block, File, ComplianceFlag, close_db
    
    db = get_db()
    
    try:
        # Get batch
        batch = db.query(Batch).filter(Batch.id == batch_id).first()
        if not batch:
            print("[FAIL] Batch not found")
            return False
        
        print(f"[OK] Batch status: {batch.status}")
        
        if batch.status != "completed":
            print(f"[WARN] Batch status is {batch.status}, not completed")
            return False
        
        # Verify files
        files = db.query(File).filter(File.batch_id == batch_id).all()
        print(f"\n[OK] Files: {len(files)}")
        for f in files:
            print(f"   - {f.filename}")
        
        # Verify blocks
        blocks = db.query(Block).filter(Block.batch_id == batch_id).all()
        print(f"\n[OK] Information Blocks: {len(blocks)}")
        
        if len(blocks) == 0:
            print("[WARN] No blocks extracted!")
            return False
        
        # Group by block type
        blocks_by_type = {}
        for block in blocks:
            block_type = block.block_type
            if block_type not in blocks_by_type:
                blocks_by_type[block_type] = []
            blocks_by_type[block_type].append(block)
        
        print(f"\n   Block breakdown:")
        for block_type, block_list in sorted(blocks_by_type.items()):
            valid_count = sum(1 for b in block_list if not b.is_invalid)
            has_data = sum(1 for b in block_list if b.data and len(b.data) > 0)
            print(f"   - {block_type}: {len(block_list)} blocks, {valid_count} valid, {has_data} with data")
        
        # Verify sufficiency
        sufficiency = batch.sufficiency_result
        if sufficiency:
            print(f"\n[OK] Sufficiency: {sufficiency.get('percentage', 0):.2f}%")
            print(f"   Present: {sufficiency.get('present_count', 0)}/{sufficiency.get('required_count', 10)}")
            missing = sufficiency.get('missing_blocks', [])
            if missing:
                print(f"   Missing: {', '.join(missing[:5])}")
        else:
            print("[WARN] Sufficiency not calculated")
        
        # Verify KPIs
        kpis = batch.kpi_results
        if kpis:
            print(f"\n[OK] KPIs: {len(kpis)} metrics")
            for kpi_id, kpi_data in list(kpis.items())[:5]:
                if isinstance(kpi_data, dict):
                    value = kpi_data.get('value', 0)
                    name = kpi_data.get('name', kpi_id)
                    print(f"   - {name}: {value:.2f}")
        else:
            print("[WARN] KPIs not calculated")
        
        # Verify compliance
        compliance_flags = db.query(ComplianceFlag).filter(ComplianceFlag.batch_id == batch_id).all()
        print(f"\n[OK] Compliance Flags: {len(compliance_flags)}")
        for flag in compliance_flags[:5]:
            print(f"   - [{flag.severity.upper()}] {flag.title}")
        
        # Verify trends
        trends = batch.trend_results
        if trends:
            has_trends = trends.get('has_trend_data', False)
            trend_data = trends.get('trend_data', [])
            print(f"\n[OK] Trends: {'Yes' if has_trends else 'No'}")
            if has_trends:
                print(f"   Trend data points: {len(trend_data)}")
                for point in trend_data[:3]:
                    print(f"   - {point.get('year')}: {point.get('kpi_name')} = {point.get('value')}")
        else:
            print("[WARN] Trends not extracted")
        
        return True
    
    except Exception as e:
        print(f"[FAIL] Verification error: {e}")
        traceback.print_exc()
        return False
    finally:
        close_db(db)

def test_dashboard_api(batch_id):
    """Test dashboard API endpoint"""
    print(f"\nTesting Dashboard API")
    print("=" * 80)
    
    try:
        from routers.dashboard import get_dashboard_data
        dashboard_data = get_dashboard_data(batch_id)
        
        print(f"[OK] Dashboard data retrieved")
        print(f"   Mode: {dashboard_data.mode}")
        print(f"   KPI Cards: {len(dashboard_data.kpi_cards)}")
        print(f"   Block Cards: {len(dashboard_data.block_cards)}")
        print(f"   Sufficiency: {dashboard_data.sufficiency.percentage:.2f}%")
        print(f"   Compliance Flags: {len(dashboard_data.compliance_flags)}")
        print(f"   Trend Data Points: {len(dashboard_data.trend_data)}")
        
        return True
    except Exception as e:
        print(f"[FAIL] Dashboard API error: {e}")
        traceback.print_exc()
        return False

def test_report_generation(batch_id):
    """Test PDF report generation"""
    print(f"\nTesting Report Generation")
    print("=" * 80)
    
    try:
        from services.report_generator import ReportGenerator
        generator = ReportGenerator()
        report_path = generator.generate_report(batch_id)
        
        if os.path.exists(report_path):
            size_mb = os.path.getsize(report_path) / (1024 * 1024)
            print(f"[OK] Report generated: {report_path}")
            print(f"   Size: {size_mb:.2f} MB")
            return True
        else:
            print(f"[FAIL] Report file not found: {report_path}")
            return False
    except Exception as e:
        print(f"[FAIL] Report generation error: {e}")
        traceback.print_exc()
        return False

def main():
    """Run complete end-to-end test"""
    print("=" * 80)
    print("COMPLETE SYSTEM TEST - REAL WORLD SCENARIO")
    print("=" * 80)
    print(f"Testing entire platform with real PDF files")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    # Step 0: Check dependencies
    if not check_dependencies():
        print("\n[WARN] Some dependencies missing, but continuing...")
    
    # Step 1: Test database
    if not test_database():
        print("\n[FAIL] Database test failed. Exiting.")
        return False
    
    # Step 2: Test Docling
    test_docling_service()
    
    # Step 3: Create batch and upload files
    print("\n" + "=" * 80)
    print("STEP 1: Create Batch & Upload Files")
    print("=" * 80)
    batch_id, file_records = create_batch_and_upload_files(mode="aicte")
    
    if not batch_id or len(file_records) == 0:
        print("[FAIL] Failed to create batch or upload files. Exiting.")
        return False
    
    # Step 4: Run pipeline
    print("\n" + "=" * 80)
    print("STEP 2: Run Processing Pipeline")
    print("=" * 80)
    result = run_pipeline(batch_id)
    
    if not result:
        print("[FAIL] Pipeline failed. Exiting.")
        return False
    
    if result.get('status') != 'completed':
        print(f"[WARN] Pipeline status: {result.get('status')}")
        # Continue anyway to see what was extracted
    
    # Step 5: Verify results
    print("\n" + "=" * 80)
    print("STEP 3: Verify Results")
    print("=" * 80)
    verification_passed = verify_results(batch_id)
    
    # Step 6: Test dashboard
    print("\n" + "=" * 80)
    print("STEP 4: Test Dashboard API")
    print("=" * 80)
    dashboard_passed = test_dashboard_api(batch_id)
    
    # Step 7: Test report generation
    print("\n" + "=" * 80)
    print("STEP 5: Test Report Generation")
    print("=" * 80)
    report_passed = test_report_generation(batch_id)
    
    # Final summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Batch ID: {batch_id}")
    print(f"Files Uploaded: {len(file_records)}")
    print(f"Pipeline: {'[PASS]' if result else '[FAIL]'}")
    print(f"Verification: {'[PASS]' if verification_passed else '[FAIL]'}")
    print(f"Dashboard: {'[PASS]' if dashboard_passed else '[FAIL]'}")
    print(f"Report: {'[PASS]' if report_passed else '[FAIL]'}")
    
    all_passed = result and verification_passed and dashboard_passed and report_passed
    
    if all_passed:
        print("\n[SUCCESS] ALL TESTS PASSED! System is working correctly.")
        print(f"\n💡 View results:")
        print(f"   - Dashboard: http://localhost:3000/dashboard?batch_id={batch_id}")
        print(f"   - API: http://localhost:8000/api/dashboard/{batch_id}")
    else:
        print("\n[WARN] SOME TESTS FAILED. Please check the errors above.")
        print("   The system may still be partially functional.")
    
    return all_passed

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n[WARN] Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n[FAIL] Fatal error: {e}")
        traceback.print_exc()
        sys.exit(1)

