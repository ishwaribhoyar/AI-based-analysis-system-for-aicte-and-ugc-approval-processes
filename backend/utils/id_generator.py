"""
ID generation utilities
"""

import uuid
from datetime import datetime

def generate_batch_id(mode: str) -> str:
    """Generate unique batch ID"""
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    return f"batch_{mode}_{timestamp}_{unique_id}"

def generate_block_id() -> str:
    """Generate unique block ID"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f"block_{timestamp}_{random_suffix}"

def generate_document_id() -> str:
    """Generate unique document ID"""
    return f"doc_{uuid.uuid4().hex[:12]}"

def generate_audit_id() -> str:
    """Generate unique audit log ID"""
    return f"audit_{uuid.uuid4().hex[:12]}"

def generate_block_id() -> str:
    """Generate unique block ID"""
    return f"block_{uuid.uuid4().hex[:12]}"

