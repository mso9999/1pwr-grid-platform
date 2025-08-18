"""
As-built data models for tracking actual field construction
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

class AsBuiltStatus(str, Enum):
    """Status of as-built vs planned comparison"""
    PLANNED = "planned"
    MODIFIED = "modified"
    ADDED = "added"
    REMOVED = "removed"
    AS_PLANNED = "as_planned"

class AsBuiltPole(BaseModel):
    """As-built pole model with field measurements"""
    pole_id: str
    latitude: float
    longitude: float
    pole_type: str = "LV"
    pole_class: Optional[str] = None
    angle_class: Optional[str] = None
    height: Optional[float] = Field(None, description="Actual pole height in meters")
    material: Optional[str] = Field(None, description="Pole material (wood/steel/concrete)")
    status: AsBuiltStatus = AsBuiltStatus.AS_PLANNED
    deviation_distance: Optional[float] = Field(None, description="Distance from planned location in meters")
    installation_date: Optional[datetime] = None
    installed_by: Optional[str] = None
    notes: Optional[str] = None
    st_code_1: Optional[int] = Field(None, ge=0, le=9)
    st_code_2: Optional[str] = None

class AsBuiltConnection(BaseModel):
    """As-built customer connection model"""
    connection_id: str
    survey_id: str
    latitude: float
    longitude: float
    meter_number: Optional[str] = None
    meter_installed: bool = False
    meter_commissioned: bool = False
    status: AsBuiltStatus = AsBuiltStatus.AS_PLANNED
    deviation_distance: Optional[float] = None
    installation_date: Optional[datetime] = None
    installed_by: Optional[str] = None
    notes: Optional[str] = None
    st_code_3: Optional[int] = Field(None, ge=0, le=10)

class AsBuiltConductor(BaseModel):
    """As-built conductor model with actual measurements"""
    conductor_id: str
    from_pole: str
    to_pole: str
    conductor_type: str = Field(..., pattern="^(MV|LV|DROP)$")
    conductor_spec: Optional[str] = None
    actual_length: Optional[float] = Field(None, description="Measured length in meters")
    planned_length: Optional[float] = Field(None, description="Planned length in meters")
    sag: Optional[float] = Field(None, description="Measured sag in meters")
    tension: Optional[float] = Field(None, description="Tension in Newtons")
    status: AsBuiltStatus = AsBuiltStatus.AS_PLANNED
    stringing_date: Optional[datetime] = None
    strung_by: Optional[str] = None
    notes: Optional[str] = None
    st_code_4: Optional[int] = Field(None, ge=0, le=5)

class AsBuiltTransformer(BaseModel):
    """As-built transformer model"""
    transformer_id: str
    pole_id: str
    capacity_kva: float
    serial_number: Optional[str] = None
    manufacturer: Optional[str] = None
    installation_date: Optional[datetime] = None
    commissioned_date: Optional[datetime] = None
    status: AsBuiltStatus = AsBuiltStatus.AS_PLANNED
    notes: Optional[str] = None

class AsBuiltSnapshot(BaseModel):
    """Complete as-built snapshot at a point in time"""
    site: str
    snapshot_date: datetime
    created_by: str
    poles: List[AsBuiltPole] = []
    connections: List[AsBuiltConnection] = []
    conductors: List[AsBuiltConductor] = []
    transformers: List[AsBuiltTransformer] = []
    metadata: Dict[str, Any] = {}
    
class AsBuiltComparison(BaseModel):
    """Comparison between planned and as-built"""
    site: str
    comparison_date: datetime
    
    # Summary statistics
    poles_planned: int = 0
    poles_built: int = 0
    poles_modified: int = 0
    poles_added: int = 0
    poles_removed: int = 0
    
    conductors_planned: int = 0
    conductors_built: int = 0
    conductors_modified: int = 0
    conductors_added: int = 0
    conductors_removed: int = 0
    
    connections_planned: int = 0
    connections_built: int = 0
    connections_modified: int = 0
    connections_added: int = 0
    connections_removed: int = 0
    
    # Length statistics
    planned_length_km: float = 0
    built_length_km: float = 0
    
    # Detailed differences
    pole_differences: List[Dict[str, Any]] = []
    conductor_differences: List[Dict[str, Any]] = []
    connection_differences: List[Dict[str, Any]] = []
    
    # Progress percentage
    overall_progress: float = 0
    pole_progress: float = 0
    conductor_progress: float = 0
    connection_progress: float = 0
