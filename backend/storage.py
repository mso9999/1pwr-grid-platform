"""
Shared storage module for network data
This provides a single source of truth for in-memory storage
"""

from typing import Dict, List, Any

# In-memory storage for network elements
# This will be replaced with database storage later
network_storage: Dict[str, Dict[str, List[Any]]] = {}
