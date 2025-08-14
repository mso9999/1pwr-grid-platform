"""
Enhanced Data Model for 1PWR Grid Platform
Distinguishes between network infrastructure and customer connections
"""

from typing import Dict, List, Optional, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

class ConnectionType(Enum):
    """Types of connections in the network"""
    HOUSEHOLD_1 = "HH1"
    HOUSEHOLD_2 = "HH2"
    SME = "SME"
    INSTITUTIONAL = "INST"
    COMMERCIAL = "COMM"
    INDUSTRIAL = "IND"

class ConductorType(Enum):
    """Types of conductors in the network"""
    BACKBONE = "backbone"      # Main MV lines
    DISTRIBUTION = "distribution"  # LV distribution lines
    DROPLINE = "dropline"      # Customer droplines
    SERVICE = "service"        # Service connections

class VoltageLevel(Enum):
    """Voltage levels in the network"""
    MV_19KV = 19000
    MV_11KV = 11000
    LV_400V = 400
    LV_230V = 230

@dataclass
class Pole:
    """Enhanced pole model with validation status"""
    pole_id: str
    utm_x: float
    utm_y: float
    gps_lat: Optional[float] = None
    gps_lng: Optional[float] = None
    voltage_level: Optional[VoltageLevel] = None
    pole_type: Optional[str] = None
    status: str = "planned"
    kml_validated: bool = False
    kml_source: Optional[str] = None  # "MV" or "LV"
    field_verified: bool = False
    installation_date: Optional[datetime] = None
    
    def is_valid_reference(self) -> bool:
        """Check if pole has valid reference format"""
        # Format: SITE_WP_ID (e.g., KET_17_GA120)
        parts = self.pole_id.split('_')
        return len(parts) == 3 and parts[0].isalpha() and parts[1].isdigit()

@dataclass
class NetworkConductor:
    """Conductor for pole-to-pole network connections"""
    conductor_id: str
    from_pole: str
    to_pole: str
    cable_type: str
    cable_size: Optional[str] = None
    length_m: float = 0.0
    voltage_level: VoltageLevel = VoltageLevel.LV_400V
    conductor_type: ConductorType = ConductorType.DISTRIBUTION
    phases: int = 1
    status: str = "planned"
    kml_validated: bool = False
    field_verified: bool = False
    installation_date: Optional[datetime] = None
    
    def is_backbone(self) -> bool:
        """Check if this is a backbone conductor"""
        return self.voltage_level in [VoltageLevel.MV_19KV, VoltageLevel.MV_11KV]
    
    def is_valid_reference(self) -> bool:
        """Validate pole references"""
        return (self.from_pole and '_' in self.from_pole and 
                self.to_pole and '_' in self.to_pole)

@dataclass
class CustomerConnection:
    """Customer connection including dropline and service details"""
    connection_id: str
    customer_number: str
    customer_name: Optional[str] = None
    connection_type: ConnectionType = ConnectionType.HOUSEHOLD_1
    pole_id: str = ""  # Connection pole
    dropline_length_m: float = 0.0
    service_cable_type: Optional[str] = None
    utm_x: Optional[float] = None
    utm_y: Optional[float] = None
    gps_lat: Optional[float] = None
    gps_lng: Optional[float] = None
    meter_number: Optional[str] = None
    tariff_category: Optional[str] = None
    status: str = "planned"
    kml_validated: bool = False
    field_verified: bool = False
    connection_date: Optional[datetime] = None
    
    def parse_from_reference(self, ref_string: str) -> bool:
        """
        Parse customer connection from reference string
        Format: "KET 2246 HH1" or "KET_2246_HH1"
        """
        # Handle both space and underscore delimiters
        parts = ref_string.replace(' ', '_').split('_')
        if len(parts) >= 3:
            self.connection_id = ref_string
            self.customer_number = parts[1]
            # Parse connection type
            type_str = parts[2].upper()
            for conn_type in ConnectionType:
                if conn_type.value == type_str:
                    self.connection_type = conn_type
                    return True
        return False

@dataclass
class Transformer:
    """Enhanced transformer model"""
    transformer_id: str
    capacity_kva: float
    primary_voltage: VoltageLevel = VoltageLevel.MV_11KV
    secondary_voltage: VoltageLevel = VoltageLevel.LV_400V
    location_pole: str = ""
    utm_x: Optional[float] = None
    utm_y: Optional[float] = None
    gps_lat: Optional[float] = None
    gps_lng: Optional[float] = None
    transformer_type: str = "distribution"
    manufacturer: Optional[str] = None
    serial_number: Optional[str] = None
    status: str = "planned"
    kml_validated: bool = False
    field_verified: bool = False
    installation_date: Optional[datetime] = None
    
    def get_load_capacity(self) -> float:
        """Get usable load capacity (80% of rating)"""
        return self.capacity_kva * 0.8

@dataclass
class NetworkSegment:
    """Group of connected network components"""
    segment_id: str
    transformer_id: Optional[str] = None
    poles: List[str] = field(default_factory=list)
    conductors: List[str] = field(default_factory=list)
    customers: List[str] = field(default_factory=list)
    voltage_level: VoltageLevel = VoltageLevel.LV_400V
    total_length_m: float = 0.0
    total_connections: int = 0
    max_voltage_drop_percent: float = 0.0
    
    def add_pole(self, pole_id: str):
        """Add pole to segment"""
        if pole_id not in self.poles:
            self.poles.append(pole_id)
    
    def add_conductor(self, conductor_id: str):
        """Add conductor to segment"""
        if conductor_id not in self.conductors:
            self.conductors.append(conductor_id)
    
    def add_customer(self, customer_id: str):
        """Add customer to segment"""
        if customer_id not in self.customers:
            self.customers.append(customer_id)
            self.total_connections += 1

@dataclass
class EnhancedNetworkModel:
    """Complete network model with all components"""
    site_code: str
    poles: Dict[str, Pole] = field(default_factory=dict)
    network_conductors: Dict[str, NetworkConductor] = field(default_factory=dict)
    customer_connections: Dict[str, CustomerConnection] = field(default_factory=dict)
    transformers: Dict[str, Transformer] = field(default_factory=dict)
    network_segments: Dict[str, NetworkSegment] = field(default_factory=dict)
    
    def add_pole(self, pole: Pole):
        """Add pole to network"""
        self.poles[pole.pole_id] = pole
    
    def add_conductor(self, conductor: NetworkConductor):
        """Add network conductor"""
        self.network_conductors[conductor.conductor_id] = conductor
    
    def add_customer(self, customer: CustomerConnection):
        """Add customer connection"""
        self.customer_connections[customer.connection_id] = customer
    
    def add_transformer(self, transformer: Transformer):
        """Add transformer"""
        self.transformers[transformer.transformer_id] = transformer
    
    def get_statistics(self) -> Dict:
        """Get network statistics"""
        total_poles = len(self.poles)
        validated_poles = sum(1 for p in self.poles.values() if p.kml_validated)
        
        total_conductors = len(self.network_conductors)
        backbone_conductors = sum(1 for c in self.network_conductors.values() if c.is_backbone())
        
        total_customers = len(self.customer_connections)
        connected_customers = sum(1 for c in self.customer_connections.values() if c.status == "connected")
        
        total_transformers = len(self.transformers)
        total_capacity = sum(t.capacity_kva for t in self.transformers.values())
        
        return {
            "site_code": self.site_code,
            "poles": {
                "total": total_poles,
                "validated": validated_poles,
                "validation_rate": validated_poles / total_poles if total_poles > 0 else 0
            },
            "conductors": {
                "total": total_conductors,
                "backbone": backbone_conductors,
                "distribution": total_conductors - backbone_conductors
            },
            "customers": {
                "total": total_customers,
                "connected": connected_customers,
                "pending": total_customers - connected_customers
            },
            "transformers": {
                "total": total_transformers,
                "total_capacity_kva": total_capacity
            },
            "segments": {
                "total": len(self.network_segments)
            }
        }
    
    def validate_network(self) -> Tuple[bool, List[str]]:
        """Validate network integrity"""
        issues = []
        
        # Check for orphaned poles
        connected_poles = set()
        for conductor in self.network_conductors.values():
            connected_poles.add(conductor.from_pole)
            connected_poles.add(conductor.to_pole)
        
        orphaned_poles = set(self.poles.keys()) - connected_poles
        if orphaned_poles:
            issues.append(f"Found {len(orphaned_poles)} orphaned poles")
        
        # Check for invalid pole references in conductors
        for conductor_id, conductor in self.network_conductors.items():
            if conductor.from_pole not in self.poles:
                issues.append(f"Conductor {conductor_id}: invalid from_pole {conductor.from_pole}")
            if conductor.to_pole not in self.poles:
                issues.append(f"Conductor {conductor_id}: invalid to_pole {conductor.to_pole}")
        
        # Check for customers without valid poles
        for customer_id, customer in self.customer_connections.items():
            if customer.pole_id and customer.pole_id not in self.poles:
                # Check if it's a customer reference that needs parsing
                if not customer.parse_from_reference(customer.pole_id):
                    issues.append(f"Customer {customer_id}: invalid pole {customer.pole_id}")
        
        # Check transformer locations
        for tx_id, transformer in self.transformers.items():
            if transformer.location_pole and transformer.location_pole not in self.poles:
                issues.append(f"Transformer {tx_id}: invalid location pole {transformer.location_pole}")
        
        return len(issues) == 0, issues
