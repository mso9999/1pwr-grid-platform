"""
Shared storage module for network data
"""

from typing import Dict, List, Any

# Shared in-memory storage for network data
network_storage: Dict[str, Dict[str, List[Any]]] = {}

# Shared storage for voltage calculation results  
voltage_storage: Dict[str, Any] = {}

# Shared storage for as-built snapshots
as_built_storage: Dict[str, List[Any]] = {}
