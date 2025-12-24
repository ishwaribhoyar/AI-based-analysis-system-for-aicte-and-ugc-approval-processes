"""
Block-Based Sufficiency Calculation
Formula: base_pct = (P/R)*100, penalty = O*4 + L*5 + I*7
Uses parse_numeric for robust numeric parsing
"""

from typing import Dict, Any, List
from config.information_blocks import get_information_blocks
from utils.parse_numeric import parse_numeric

class BlockSufficiencyService:
    """Calculate sufficiency based on information blocks"""
    
    def calculate_sufficiency(
        self,
        mode: str,
        blocks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculate block-based sufficiency
        Formula: base_pct = (P/R)*100
                 penalty = O*4 + L*5 + I*7
                 penalty = min(penalty, 50)
                 sufficiency = max(0, base_pct - penalty)
        
        Where:
        - P = number of blocks with valid data
        - R = 10 (total required blocks)
        - O = outdated blocks
        - L = low-quality blocks
        - I = invalid blocks
        """
        # Note: new_university flag not available here, but sufficiency calculation
        # works with whatever blocks are present, so this is fine
        required_blocks = get_information_blocks(mode, new_university=False)  # Default to renewal
        R = len(required_blocks)  # Always 10 (for both AICTE and UGC)
        
        # Group blocks by type
        blocks_by_type = {}
        for block in blocks:
            block_type = block.get("block_type")
            if block_type:
                if block_type not in blocks_by_type:
                    blocks_by_type[block_type] = []
                blocks_by_type[block_type].append(block)
        
        # Count present blocks (P) - at least one valid block per type with extracted data
        present_block_types = set()
        for block_type, block_list in blocks_by_type.items():
            # Check if any block of this type is valid (not invalid) AND has extracted data
            has_valid = any(
                not block.get("is_invalid", False) and 
                block.get("extracted_data") and 
                len(block.get("extracted_data", {})) > 0
                for block in block_list
            )
            if has_valid and block_type in required_blocks:
                present_block_types.add(block_type)
        
        P = len(present_block_types)
        
        # Count penalties
        O = sum(1 for block in blocks if block.get("is_outdated", False))
        L = sum(1 for block in blocks if block.get("is_low_quality", False))
        I = sum(1 for block in blocks if block.get("is_invalid", False))
        
        # Calculate base percentage
        base_pct = (P / R * 100) if R > 0 else 0
        
        # Calculate penalty
        penalty = O * 4 + L * 5 + I * 7
        penalty = min(penalty, 50)
        
        # Final sufficiency
        sufficiency = max(0, base_pct - penalty)
        
        # Missing blocks
        missing_blocks = [bt for bt in required_blocks if bt not in present_block_types]
        
        # Determine color
        if sufficiency >= 80:
            color = "green"
        elif sufficiency >= 60:
            color = "yellow"
        else:
            color = "red"
        
        return {
            "percentage": round(sufficiency, 2),
            "present_count": P,
            "required_count": R,
            "missing_blocks": missing_blocks,
            "penalty_breakdown": {
                "outdated": O,
                "low_quality": L,
                "invalid": I
            },
            "penalty_points": penalty,
            "color": color,
            "base_percentage": round(base_pct, 2)
        }
