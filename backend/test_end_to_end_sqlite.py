"""
End-to-End Test - Real World Scenario
Tests the complete flow with actual PDF files using SQLite
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import shutil

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from config.database import get_db, Batch, Block, File, ComplianceFlag, init_db, close_db
from pipelines.block_processing_pipeline import BlockProcessingPipeline
from utils.id_generator import generate_batch_id, generate_document_id
from config.settings import settings

def find_pdf_files():
    """Find all PDF files in the repository root"""
    repo_root = Path(__file__).parent.parent
    pdf_files = []
    
    # Check root directory
    for pdf_file in repo_root.glob("*.pdf"):
        if pdf_file.is_file() and pdf_file.stat().st_size > 0:
            pdf_files.append(pdf_file)
    
    print(f"📄 Found {len(pdf_files)} PDF files:")
    for pdf in pdf_files:
        size_mb = pdf.stat().st_size / (1024 * 1024)
        print(f"   - {pdf.name} ({size_mb:.2f} MB)")
    
    return pdf_files

def create_batch_and_upload_files(mode="aicte"):
    """Create a batch and upload PDF files"""
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
        print(f"✅ Created batch: {batch_id}")
        
        # Find PDF files
        pdf_files = find_pdf_files()
        if not pdf_files:
            print("❌ No PDF files found in repository root")
            return None, []
        
        # Create upload directory
        upload_dir = Path(settings.UPLOAD_DIR) / batch_id
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy files and create file records
        file_records = []
        for pdf_file in pdf_files:
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
            print(f"✅ Uploaded: {pdf_file.name}")
        
        db.commit()
        print(f"✅ Uploaded {len(file_records)} files to batch {batch_id}")
        
        return batch_id, file_records
    
    except Exception as e:
        print(f"❌ Error creating batch/uploading files: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return None, []
    finally:
        close_db(db)

def run_pipeline(batch_id):
    """Run the complete processing pipeline"""
    print(f"\n🚀 Starting pipeline for batch {batch_id}")
    print("=" * 80)
    
    pipeline = BlockProcessingPipeline()
    
    try:
        result = pipeline.process_batch(batch_id)
        print(f"\n✅ Pipeline completed: {result.get('status')}")
        return result
    except Exception as e:
        print(f"\n❌ Pipeline error: {e}")
        import traceback
        traceback.print_exc()
        return None

def verify_results(batch_id):
    """Verify all results are correctly stored"""
    print(f"\n🔍 Verifying results for batch {batch_id}")
    print("=" * 80)
    
    db = get_db()
    
    try:
        # Get batch
        batch = db.query(Batch).filter(Batch.id == batch_id).first()
        if not batch:
            print("❌ Batch not found")
            return False
        
        print(f"✅ Batch status: {batch.status}")
        
        # Verify files
        files = db.query(File).filter(File.batch_id == batch_id).all()
        print(f"✅ Files: {len(files)}")
        for f in files:
            print(f"   - {f.filename}")
        
        # Verify blocks
        blocks = db.query(Block).filter(Block.batch_id == batch_id).all()
        print(f"\n✅ Information Blocks: {len(blocks)}")
        
        # Group by block type
        blocks_by_type = {}
        for block in blocks:
            block_type = block.block_type
            if block_type not in blocks_by_type:
                blocks_by_type[block_type] = []
            blocks_by_type[block_type].append(block)
        
        for block_type, block_list in blocks_by_type.items():
            valid_count = sum(1 for b in block_list if not b.is_invalid)
            outdated_count = sum(1 for b in block_list if b.is_outdated)
            low_quality_count = sum(1 for b in block_list if b.is_low_quality)
            invalid_count = sum(1 for b in block_list if b.is_invalid)
            
            print(f"   - {block_type}: {len(block_list)} blocks")
            print(f"     Valid: {valid_count}, Outdated: {outdated_count}, Low Quality: {low_quality_count}, Invalid: {invalid_count}")
        
        # Verify sufficiency
        sufficiency = batch.sufficiency_result
        if sufficiency:
            print(f"\n✅ Sufficiency: {sufficiency.get('percentage', 0):.2f}%")
            print(f"   Present: {sufficiency.get('present_count', 0)}/{sufficiency.get('required_count', 10)}")
            missing = sufficiency.get('missing_blocks', [])
            if missing:
                print(f"   Missing: {', '.join(missing)}")
        else:
            print("⚠️  Sufficiency not calculated")
        
        # Verify KPIs
        kpis = batch.kpi_results
        if kpis:
            print(f"\n✅ KPIs: {len(kpis)} metrics")
            for kpi_id, kpi_data in kpis.items():
                if isinstance(kpi_data, dict):
                    value = kpi_data.get('value', 0)
                    name = kpi_data.get('name', kpi_id)
                    if value is None:
                        print(f"   - {name}: Insufficient Data")
                    else:
                        print(f"   - {name}: {value:.2f}")
        else:
            print("⚠️  KPIs not calculated")
        
        # Verify compliance
        compliance_flags = db.query(ComplianceFlag).filter(ComplianceFlag.batch_id == batch_id).all()
        print(f"\n✅ Compliance Flags: {len(compliance_flags)}")
        for flag in compliance_flags:
            print(f"   - [{flag.severity.upper()}] {flag.title}")
        
        # Verify trends
        trends = batch.trend_results
        if trends:
            has_trends = trends.get('has_trend_data', False)
            trend_data = trends.get('trend_data', [])
            print(f"\n✅ Trends: {'Yes' if has_trends else 'No'}")
            if has_trends:
                print(f"   Trend data points: {len(trend_data)}")
                for point in trend_data[:5]:  # Show first 5
                    print(f"   - {point.get('year')}: {point.get('kpi_name')} = {point.get('value')}")
        else:
            print("⚠️  Trends not extracted")
        
        return True
    
    except Exception as e:
        print(f"❌ Verification error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        close_db(db)

def test_dashboard_data(batch_id):
    """Test dashboard data retrieval"""
    print(f"\n📊 Testing Dashboard Data")
    print("=" * 80)
    
    from routers.dashboard import get_dashboard_data
    
    try:
        dashboard_data = get_dashboard_data(batch_id)
        
        print(f"✅ Dashboard data retrieved")
        print(f"   Mode: {dashboard_data.mode}")
        print(f"   KPI Cards: {len(dashboard_data.kpi_cards)}")
        print(f"   Block Cards: {len(dashboard_data.block_cards)}")
        print(f"   Sufficiency: {dashboard_data.sufficiency.percentage:.2f}%")
        print(f"   Compliance Flags: {len(dashboard_data.compliance_flags)}")
        print(f"   Trend Data Points: {len(dashboard_data.trend_data)}")
        
        return True
    except Exception as e:
        print(f"❌ Dashboard data error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_report_generation(batch_id):
    """Test PDF report generation"""
    print(f"\n📄 Testing Report Generation")
    print("=" * 80)
    
    from services.report_generator import ReportGenerator
    
    try:
        generator = ReportGenerator()
        report_path = generator.generate_report(batch_id)
        
        if os.path.exists(report_path):
            size_mb = os.path.getsize(report_path) / (1024 * 1024)
            print(f"✅ Report generated: {report_path}")
            print(f"   Size: {size_mb:.2f} MB")
            return True
        else:
            print(f"❌ Report file not found: {report_path}")
            return False
    except Exception as e:
        print(f"❌ Report generation error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run complete end-to-end test"""
    print("=" * 80)
    print("🧪 END-TO-END TEST - REAL WORLD SCENARIO")
    print("=" * 80)
    print(f"Testing with SQLite architecture")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    # Initialize database
    print("📦 Initializing SQLite database...")
    init_db()
    print("✅ Database initialized")
    
    # Step 1: Create batch and upload files
    print("\n" + "=" * 80)
    print("STEP 1: Create Batch & Upload Files")
    print("=" * 80)
    batch_id, file_records = create_batch_and_upload_files(mode="aicte")
    
    if not batch_id:
        print("❌ Failed to create batch. Exiting.")
        return False
    
    # Step 2: Run pipeline
    print("\n" + "=" * 80)
    print("STEP 2: Run Processing Pipeline")
    print("=" * 80)
    result = run_pipeline(batch_id)
    
    if not result or result.get('status') != 'completed':
        print("❌ Pipeline failed. Exiting.")
        return False
    
    # Step 3: Verify results
    print("\n" + "=" * 80)
    print("STEP 3: Verify Results")
    print("=" * 80)
    verification_passed = verify_results(batch_id)
    
    if not verification_passed:
        print("❌ Verification failed. Exiting.")
        return False
    
    # Step 4: Test dashboard
    print("\n" + "=" * 80)
    print("STEP 4: Test Dashboard Data")
    print("=" * 80)
    dashboard_passed = test_dashboard_data(batch_id)
    
    # Step 5: Test report generation
    print("\n" + "=" * 80)
    print("STEP 5: Test Report Generation")
    print("=" * 80)
    report_passed = test_report_generation(batch_id)
    
    # Final summary
    print("\n" + "=" * 80)
    print("📋 TEST SUMMARY")
    print("=" * 80)
    print(f"Batch ID: {batch_id}")
    print(f"Files Uploaded: {len(file_records)}")
    print(f"Pipeline: {'✅ PASSED' if result else '❌ FAILED'}")
    print(f"Verification: {'✅ PASSED' if verification_passed else '❌ FAILED'}")
    print(f"Dashboard: {'✅ PASSED' if dashboard_passed else '❌ FAILED'}")
    print(f"Report: {'✅ PASSED' if report_passed else '❌ FAILED'}")
    
    all_passed = result and verification_passed and dashboard_passed and report_passed
    
    if all_passed:
        print("\n🎉 ALL TESTS PASSED! System is working correctly.")
        print(f"\n💡 View results:")
        print(f"   - Dashboard: http://localhost:3000/dashboard?batch_id={batch_id}")
        print(f"   - API: http://localhost:8000/api/dashboard/{batch_id}")
    else:
        print("\n⚠️  SOME TESTS FAILED. Please check the errors above.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

