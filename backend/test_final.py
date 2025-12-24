"""
Final System Test - Clean version without Unicode issues
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import shutil

sys.path.insert(0, str(Path(__file__).parent))

def main():
    print("=" * 80)
    print("FINAL SYSTEM TEST")
    print("=" * 80)
    
    try:
        from config.database import init_db, get_db, Batch, Block, File, ComplianceFlag, close_db
        from pipelines.block_processing_pipeline import BlockProcessingPipeline
        from utils.id_generator import generate_batch_id, generate_document_id
        from config.settings import settings
        
        # Initialize
        init_db()
        print("[OK] Database initialized")
        
        # Create batch
        batch_id = generate_batch_id("aicte")
        db = get_db()
        from datetime import timezone
        batch = Batch(id=batch_id, mode="aicte", status="created", created_at=datetime.now(timezone.utc))
        db.add(batch)
        db.commit()
        print(f"[OK] Created batch: {batch_id}")
        
        # Find and upload PDFs
        repo_root = Path(__file__).parent.parent
        pdf_files = [f for f in repo_root.glob("*.pdf") if f.is_file() and f.stat().st_size > 0 and f.name.lower() != "sample.pdf"][:4]
        
        print(f"[OK] Found {len(pdf_files)} PDF files")
        
        upload_dir = Path(settings.UPLOAD_DIR) / batch_id
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        for pdf_file in pdf_files:
            dest_path = upload_dir / pdf_file.name
            shutil.copy2(pdf_file, dest_path)
            file_id = generate_document_id()
            from datetime import timezone
            file_record = File(id=file_id, batch_id=batch_id, filename=pdf_file.name, 
                             filepath=str(dest_path), file_size=pdf_file.stat().st_size, 
                             uploaded_at=datetime.now(timezone.utc))
            db.add(file_record)
            print(f"  [OK] Uploaded: {pdf_file.name}")
        
        db.commit()
        close_db(db)
        
        # Run pipeline
        print("\n[INFO] Running pipeline...")
        pipeline = BlockProcessingPipeline()
        result = pipeline.process_batch(batch_id)
        
        if result and result.get('status') == 'completed':
            print("[OK] Pipeline completed successfully")
            
            # Verify
            db = get_db()
            batch = db.query(Batch).filter(Batch.id == batch_id).first()
            blocks = db.query(Block).filter(Block.batch_id == batch_id).all()
            
            print(f"[OK] Blocks extracted: {len(blocks)}")
            print(f"[OK] Sufficiency: {batch.sufficiency_result.get('percentage', 0):.2f}%")
            print(f"[OK] KPIs: {len(batch.kpi_results or {})}")
            print(f"[OK] Compliance flags: {len(db.query(ComplianceFlag).filter(ComplianceFlag.batch_id == batch_id).all())}")
            
            close_db(db)
            
            # Test dashboard
            print("\n[INFO] Testing dashboard...")
            from routers.dashboard import get_dashboard_data
            dashboard = get_dashboard_data(batch_id)
            print(f"[OK] Dashboard: {len(dashboard.block_cards)} blocks, {len(dashboard.kpi_cards)} KPIs")
            
            # Test report
            print("\n[INFO] Testing report generation...")
            from services.report_generator import ReportGenerator
            generator = ReportGenerator()
            report_path = generator.generate_report(batch_id)
            if os.path.exists(report_path):
                print(f"[OK] Report generated: {os.path.getsize(report_path) / 1024:.1f} KB")
            
            print("\n" + "=" * 80)
            print("ALL TESTS PASSED!")
            print(f"Batch ID: {batch_id}")
            print("=" * 80)
            return True
        else:
            print("[FAIL] Pipeline failed")
            return False
            
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

