"""Check what infrastructure data is actually extracted from sample.pdf."""
import sys
import json
from pathlib import Path
from datetime import datetime, timezone
import shutil

sys.path.insert(0, str(Path(__file__).parent))


def main():
    from config.database import get_db, close_db, Batch, File, init_db
    from config.settings import settings
    from utils.id_generator import generate_batch_id, generate_document_id
    from pipelines.block_processing_pipeline import BlockProcessingPipeline
    from routers.dashboard import get_dashboard_data
    from services.kpi import KPIService

    init_db()

    repo_root = Path(__file__).parent.parent
    sample_path = repo_root / "sample.pdf"

    db = get_db()
    try:
        batch_id = generate_batch_id("aicte")
        batch = Batch(
            id=batch_id,
            mode="aicte",
            new_university=0,
            status="created",
            created_at=datetime.now(timezone.utc)
        )
        db.add(batch)
        db.commit()

        upload_dir = Path(settings.UPLOAD_DIR) / batch_id
        upload_dir.mkdir(parents=True, exist_ok=True)
        dest_path = upload_dir / sample_path.name
        shutil.copy2(sample_path, dest_path)

        file_id = generate_document_id()
        file_rec = File(
            id=file_id,
            batch_id=batch_id,
            filename=sample_path.name,
            filepath=str(dest_path),
            file_size=sample_path.stat().st_size,
            uploaded_at=datetime.now(timezone.utc)
        )
        db.add(file_rec)
        db.commit()

        pipeline = BlockProcessingPipeline()
        result = pipeline.process_batch(batch_id)
        
        # Get aggregated data through KPI service
        kpi_service = KPIService()
        
        # Look at what's in the database for infrastructure block
        from config.database import InformationBlock
        blocks = db.query(InformationBlock).filter(
            InformationBlock.batch_id == batch_id
        ).all()
        
        aggregated = {}
        for block in blocks:
            if block.extracted_data:
                data = json.loads(block.extracted_data) if isinstance(block.extracted_data, str) else block.extracted_data
                if block.block_type == "infrastructure":
                    print(f"\n=== INFRASTRUCTURE BLOCK DATA ===")
                    print(json.dumps(data, indent=2))
                if block.block_type == "student_enrollment":
                    print(f"\n=== STUDENT ENROLLMENT BLOCK DATA ===")
                    print(json.dumps(data, indent=2))
                for k, v in data.items():
                    if k not in aggregated or aggregated[k] is None:
                        aggregated[k] = v
        
        print(f"\n=== AGGREGATED DATA (relevant fields) ===")
        relevant_keys = [
            "built_up_area_sqm", "built_up_area_sqm_num", "built_up_area", 
            "total_students", "total_students_num", "student_count",
            "classrooms", "total_classrooms", 
            "library_area_sqm", "library_area",
            "digital_library_resources", "digital_resources",
            "hostel_capacity"
        ]
        for key in relevant_keys:
            if key in aggregated:
                print(f"  {key}: {aggregated[key]}")
        
        # Calculate infrastructure score with the aggregated data
        infra_score = kpi_service.calculate_infrastructure_score(aggregated, "aicte")
        print(f"\n=== INFRASTRUCTURE SCORE ===")
        print(f"  Calculated: {infra_score}")
        print(f"  Expected: 14.34")

    except Exception as e:
        import traceback
        print(f"Error: {e}")
        traceback.print_exc()
    finally:
        close_db(db)


if __name__ == "__main__":
    main()
