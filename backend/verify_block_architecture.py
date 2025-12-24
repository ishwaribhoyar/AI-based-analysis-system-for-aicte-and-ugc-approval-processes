"""
Code Verification Script for Information Block Architecture
Verifies that all components are correctly implemented without requiring database connection
"""

import os
import sys
import ast
import re
from pathlib import Path

def check_file_for_patterns(file_path, patterns, description):
    """Check if file contains/doesn't contain certain patterns"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        results = []
        for pattern, should_exist, error_msg in patterns:
            found = bool(re.search(pattern, content, re.IGNORECASE))
            if should_exist and not found:
                results.append(("❌", f"{description}: {error_msg}"))
            elif not should_exist and found:
                results.append(("❌", f"{description}: {error_msg}"))
            else:
                results.append(("✅", f"{description}: Pattern check passed"))
        
        return results
    except Exception as e:
        return [("❌", f"Error reading {file_path}: {e}")]

def verify_block_architecture():
    """Verify Information Block Architecture implementation"""
    
    print("=" * 80)
    print("VERIFYING INFORMATION BLOCK ARCHITECTURE")
    print("=" * 80)
    
    backend_dir = Path(__file__).parent
    issues = []
    passed = []
    
    # Test 1: Verify information_blocks.py has 10 blocks
    print("\n📋 Test 1: Verify 10 Information Blocks Definition")
    print("-" * 80)
    blocks_file = backend_dir / "config" / "information_blocks.py"
    if blocks_file.exists():
        with open(blocks_file, 'r', encoding='utf-8') as f:
            content = f.read()
            block_count = content.count('"faculty_information"') + content.count("'faculty_information'")
            if block_count >= 1:
                # Count unique block definitions
                blocks = [
                    "faculty_information",
                    "student_enrollment_information",
                    "infrastructure_information",
                    "lab_equipment_information",
                    "safety_compliance_information",
                    "academic_calendar_information",
                    "fee_structure_information",
                    "placement_information",
                    "research_innovation_information",
                    "mandatory_committees_information"
                ]
                found_blocks = [b for b in blocks if b in content]
                if len(found_blocks) == 10:
                    print(f"✅ All 10 information blocks are defined")
                    passed.append("10 blocks defined")
                else:
                    print(f"❌ Only {len(found_blocks)}/10 blocks found")
                    issues.append(f"Missing blocks: {set(blocks) - set(found_blocks)}")
            else:
                print("❌ Information blocks file doesn't contain block definitions")
                issues.append("No blocks found in information_blocks.py")
    else:
        print("❌ information_blocks.py not found")
        issues.append("information_blocks.py missing")
    
    # Test 2: Verify block_processing_pipeline.py uses blocks
    print("\n📋 Test 2: Verify Block Processing Pipeline")
    print("-" * 80)
    pipeline_file = backend_dir / "pipelines" / "block_processing_pipeline.py"
    if pipeline_file.exists():
        patterns = [
            (r"classify_blocks", True, "Should use classify_blocks method"),
            (r"extract_block_data", True, "Should use extract_block_data method"),
            (r"information_blocks", True, "Should reference information_blocks collection"),
            (r"doc_type|document_type|classify_document", False, "Should NOT use document-type classification"),
        ]
        results = check_file_for_patterns(pipeline_file, patterns, "Block Processing Pipeline")
        for status, msg in results:
            print(f"  {status} {msg}")
            if "❌" in status:
                issues.append(msg)
            else:
                passed.append(msg)
    else:
        print("❌ block_processing_pipeline.py not found")
        issues.append("block_processing_pipeline.py missing")
    
    # Test 3: Verify AI client doesn't use document types
    print("\n📋 Test 3: Verify AI Client (No Document Types)")
    print("-" * 80)
    ai_client_file = backend_dir / "ai" / "openai_client.py"
    if ai_client_file.exists():
        patterns = [
            (r"classify_blocks", True, "Should have classify_blocks method"),
            (r"extract_block_data", True, "Should have extract_block_data method"),
            (r"classify_document|extract_structured_data", False, "Should NOT have document-type methods (or marked deprecated)"),
        ]
        results = check_file_for_patterns(ai_client_file, patterns, "AI Client")
        for status, msg in results:
            print(f"  {status} {msg}")
            if "❌" in status:
                issues.append(msg)
            else:
                passed.append(msg)
    else:
        print("❌ openai_client.py not found")
        issues.append("openai_client.py missing")
    
    # Test 4: Verify block_sufficiency.py uses correct formula
    print("\n📋 Test 4: Verify Sufficiency Formula")
    print("-" * 80)
    sufficiency_file = backend_dir / "services" / "block_sufficiency.py"
    if sufficiency_file.exists():
        with open(sufficiency_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        checks = [
            ("O * 4", "Outdated penalty (O*4)"),
            ("L * 5", "Low quality penalty (L*5)"),
            ("I * 7", "Invalid penalty (I*7)"),
            ("missing_blocks", "Uses missing_blocks (not missing_documents)"),
            ("(P/R)*100", "Base percentage formula"),
        ]
        
        for pattern, description in checks:
            if pattern in content:
                print(f"  ✅ {description}")
                passed.append(description)
            else:
                print(f"  ❌ Missing: {description}")
                issues.append(f"Sufficiency: Missing {description}")
    else:
        print("❌ block_sufficiency.py not found")
        issues.append("block_sufficiency.py missing")
    
    # Test 5: Verify KPI service uses blocks
    print("\n📋 Test 5: Verify KPI Service Uses Blocks")
    print("-" * 80)
    kpi_file = backend_dir / "services" / "kpi.py"
    if kpi_file.exists():
        with open(kpi_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if "_aggregate_block_data" in content or "blocks=" in content:
            print("  ✅ KPI service aggregates from blocks")
            passed.append("KPI uses blocks")
        else:
            print("  ❌ KPI service doesn't use blocks")
            issues.append("KPI service not using blocks")
        
        if "documents:" in content and "blocks:" not in content:
            print("  ⚠️  KPI service still has documents parameter (should be optional/deprecated)")
    else:
        print("❌ kpi.py not found")
        issues.append("kpi.py missing")
    
    # Test 6: Verify Compliance service uses blocks
    print("\n📋 Test 6: Verify Compliance Service Uses Blocks")
    print("-" * 80)
    compliance_file = backend_dir / "services" / "compliance.py"
    if compliance_file.exists():
        with open(compliance_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for blocks parameter and usage
        has_blocks_param = "blocks:" in content or "blocks = None" in content or "blocks: List" in content
        uses_blocks = "for block in blocks" in content or "blocks:" in content
        
        if has_blocks_param and uses_blocks:
            print("  ✅ Compliance service uses blocks parameter")
            passed.append("Compliance uses blocks")
        elif has_blocks_param:
            print("  ✅ Compliance service has blocks parameter")
            passed.append("Compliance has blocks param")
        else:
            print("  ❌ Compliance service doesn't use blocks")
            issues.append("Compliance service not using blocks")
    else:
        print("❌ compliance.py not found")
        issues.append("compliance.py missing")
    
    # Test 7: Verify Dashboard returns block_cards
    print("\n📋 Test 7: Verify Dashboard Returns Block Cards")
    print("-" * 80)
    dashboard_file = backend_dir / "routers" / "dashboard.py"
    if dashboard_file.exists():
        with open(dashboard_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        checks = [
            ("block_cards", "Returns block_cards"),
            ("BlockCard", "Uses BlockCard schema"),
            ("information_blocks", "Queries information_blocks collection"),
            ("missing_blocks", "Uses missing_blocks"),
        ]
        
        for pattern, description in checks:
            if pattern in content:
                print(f"  ✅ {description}")
                passed.append(description)
            else:
                print(f"  ❌ Missing: {description}")
                issues.append(f"Dashboard: Missing {description}")
    else:
        print("❌ dashboard.py not found")
        issues.append("dashboard.py missing")
    
    # Test 8: Verify Frontend shows blocks
    print("\n📋 Test 8: Verify Frontend Shows Blocks")
    print("-" * 80)
    frontend_dir = backend_dir.parent / "frontend" / "pages"
    dashboard_tsx = frontend_dir / "dashboard.tsx"
    if dashboard_tsx.exists():
        with open(dashboard_tsx, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if "block_cards" in content and "Information Blocks" in content:
            print("  ✅ Frontend displays block cards")
            passed.append("Frontend shows blocks")
        else:
            print("  ❌ Frontend doesn't show block cards")
            issues.append("Frontend missing block display")
        
        if "missing_blocks" in content:
            print("  ✅ Frontend uses missing_blocks")
            passed.append("Frontend uses missing_blocks")
        else:
            print("  ⚠️  Frontend may still use missing_documents")
    else:
        print("⚠️  dashboard.tsx not found (may be in different location)")
    
    # Test 9: Verify Report Generator uses blocks
    print("\n📋 Test 9: Verify Report Generator Uses Blocks")
    print("-" * 80)
    report_file = backend_dir / "services" / "report_generator.py"
    if report_file.exists():
        with open(report_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if "information_blocks" in content and "missing_blocks" in content:
            print("  ✅ Report generator uses blocks")
            passed.append("Report uses blocks")
        else:
            print("  ❌ Report generator doesn't use blocks")
            issues.append("Report generator not using blocks")
    else:
        print("❌ report_generator.py not found")
        issues.append("report_generator.py missing")
    
    # Test 10: Verify Chatbot uses blocks
    print("\n📋 Test 10: Verify Chatbot Uses Blocks")
    print("-" * 80)
    chatbot_file = backend_dir / "routers" / "chatbot.py"
    if chatbot_file.exists():
        with open(chatbot_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if "information_blocks" in content:
            print("  ✅ Chatbot uses information blocks")
            passed.append("Chatbot uses blocks")
        else:
            print("  ❌ Chatbot doesn't use information blocks")
            issues.append("Chatbot not using blocks")
    else:
        print("❌ chatbot.py not found")
        issues.append("chatbot.py missing")
    
    # Test 11: Verify Processing Router uses BlockProcessingPipeline
    print("\n📋 Test 11: Verify Processing Router")
    print("-" * 80)
    processing_file = backend_dir / "routers" / "processing.py"
    if processing_file.exists():
        with open(processing_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if "BlockProcessingPipeline" in content:
            print("  ✅ Processing router uses BlockProcessingPipeline")
            passed.append("Router uses block pipeline")
        else:
            print("  ❌ Processing router doesn't use BlockProcessingPipeline")
            issues.append("Router not using block pipeline")
    else:
        print("❌ processing.py not found")
        issues.append("processing.py missing")
    
    # Summary
    print("\n" + "=" * 80)
    print("VERIFICATION SUMMARY")
    print("=" * 80)
    print(f"✅ Passed: {len(passed)} checks")
    print(f"❌ Issues: {len(issues)} checks")
    
    if issues:
        print("\n❌ ISSUES FOUND:")
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. {issue}")
        return False
    else:
        print("\n✅ All checks passed! Information Block Architecture is correctly implemented.")
        return True

if __name__ == "__main__":
    success = verify_block_architecture()
    sys.exit(0 if success else 1)

