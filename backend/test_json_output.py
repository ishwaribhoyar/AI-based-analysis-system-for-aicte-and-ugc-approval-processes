"""
End-to-end test using sample.pdf with JSON output for verification.
"""

import sys
import json
from pathlib import Path
from datetime import datetime, timezone
import shutil
import traceback

sys.path.insert(0, str(Path(__file__).parent))


def print_report(output):
    """Print a formatted report to the console."""
    print("\n" + "=" * 70)
    print("                    📊 DOCUMENT ANALYSIS REPORT")
    print("=" * 70)
    
    # Status
    status_icon = "✅" if output["status"] == "completed" else "❌"
    print(f"\n{status_icon} Status: {output['status'].upper()}")
    if output.get("batch_id"):
        print(f"📁 Batch ID: {output['batch_id']}")
    
    # Blocks Section
    print("\n" + "-" * 70)
    print("📦 EXTRACTED BLOCKS")
    print("-" * 70)
    print(f"{'Block Name':<40} {'Present':<10} {'Confidence':<12} {'Fields':<8}")
    print("-" * 70)
    
    for block in output.get("blocks", []):
        present_icon = "✅" if block["is_present"] else "❌"
        outdated_flag = " 📅 OUTDATED" if block.get("is_outdated") else ""
        invalid_flag = " ⚠️ INVALID" if block.get("is_invalid") else ""
        confidence = f"{block['confidence']:.1%}" if block['confidence'] else "N/A"
        
        print(f"{block['name']:<40} {present_icon:<10} {confidence:<12} {block['extracted_fields_count']:<8}{outdated_flag}{invalid_flag}")
    
    # KPIs Section
    print("\n" + "-" * 70)
    print("📈 KEY PERFORMANCE INDICATORS (KPIs)")
    print("-" * 70)
    
    for kpi in output.get("kpis", []):
        value = kpi["value"]
        if isinstance(value, (int, float)):
            value_str = f"{value:.2f}"
            # Color-code based on value
            if value >= 80:
                indicator = "🟢"
            elif value >= 50:
                indicator = "🟡"
            else:
                indicator = "🔴"
        else:
            value_str = str(value)
            indicator = "⚪"
        
        print(f"  {indicator} {kpi['name']:<30} {value_str:>10}")
    
    # Sufficiency Section
    if output.get("sufficiency"):
        suff = output["sufficiency"]
        print("\n" + "-" * 70)
        print("📋 DOCUMENT SUFFICIENCY")
        print("-" * 70)
        
        pct = suff["percentage"]
        if pct >= 80:
            suff_icon = "🟢"
        elif pct >= 50:
            suff_icon = "🟡"
        else:
            suff_icon = "🔴"
        
        print(f"  {suff_icon} Overall Sufficiency: {pct:.1f}%")
        print(f"  📊 Blocks Present: {suff['present_count']} / {suff['required_count']}")
        
        if suff.get("missing_blocks"):
            print(f"  ⚠️  Missing Blocks: {', '.join(suff['missing_blocks'])}")
        
        if suff.get("penalty_breakdown"):
            penalties = suff["penalty_breakdown"]
            if any(v > 0 for v in penalties.values()):
                print(f"  📉 Penalties: Outdated={penalties.get('outdated', 0)}, Low Quality={penalties.get('low_quality', 0)}, Invalid={penalties.get('invalid', 0)}")
    
    # Compliance Flags Section
    if output.get("compliance_flags"):
        print("\n" + "-" * 70)
        print("🚩 COMPLIANCE FLAGS")
        print("-" * 70)
        
        for flag in output["compliance_flags"]:
            severity = flag["severity"].upper()
            if severity == "HIGH" or severity == "CRITICAL":
                sev_icon = "🔴"
            elif severity == "MEDIUM":
                sev_icon = "🟡"
            else:
                sev_icon = "🟢"
            
            print(f"\n  {sev_icon} [{severity}] {flag['title']}")
            print(f"     Reason: {flag['reason']}")
            print(f"     Recommendation: {flag['recommendation']}")
    else:
        print("\n  ✅ No compliance issues detected!")
    
    # Errors Section
    if output.get("errors"):
        print("\n" + "-" * 70)
        print("❌ ERRORS")
        print("-" * 70)
        for error in output["errors"]:
            print(f"  • {error}")
    
    print("\n" + "=" * 70)
    print("                         END OF REPORT")
    print("=" * 70 + "\n")


def main():
    from config.database import get_db, close_db, Batch, File, init_db
    from config.settings import settings
    from utils.id_generator import generate_batch_id, generate_document_id
    from pipelines.block_processing_pipeline import BlockProcessingPipeline
    from routers.dashboard import get_dashboard_data

    output = {
        "status": "started",
        "blocks": [],
        "kpis": [],
        "sufficiency": None,
        "compliance_flags": [],
        "errors": []
    }

    # Ensure DB is ready
    init_db()

    repo_root = Path(__file__).parent.parent
    sample_path = repo_root / "sample.pdf"

    if not sample_path.exists() or sample_path.stat().st_size == 0:
        output["errors"].append("sample.pdf not found or empty in repo root")
        print(json.dumps(output, indent=2))
        return

    db = get_db()
    try:
        # Create batch
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
        output["batch_id"] = batch_id

        # Copy sample.pdf into uploads folder
        upload_dir = Path(settings.UPLOAD_DIR) / batch_id
        upload_dir.mkdir(parents=True, exist_ok=True)
        dest_path = upload_dir / sample_path.name
        shutil.copy2(sample_path, dest_path)

        # Create file record
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

        # Run pipeline synchronously
        pipeline = BlockProcessingPipeline()
        result = pipeline.process_batch(batch_id)
        output["pipeline_status"] = result.get('status')

        # Fetch dashboard data
        dashboard = get_dashboard_data(batch_id)
        
        # Collect block status
        for block in dashboard.block_cards:
            output["blocks"].append({
                "name": block.block_name,
                "is_present": block.is_present,
                "confidence": block.confidence,
                "extracted_fields_count": block.extracted_fields_count,
                "is_outdated": block.is_outdated,
                "is_invalid": block.is_invalid
            })
        
        # Collect KPI results
        for kpi in dashboard.kpi_cards:
            output["kpis"].append({
                "name": kpi.name,
                "value": kpi.value if kpi.value is not None else "Insufficient Data",
                "label": kpi.label
            })
        
        # Sufficiency info
        output["sufficiency"] = {
            "percentage": dashboard.sufficiency.percentage,
            "present_count": dashboard.sufficiency.present_count,
            "required_count": dashboard.sufficiency.required_count,
            "missing_blocks": dashboard.sufficiency.missing_blocks,
            "penalty_breakdown": dashboard.sufficiency.penalty_breakdown
        }
        
        # Compliance flags
        for flag in dashboard.compliance_flags:
            output["compliance_flags"].append({
                "severity": flag.severity,
                "title": flag.title,
                "reason": flag.reason,
                "recommendation": flag.recommendation
            })
        
        output["status"] = "completed"

    except Exception as e:
        output["errors"].append(str(e))
        output["status"] = "error"
        traceback.print_exc()
    finally:
        close_db(db)

    # Write output to file
    output_path = Path(__file__).parent / "test_results.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\nResults saved to: {output_path}")
    
    # Print formatted report
    print_report(output)


if __name__ == "__main__":
    main()
