"""
Data Converter for Enhanced Model
Converts existing Excel/KML data to enhanced data model
"""

import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging

from modules.data_model.enhanced_model import (
    EnhancedNetworkModel, Pole, NetworkConductor, CustomerConnection,
    Transformer, NetworkSegment, ConnectionType, ConductorType, 
    VoltageLevel
)

logger = logging.getLogger(__name__)

class DataConverter:
    """Convert legacy data to enhanced model"""
    
    def __init__(self, site_code: str):
        self.site_code = site_code
        self.model = EnhancedNetworkModel(site_code=site_code)
        self.customer_pattern = re.compile(r'^(\w+)[\s_]+(\d+)[\s_]+(\w+)$')
        
    def convert_poles(self, poles_data: List[Dict]) -> Dict[str, str]:
        """
        Convert pole data to enhanced model
        Returns mapping of original to new IDs
        """
        pole_mapping = {}
        
        for pole_dict in poles_data:
            pole_id = pole_dict.get('pole_id', '')
            
            # Skip invalid poles
            if not pole_id:
                continue
            
            # Determine voltage level from pole ID pattern
            voltage_level = None
            if '_GA' in pole_id or '_GB' in pole_id:
                voltage_level = VoltageLevel.MV_11KV
            elif '_IA' in pole_id or '_IB' in pole_id:
                voltage_level = VoltageLevel.LV_400V
            
            pole = Pole(
                pole_id=pole_id,
                utm_x=pole_dict.get('utm_x', 0.0),
                utm_y=pole_dict.get('utm_y', 0.0),
                gps_lat=pole_dict.get('gps_y'),
                gps_lng=pole_dict.get('gps_x'),
                voltage_level=voltage_level,
                pole_type=pole_dict.get('type', 'standard'),
                status=pole_dict.get('status', 'planned')
            )
            
            self.model.add_pole(pole)
            pole_mapping[pole_id] = pole_id
            
        logger.info(f"Converted {len(self.model.poles)} poles")
        return pole_mapping
    
    def convert_conductors(self, conductors_data: List[Dict]) -> Tuple[int, int]:
        """
        Convert conductor data, separating network conductors from customer droplines
        Returns (network_count, dropline_count)
        """
        network_count = 0
        dropline_count = 0
        
        for conductor_dict in conductors_data:
            from_pole = conductor_dict.get('from_pole', '')
            to_pole = conductor_dict.get('to_pole', '')
            
            # Check if this is a customer dropline
            if self._is_customer_reference(to_pole):
                # Create customer connection
                customer = self._create_customer_from_reference(
                    to_pole, from_pole, conductor_dict
                )
                if customer:
                    self.model.add_customer(customer)
                    dropline_count += 1
            else:
                # Create network conductor
                conductor_id = f"{from_pole}_{to_pole}"
                
                # Determine conductor type and voltage
                conductor_type = ConductorType.DISTRIBUTION
                voltage_level = VoltageLevel.LV_400V
                
                if from_pole.startswith(f"{self.site_code}_") and '_G' in from_pole:
                    conductor_type = ConductorType.BACKBONE
                    voltage_level = VoltageLevel.MV_11KV
                
                conductor = NetworkConductor(
                    conductor_id=conductor_id,
                    from_pole=from_pole,
                    to_pole=to_pole,
                    cable_type=conductor_dict.get('cable_type', 'ABC'),
                    cable_size=conductor_dict.get('cable_size'),
                    length_m=conductor_dict.get('length', 0.0),
                    voltage_level=voltage_level,
                    conductor_type=conductor_type,
                    phases=conductor_dict.get('phases', 1),
                    status=conductor_dict.get('status', 'planned')
                )
                
                self.model.add_conductor(conductor)
                network_count += 1
        
        logger.info(f"Converted {network_count} network conductors, {dropline_count} droplines")
        return network_count, dropline_count
    
    def convert_transformers(self, transformers_data: List[Dict]) -> int:
        """Convert transformer data"""
        count = 0
        
        for tx_dict in transformers_data:
            tx_id = tx_dict.get('transformer_id')
            if not tx_id:
                continue
            
            # Determine voltage levels
            primary_v = tx_dict.get('primary_voltage', 11000)
            secondary_v = tx_dict.get('secondary_voltage', 400)
            
            primary_voltage = VoltageLevel.MV_11KV
            if primary_v == 19000:
                primary_voltage = VoltageLevel.MV_19KV
            
            secondary_voltage = VoltageLevel.LV_400V
            if secondary_v == 230:
                secondary_voltage = VoltageLevel.LV_230V
            
            transformer = Transformer(
                transformer_id=tx_id,
                capacity_kva=tx_dict.get('capacity_kva', 0.0),
                primary_voltage=primary_voltage,
                secondary_voltage=secondary_voltage,
                location_pole=tx_dict.get('location_pole', ''),
                utm_x=tx_dict.get('utm_x'),
                utm_y=tx_dict.get('utm_y'),
                gps_lat=tx_dict.get('gps_lat'),
                gps_lng=tx_dict.get('gps_lng'),
                transformer_type=tx_dict.get('type', 'distribution'),
                status=tx_dict.get('status', 'planned')
            )
            
            self.model.add_transformer(transformer)
            count += 1
        
        logger.info(f"Converted {count} transformers")
        return count
    
    def apply_kml_validation(self, kml_data: Dict):
        """Apply KML validation data to model"""
        validated_count = 0
        
        # Validate poles
        if 'poles_mv' in kml_data:
            for pole_id in kml_data['poles_mv']:
                if pole_id in self.model.poles:
                    self.model.poles[pole_id].kml_validated = True
                    self.model.poles[pole_id].kml_source = "MV"
                    validated_count += 1
        
        if 'poles_lv' in kml_data:
            for pole_id in kml_data['poles_lv']:
                if pole_id in self.model.poles:
                    self.model.poles[pole_id].kml_validated = True
                    self.model.poles[pole_id].kml_source = "LV"
                    validated_count += 1
        
        # Validate customer connections
        if 'customers' in kml_data:
            for customer_ref in kml_data['customers']:
                # Try to match with existing customers
                for customer_id, customer in self.model.customer_connections.items():
                    if customer.customer_number in customer_ref:
                        customer.kml_validated = True
        
        logger.info(f"Applied KML validation to {validated_count} components")
        return validated_count
    
    def build_network_segments(self):
        """Build network segments from connectivity"""
        from collections import deque
        
        visited_poles = set()
        segment_count = 0
        
        # Find all transformer poles as segment roots
        for tx_id, transformer in self.model.transformers.items():
            if transformer.location_pole and transformer.location_pole not in visited_poles:
                segment_id = f"SEG_{self.site_code}_{segment_count:03d}"
                segment = self._trace_segment(
                    transformer.location_pole, 
                    visited_poles,
                    transformer_id=tx_id
                )
                if segment:
                    segment.segment_id = segment_id
                    self.model.network_segments[segment_id] = segment
                    segment_count += 1
        
        # Find remaining unconnected segments
        for pole_id in self.model.poles:
            if pole_id not in visited_poles:
                segment_id = f"SEG_{self.site_code}_{segment_count:03d}"
                segment = self._trace_segment(pole_id, visited_poles)
                if segment:
                    segment.segment_id = segment_id
                    self.model.network_segments[segment_id] = segment
                    segment_count += 1
        
        logger.info(f"Built {segment_count} network segments")
        return segment_count
    
    def _is_customer_reference(self, reference: str) -> bool:
        """Check if reference is a customer connection"""
        # Patterns: "KET 2246 HH1", "KET_2246_SME", etc.
        if not reference:
            return False
        
        # Check for customer number pattern
        parts = reference.replace(' ', '_').split('_')
        if len(parts) >= 3:
            # Second part should be numeric (customer number)
            # Third part should be connection type
            if parts[1].isdigit() and parts[2].upper() in ['HH1', 'HH2', 'SME', 'HHSME', 'COMM', 'IND']:
                return True
        
        return False
    
    def _create_customer_from_reference(self, 
                                       customer_ref: str, 
                                       pole_id: str,
                                       conductor_dict: Dict) -> Optional[CustomerConnection]:
        """Create customer connection from reference string"""
        customer = CustomerConnection(
            connection_id=customer_ref,
            customer_number="",
            pole_id=pole_id,
            dropline_length_m=conductor_dict.get('length', 0.0),
            service_cable_type=conductor_dict.get('cable_type'),
            status=conductor_dict.get('status', 'planned')
        )
        
        if customer.parse_from_reference(customer_ref):
            return customer
        
        return None
    
    def _trace_segment(self, 
                       start_pole: str, 
                       visited: set,
                       transformer_id: Optional[str] = None) -> Optional[NetworkSegment]:
        """Trace network segment from starting pole"""
        from collections import deque
        
        segment = NetworkSegment(
            segment_id="",
            transformer_id=transformer_id
        )
        
        queue = deque([start_pole])
        
        while queue:
            pole_id = queue.popleft()
            
            if pole_id in visited:
                continue
            
            visited.add(pole_id)
            segment.add_pole(pole_id)
            
            # Find connected conductors
            for conductor_id, conductor in self.model.network_conductors.items():
                if conductor.from_pole == pole_id:
                    segment.add_conductor(conductor_id)
                    segment.total_length_m += conductor.length_m
                    if conductor.to_pole not in visited:
                        queue.append(conductor.to_pole)
                elif conductor.to_pole == pole_id:
                    segment.add_conductor(conductor_id)
                    if conductor.from_pole not in visited:
                        queue.append(conductor.from_pole)
            
            # Find connected customers
            for customer_id, customer in self.model.customer_connections.items():
                if customer.pole_id == pole_id:
                    segment.add_customer(customer_id)
        
        # Only return segment if it has content
        if len(segment.poles) > 0:
            return segment
        
        return None
    
    def get_model(self) -> EnhancedNetworkModel:
        """Get the converted enhanced model"""
        return self.model
    
    def export_summary(self) -> Dict:
        """Export conversion summary"""
        stats = self.model.get_statistics()
        is_valid, issues = self.model.validate_network()
        
        return {
            "site_code": self.site_code,
            "conversion_timestamp": datetime.now().isoformat(),
            "statistics": stats,
            "validation": {
                "is_valid": is_valid,
                "issue_count": len(issues),
                "issues": issues[:10] if issues else []  # First 10 issues
            }
        }
