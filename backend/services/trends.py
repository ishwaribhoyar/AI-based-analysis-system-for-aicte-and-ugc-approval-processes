"""
Trend analysis service
Extracts trends ONLY from Docling tables (structured_table_text or table_markdown)
NO interpolation, NO prediction
"""

from typing import List, Dict, Any, Optional
import re
import logging

logger = logging.getLogger(__name__)

class TrendService:
    def __init__(self):
        pass
    
    def extract_trends_from_docling_tables(
        self,
        files: List,  # File objects from SQLite
        tables_text: str,
        mode: str
    ) -> Dict[str, Any]:
        """
        Extract trends from tables (PDF, Excel, CSV, DOCX)
        Looks for multi-year tables (e.g., NIRF 2022-2024, Placement 3-year)
        Returns: {
            has_trend_data: bool,
            trend_data: [{year, kpi_name, value}],
            message: str (if no data)
        }
        """
        try:
            # Also extract from Excel/CSV files directly if tables_text is empty
            if not tables_text or len(tables_text.strip()) < 50:
                # Try to extract from Excel/CSV files
                from services.document_parser import parse_document, detect_file_type
                excel_csv_tables = []
                
                for file in files:
                    file_type = detect_file_type(file.filepath)
                    if file_type in ['xlsx', 'xls', 'csv']:
                        parsed = parse_document(file.filepath)
                        parsed_tables = parsed.get("tables", [])
                        for table in parsed_tables:
                            if isinstance(table, dict) and "data" in table:
                                # Convert table to text format for trend extraction
                                sheet_name = table.get("sheet", "Table")
                                columns = table.get("columns", [])
                                table_data = table.get("data", [])
                                
                                table_text = f"=== {sheet_name} ===\n"
                                if columns:
                                    table_text += "| " + " | ".join(str(c) for c in columns) + " |\n"
                                    for row in table_data[:200]:  # Up to 200 rows
                                        if isinstance(row, dict):
                                            row_values = [str(row.get(col, "")) for col in columns]
                                            table_text += "| " + " | ".join(row_values) + " |\n"
                                excel_csv_tables.append(table_text)
                
                if excel_csv_tables:
                    tables_text = "\n\n".join(excel_csv_tables)
                else:
                    return {
                        "has_trend_data": False,
                        "trend_data": [],
                        "message": "No tables extracted from documents"
                    }
            
            # Extract trend data from table text
            trend_data = self._extract_trend_tables(tables_text, mode)
            
            # Require at least 2 data points for valid trends
            if trend_data and len(trend_data) >= 2:
                # Group by year to count unique years
                years = set()
                for point in trend_data:
                    if point.get("year"):
                        years.add(str(point["year"]))
                
                if len(years) >= 2:
                    return {
                        "has_trend_data": True,
                        "insufficient_data": False,
                        "trend_data": trend_data,
                        "message": None
                    }
            
            # Insufficient data
            return {
                "has_trend_data": False,
                "insufficient_data": True,
                "trend_data": trend_data if trend_data else [],
                "message": f"Insufficient data: found {len(trend_data) if trend_data else 0} data point(s), need at least 2 years"
            }
                
        except Exception as e:
            logger.error(f"Trend extraction error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                "has_trend_data": False,
                "trend_data": [],
                "message": f"Error extracting trends: {str(e)}"
            }
    
    def _extract_trend_tables(self, tables_text: str, mode: str) -> List[Dict[str, Any]]:
        """
        Extract trend data from Docling table text
        Looks for tables with years and numeric values
        NO interpolation, NO prediction
        """
        trend_data = []
        
        # Split tables_text into individual tables (separated by blank lines or headers)
        # Look for patterns like:
        # - Year columns (2020, 2021, 2022, etc.)
        # - KPI names (FSR, Placement Rate, Publications, etc.)
        # - Numeric values
        
        # Pattern 1: Table with year columns
        # Example: "Year | Intake | Placements\n2022 | 100 | 85\n2023 | 120 | 95"
        year_pattern = r'\b(20\d{2}|19\d{2})\b'
        
        # Find all year mentions
        years_found = set(re.findall(year_pattern, tables_text))
        
        if not years_found:
            return []
        
        # Look for table structures with years
        # Split by common table delimiters
        lines = tables_text.split('\n')
        
        # Find lines containing years
        year_lines = []
        for i, line in enumerate(lines):
            if re.search(year_pattern, line):
                year_lines.append((i, line))
        
        if not year_lines:
            return []
        
        # Extract data from lines around year lines
        for idx, year_line in year_lines:
            # Look for numeric values in the same line or nearby lines
            # Extract year
            year_match = re.search(year_pattern, year_line)
            if not year_match:
                continue
            
            year = year_match.group(1)
            
            # Extract numbers from the same line
            numbers = re.findall(r'\d+\.?\d*', year_line)
            
            # Try to identify KPI name from context (previous lines or table headers)
            # Look backwards for header row
            kpi_name = None
            for i in range(max(0, idx - 3), idx):
                header_line = lines[i] if i < len(lines) else ""
                # Check for common KPI keywords
                if any(kw in header_line.lower() for kw in ['fsr', 'faculty', 'student', 'ratio']):
                    kpi_name = "FSR Score"
                elif any(kw in header_line.lower() for kw in ['placement', 'placed']):
                    kpi_name = "Placement Index"
                elif any(kw in header_line.lower() for kw in ['publication', 'research']):
                    kpi_name = "Research Index"
                elif any(kw in header_line.lower() for kw in ['infrastructure', 'area', 'built']):
                    kpi_name = "Infrastructure Score"
                elif any(kw in header_line.lower() for kw in ['lab', 'laboratory']):
                    kpi_name = "Lab Compliance Index"
                elif any(kw in header_line.lower() for kw in ['intake', 'enrollment']):
                    kpi_name = "Student Enrollment"
                elif any(kw in header_line.lower() for kw in ['fee', 'tuition']):
                    kpi_name = "Fee Structure"
            
            # If no KPI name found, use generic
            if not kpi_name:
                kpi_name = "Metric"
            
            # Extract numeric values (skip the year itself)
            for num_str in numbers:
                try:
                    num_val = float(num_str)
                    # Skip if it's the year itself
                    if abs(num_val - float(year)) < 100:  # Year is close to the number
                        continue
                    # Only add if it's a reasonable value
                    if 0 <= num_val <= 1000000:  # Reasonable range
                        trend_data.append({
                            "year": year,
                            "kpi_name": kpi_name,
                            "value": num_val
                        })
                except (ValueError, TypeError):
                    continue
        
        # Deduplicate (keep first occurrence)
        seen = set()
        unique_trend_data = []
        for item in trend_data:
            key = (item["year"], item["kpi_name"], item["value"])
            if key not in seen:
                seen.add(key)
                unique_trend_data.append(item)
        
        return unique_trend_data
