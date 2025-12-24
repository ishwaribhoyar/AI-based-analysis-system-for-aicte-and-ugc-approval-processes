"""Debug why blocks are flagged as outdated."""
import sys
import json
from pathlib import Path
from datetime import datetime, timezone
import shutil

sys.path.insert(0, str(Path(__file__).parent))


def main():
    from config.database import get_db, close_db, Batch, Block, File, init_db
    from config.settings import settings
    from utils.id_generator import generate_batch_id, generate_document_id
    from pipelines.block_processing_pipeline import BlockProcessingPipeline
    from services.block_quality import BlockQualityService

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
        
        # Get blocks and check their year data
        blocks = db.query(Block).filter(Block.batch_id == batch_id).all()
        
        quality_service = BlockQualityService()
        current_year = datetime.now().year
        
        print(f"\n=== OUTDATED BLOCK ANALYSIS ===")
        print(f"Current year: {current_year}")
        print()
        
        for block in blocks:
            block_data = block.data or {}
            
            # Check for year fields
            year_fields = {
                "parsed_year": block_data.get("parsed_year"),
                "last_updated_year": block_data.get("last_updated_year"),
                "year": block_data.get("year"),
                "academic_year": block_data.get("academic_year"),
                "academic_year_start": block_data.get("academic_year_start"),
                "academic_year_end": block_data.get("academic_year_end"),
            }
            
            # Check all values for years
            all_years = []
            for key, value in block_data.items():
                if isinstance(value, (int, float)) and 1900 <= value <= 2100:
                    all_years.append((key, int(value)))
                elif isinstance(value, str) and ("20" in value or "19" in value):
                    from utils.parse_year import parse_year
                    parsed = parse_year(value)
                    if parsed:
                        all_years.append((key, parsed))
            
            if block.is_outdated:
                print(f"OUTDATED: {block.block_type}")
                print(f"  Year fields: {year_fields}")
                print(f"  Years found in data: {all_years[:5]}")  # Show first 5
                print()

    except Exception as e:
        import traceback
        print(f"Error: {e}")
        traceback.print_exc()
    finally:
        close_db(db)


if __name__ == "__main__":
    main()
