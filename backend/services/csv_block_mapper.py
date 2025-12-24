"""
CSV/Excel Block Mapper.
Directly maps CSV/Excel structured data to AICTE/UGC information blocks.
Bypasses LLM extraction for structured data sources.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from utils.parse_numeric import parse_numeric
from utils.parse_year import parse_year
import pandas as pd

logger = logging.getLogger(__name__)


# Block type detection rules based on column names
BLOCK_DETECTION_RULES = {
    "faculty_information": {
        "keywords": ["faculty", "professor", "phd", "assistant_professor", "associate_professor", 
                     "teaching_staff", "total_faculty", "faculty_count", "lecturer"],
        "required_fields": ["faculty_count", "total_faculty"],
        "optional_fields": ["phd_count", "assistant_professor", "associate_professor", "professor"]
    },
    "student_enrollment_information": {
        "keywords": ["total_students", "student_count", "male", "female", "intake", "admitted",
                     "enrollment", "enrolled", "students", "ug_students", "pg_students"],
        "required_fields": ["total_students", "student_count"],
        "optional_fields": ["male_students", "female_students", "ug_enrollment", "pg_enrollment"]
    },
    "infrastructure_information": {
        "keywords": ["built_up_area", "area", "classrooms", "library_area", "labs", "computers",
                     "infrastructure", "building", "campus_area", "total_area", "classroom_count"],
        "required_fields": ["built_up_area", "classrooms"],
        "optional_fields": ["library_area", "lab_area", "digital_resources", "hostel_capacity"]
    },
    "lab_information": {
        "keywords": ["lab", "laboratory", "equipment", "machine", "capacity", "total_labs",
                     "computer_labs", "science_labs", "engineering_labs"],
        "required_fields": ["total_labs", "lab_count"],
        "optional_fields": ["computer_labs", "science_labs", "engineering_labs", "lab_equipment"]
    },
    "safety_compliance_information": {
        "keywords": ["fire_noc", "building_stability", "electrical_safety", "safety", "noc",
                     "fire_certificate", "stability_certificate", "safety_certificate"],
        "required_fields": [],
        "optional_fields": ["fire_noc", "building_stability_certificate", "electrical_safety_certificate"]
    },
    "academic_calendar_information": {
        "keywords": ["academic_year", "start_date", "end_date", "calendar", "semester",
                     "academic_year_start", "academic_year_end"],
        "required_fields": ["academic_year"],
        "optional_fields": ["academic_year_start", "academic_year_end", "semester_dates"]
    },
    "fee_structure_information": {
        "keywords": ["fee", "tuition", "hostel_fee", "transport_fee", "annual_fee", "semester_fee",
                     "tuition_fee", "hostel", "transport"],
        "required_fields": [],
        "optional_fields": ["annual_fee", "hostel_fee", "transport_fee", "tuition_fee"]
    },
    "placement_information": {
        "keywords": ["placed", "eligible", "highest_salary", "avg_salary", "placement", "package",
                     "students_placed", "placement_rate", "average_package", "highest_package"],
        "required_fields": [],
        "optional_fields": ["students_placed", "students_eligible", "placement_rate", "average_package", "highest_package"]
    },
    "research_publications_information": {
        "keywords": ["publications", "patents", "funded_projects", "research", "paper", "journal",
                     "publication_count", "patent_count", "projects"],
        "required_fields": [],
        "optional_fields": ["publications", "patents", "funded_projects", "publication_count"]
    },
    "governance_committees_information": {
        "keywords": ["iqac", "anti_ragging", "icc", "grievance", "committee", "governance",
                     "internal_quality", "women_cell", "sc_st_cell"],
        "required_fields": [],
        "optional_fields": ["iqac", "anti_ragging_committee", "icc", "grievance_committee"]
    }
}


def detect_block_type_from_columns(columns: List[str]) -> Optional[str]:
    """
    Detect block type based on column names.
    Returns the block type with the highest match score.
    """
    if not columns:
        return None
    
    columns_lower = [str(c).lower().strip() for c in columns]
    best_match = None
    best_score = 0
    
    for block_type, rules in BLOCK_DETECTION_RULES.items():
        keywords = rules["keywords"]
        score = 0
        
        for keyword in keywords:
            for col in columns_lower:
                if keyword in col or col in keyword:
                    score += 1
                    break
        
        if score > best_score:
            best_score = score
            best_match = block_type
    
    # Require at least 1 keyword match (more lenient)
    if best_score >= 1:
        return best_match
    
    return None


def normalize_column_name(col: str) -> str:
    """
    Normalize column name to match AICTE/UGC schema field names.
    """
    col_lower = str(col).lower().strip()
    
    # Common mappings
    mappings = {
        "faculty": "faculty_count",
        "total faculty": "faculty_count",
        "no of faculty": "faculty_count",
        "teaching staff": "faculty_count",
        "students": "total_students",
        "total students": "total_students",
        "student count": "total_students",
        "enrollment": "total_students",
        "area": "built_up_area",
        "built up area": "built_up_area",
        "total area": "built_up_area",
        "classroom": "classrooms",
        "no of classrooms": "classrooms",
        "classroom count": "classrooms",
        "labs": "total_labs",
        "laboratory": "total_labs",
        "lab count": "total_labs",
        "placed": "students_placed",
        "students placed": "students_placed",
        "eligible": "students_eligible",
        "students eligible": "students_eligible",
        "avg salary": "average_package",
        "average salary": "average_package",
        "highest salary": "highest_package",
        "max salary": "highest_package",
        "publication": "publications",
        "publication count": "publications",
        "patent": "patents",
        "patent count": "patents",
        "academic year": "academic_year",
        "year": "academic_year",
    }
    
    # Direct mapping
    if col_lower in mappings:
        return mappings[col_lower]
    
    # Replace spaces and special chars with underscores
    normalized = col_lower.replace(" ", "_").replace("-", "_").replace(".", "_")
    
    return normalized


def map_row_to_block_data(row: Dict[str, Any], block_type: str, columns: List[str]) -> Dict[str, Any]:
    """
    Map a CSV/Excel row to block data structure.
    """
    block_data = {}
    rules = BLOCK_DETECTION_RULES.get(block_type, {})
    
    # Normalize column names and map values
    for col in columns:
        normalized_col = normalize_column_name(col)
        value = row.get(col)
        
        if value is None or (isinstance(value, str) and value.strip() == ""):
            continue
        
        # Try to parse numeric values
        if isinstance(value, (int, float)):
            block_data[normalized_col] = value
            block_data[f"{normalized_col}_num"] = float(value)
        elif isinstance(value, str):
            # Try parsing as number
            parsed_num = parse_numeric(value)
            if parsed_num is not None:
                block_data[normalized_col] = value  # Keep raw value
                block_data[f"{normalized_col}_num"] = parsed_num
            else:
                # Check if it's a year
                parsed_year = parse_year(value)
                if parsed_year:
                    block_data[normalized_col] = value
                    block_data["last_updated_year"] = parsed_year
                else:
                    # Keep as string
                    block_data[normalized_col] = value
    
    # Extract and set academic_year if found in any field
    if "academic_year" not in block_data:
        for key, value in block_data.items():
            if value and isinstance(value, str):
                # Check if field name suggests it's a year
                if any(term in key.lower() for term in ['year', 'session', 'academic']):
                    parsed_year = parse_year(str(value))
                    if parsed_year:
                        # Format as academic year (e.g., 2023-24)
                        if parsed_year >= 2000:
                            academic_year = f"{parsed_year}-{str(parsed_year + 1)[-2:]}"
                        else:
                            academic_year = str(parsed_year)
                        block_data["academic_year"] = academic_year
                        block_data["year"] = parsed_year
                        break
    
    # Block-specific mappings
    if block_type == "faculty_information":
        # Map common variations
        if "faculty_count" not in block_data:
            for key in ["faculty", "total_faculty", "teaching_staff"]:
                if key in block_data:
                    block_data["faculty_count"] = block_data[key]
                    block_data["faculty_count_num"] = block_data.get(f"{key}_num", block_data.get(key))
                    break
    
    elif block_type == "student_enrollment_information":
        # Map common variations
        if "total_students" not in block_data:
            for key in ["students", "student_count", "enrollment", "total_enrollment"]:
                if key in block_data:
                    block_data["total_students"] = block_data[key]
                    block_data["total_students_num"] = block_data.get(f"{key}_num", block_data.get(key))
                    break
        
        # Calculate total from male + female if available
        if "total_students" not in block_data or block_data.get("total_students_num") is None:
            male = block_data.get("male_students_num") or block_data.get("male_num")
            female = block_data.get("female_students_num") or block_data.get("female_num")
            if male is not None and female is not None:
                total = male + female
                block_data["total_students"] = str(total)
                block_data["total_students_num"] = total
    
    elif block_type == "infrastructure_information":
        # Map area fields with proper unit conversion
        if "built_up_area" not in block_data:
            for key in ["area", "total_area", "campus_area", "building_area"]:
                if key in block_data:
                    raw_value = block_data[key]
                    block_data["built_up_area"] = raw_value
                    # Parse and convert to sqm (parse_numeric handles unit conversion)
                    parsed_sqm = parse_numeric(raw_value)
                    if parsed_sqm is not None:
                        block_data["built_up_area_num"] = parsed_sqm
                        block_data["built_up_area_sqm_num"] = parsed_sqm  # Already in sqm after conversion
                    break
        
        # Map classroom fields
        if "classrooms" not in block_data:
            for key in ["classroom", "classroom_count", "no_of_classrooms"]:
                if key in block_data:
                    block_data["classrooms"] = block_data[key]
                    block_data["classrooms_num"] = block_data.get(f"{key}_num")
                    break
    
    elif block_type == "placement_information":
        # Map placement fields
        if "students_placed" not in block_data:
            for key in ["placed", "placement_count"]:
                if key in block_data:
                    block_data["students_placed"] = block_data[key]
                    block_data["students_placed_num"] = block_data.get(f"{key}_num")
                    break
        
        if "students_eligible" not in block_data:
            for key in ["eligible", "eligible_students"]:
                if key in block_data:
                    block_data["students_eligible"] = block_data[key]
                    block_data["students_eligible_num"] = block_data.get(f"{key}_num")
                    break
        
        # Calculate placement rate if both available
        placed = block_data.get("students_placed_num")
        eligible = block_data.get("students_eligible_num")
        if placed is not None and eligible is not None and eligible > 0:
            rate = (placed / eligible) * 100
            block_data["placement_rate"] = f"{rate:.2f}%"
            block_data["placement_rate_num"] = rate
    
    elif block_type == "lab_information":
        # Map lab fields
        if "total_labs" not in block_data:
            for key in ["labs", "lab_count", "laboratory"]:
                if key in block_data:
                    block_data["total_labs"] = block_data[key]
                    block_data["total_labs_num"] = block_data.get(f"{key}_num")
                    break
    
    return block_data


def map_csv_file(file_path: str, mode: str = "aicte") -> List[Dict[str, Any]]:
    """
    Map a CSV file to information blocks.
    
    Returns:
        List of block dictionaries: [
            {
                "block_type": "...",
                "data": {...},
                "confidence": 0.95,
                "source": "csv"
            }
        ]
    """
    blocks = []
    
    try:
        # Read CSV with multiple encoding attempts
        df = None
        for encoding in ['utf-8', 'latin-1', 'cp1252']:
            try:
                df = pd.read_csv(file_path, encoding=encoding)
                break
            except:
                continue
        
        if df is None:
            df = pd.read_csv(file_path, encoding='utf-8', errors='ignore')
        
        if df.empty:
            logger.warning(f"CSV file {file_path} is empty")
            return blocks
        
        columns = list(df.columns)
        logger.info(f"CSV columns: {columns}")
        
        # Detect block type from columns
        block_type = detect_block_type_from_columns(columns)
        
        if not block_type:
            # Fallback: Use generic_data block and extract all columns
            logger.info(f"No specific block type detected, using generic_data for columns: {columns}")
            block_type = "generic_data"
        
        logger.info(f"Detected block type: {block_type} for CSV file")
        
        # Check if CSV has year-based structure (rows per year)
        year_column = None
        for col in columns:
            col_lower = str(col).lower().strip()
            if any(term in col_lower for term in ['year', 'academic_year', 'session', 'academic']):
                # Check if this column contains year values
                try:
                    sample_values = df[col].dropna().head(5).astype(str)
                    if any(parse_year(str(v)) for v in sample_values):
                        year_column = col
                        break
                except (KeyError, AttributeError, TypeError):
                    # Column might not exist or have issues, skip it
                    continue
        
        # If year column found, extract year from first row or use latest
        if year_column:
            year_values = df[year_column].dropna()
            if not year_values.empty:
                # Try to parse year from first non-null value
                first_year_val = str(year_values.iloc[0])
                parsed_year = parse_year(first_year_val)
                if parsed_year:
                    academic_year = f"{parsed_year}-{str(parsed_year + 1)[-2:]}"
                    aggregated_data = {"academic_year": academic_year, "year": parsed_year}
                else:
                    aggregated_data = {}
            else:
                aggregated_data = {}
        else:
            aggregated_data = {}
        
        # Aggregate all rows into a single block
        for idx, row in df.iterrows():
            row_dict = row.to_dict()
            row_data = map_row_to_block_data(row_dict, block_type, columns)
            
            # Merge row data into aggregated data (prefer non-null values)
            for key, value in row_data.items():
                if key not in aggregated_data or aggregated_data[key] is None:
                    aggregated_data[key] = value
                elif isinstance(value, (int, float)) and isinstance(aggregated_data[key], (int, float)):
                    # For numeric values, use sum or max depending on field
                    if "count" in key or "total" in key:
                        aggregated_data[key] = max(aggregated_data[key], value)
                    else:
                        aggregated_data[key] = value
        
        # Calculate confidence based on data completeness
        rules = BLOCK_DETECTION_RULES.get(block_type, {})
        required_fields = rules.get("required_fields", [])
        optional_fields = rules.get("optional_fields", [])
        
        filled_required = sum(1 for field in required_fields if field in aggregated_data or f"{field}_num" in aggregated_data)
        filled_optional = sum(1 for field in optional_fields if field in aggregated_data or f"{field}_num" in aggregated_data)
        
        total_fields = len(required_fields) + len(optional_fields)
        filled_fields = filled_required + filled_optional
        
        if total_fields > 0:
            completeness = filled_fields / total_fields
            confidence = 0.85 + (completeness * 0.13)  # 0.85 to 0.98
        else:
            confidence = 0.90
        
        # If required fields are present, boost confidence
        if required_fields and filled_required == len(required_fields):
            confidence = min(0.98, confidence + 0.05)
        
        blocks.append({
            "block_type": block_type,
            "data": aggregated_data,
            "confidence": confidence,
            "source": "csv",
            "file_path": file_path
        })
        
        logger.info(f"✅ Mapped CSV to {block_type} block (confidence: {confidence:.2f})")
        
    except Exception as e:
        logger.error(f"Error mapping CSV file {file_path}: {e}")
        import traceback
        logger.error(traceback.format_exc())
    
    return blocks


def map_excel_file(file_path: str, mode: str = "aicte") -> List[Dict[str, Any]]:
    """
    Map an Excel file to information blocks.
    Processes each sheet and detects block types.
    
    Returns:
        List of block dictionaries
    """
    blocks = []
    excel_file = None
    
    try:
        excel_file = pd.ExcelFile(file_path)
        sheet_names = excel_file.sheet_names
        
        logger.info(f"Excel file has {len(sheet_names)} sheets: {sheet_names}")
        
        for sheet_name in sheet_names:
            try:
                df = pd.read_excel(excel_file, sheet_name=sheet_name)
                
                if df.empty:
                    continue
                
                columns = list(df.columns)
                block_type = detect_block_type_from_columns(columns)
                
                if not block_type:
                    # Fallback: Use generic_data block for sheets without detected type
                    logger.info(f"No specific block type for sheet '{sheet_name}', using generic_data")
                    block_type = "generic_data"
                
                # Aggregate rows from this sheet
                aggregated_data = {}
                
                for idx, row in df.iterrows():
                    row_dict = row.to_dict()
                    row_data = map_row_to_block_data(row_dict, block_type, columns)
                    
                    for key, value in row_data.items():
                        if key not in aggregated_data or aggregated_data[key] is None:
                            aggregated_data[key] = value
                        elif isinstance(value, (int, float)) and isinstance(aggregated_data[key], (int, float)):
                            if "count" in key or "total" in key:
                                aggregated_data[key] = max(aggregated_data[key], value)
                            else:
                                aggregated_data[key] = value
                
                # Calculate confidence
                rules = BLOCK_DETECTION_RULES.get(block_type, {})
                required_fields = rules.get("required_fields", [])
                optional_fields = rules.get("optional_fields", [])
                
                filled_required = sum(1 for field in required_fields if field in aggregated_data or f"{field}_num" in aggregated_data)
                filled_optional = sum(1 for field in optional_fields if field in aggregated_data or f"{field}_num" in aggregated_data)
                
                total_fields = len(required_fields) + len(optional_fields)
                filled_fields = filled_required + filled_optional
                
                if total_fields > 0:
                    completeness = filled_fields / total_fields
                    confidence = 0.85 + (completeness * 0.13)
                else:
                    confidence = 0.90
                
                if required_fields and filled_required == len(required_fields):
                    confidence = min(0.98, confidence + 0.05)
                
                blocks.append({
                    "block_type": block_type,
                    "data": aggregated_data,
                    "confidence": confidence,
                    "source": "excel",
                    "sheet": sheet_name,
                    "file_path": file_path
                })
                
                logger.info(f"✅ Mapped Excel sheet '{sheet_name}' to {block_type} block (confidence: {confidence:.2f})")
                
            except Exception as e:
                logger.warning(f"Error processing sheet '{sheet_name}': {e}")
                continue
        
    except Exception as e:
        logger.error(f"Error mapping Excel file {file_path}: {e}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        # Ensure ExcelFile is closed to release file handle
        if excel_file is not None:
            try:
                excel_file.close()
            except:
                pass
    
    return blocks


def map_file(file_path: str, file_type: str, mode: str = "aicte") -> List[Dict[str, Any]]:
    """
    Map a file (CSV or Excel) to information blocks.
    
    Args:
        file_path: Path to the file
        file_type: 'csv', 'xlsx', or 'xls'
        mode: 'aicte' or 'ugc'
    
    Returns:
        List of block dictionaries
    """
    if file_type == "csv":
        return map_csv_file(file_path, mode)
    elif file_type in ["xlsx", "xls"]:
        return map_excel_file(file_path, mode)
    else:
        logger.warning(f"Unsupported file type for mapping: {file_type}")
        return []

