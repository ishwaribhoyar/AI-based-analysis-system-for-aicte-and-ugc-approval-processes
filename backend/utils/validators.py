"""
Validation utilities
"""

from typing import Dict, Any, List, Optional, Tuple
import json

def validate_json_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """Validate data against JSON schema (simplified)"""
    try:
        # Basic validation - in production use jsonschema library
        for key, value_type in schema.items():
            if key not in data:
                return False, f"Missing required field: {key}"
            if not isinstance(data[key], value_type):
                return False, f"Invalid type for {key}: expected {value_type}"
        return True, None
    except Exception as e:
        return False, str(e)

def sanitize_json_string(json_str: str) -> str:
    """Remove markdown code blocks and clean JSON string"""
    json_str = json_str.strip()
    if json_str.startswith("```json"):
        json_str = json_str[7:]
    elif json_str.startswith("```"):
        json_str = json_str[3:]
    if json_str.endswith("```"):
        json_str = json_str[:-3]
    return json_str.strip()

def parse_json_safely(json_str: str) -> Dict[str, Any]:
    """Safely parse JSON with error handling"""
    try:
        cleaned = sanitize_json_string(json_str)
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {e}")

