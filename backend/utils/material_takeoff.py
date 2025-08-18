"""
Material takeoff report generator
Calculates bill of materials from network data
"""

from typing import Dict, List, Any
from collections import defaultdict
import math

class MaterialTakeoffCalculator:
    """Calculate material takeoff/bill of materials from network data"""
    
    def __init__(self, network_data: Dict[str, Any]):
        self.poles = network_data.get('poles', [])
        self.conductors = network_data.get('conductors', [])
        self.connections = network_data.get('connections', [])
        self.transformers = network_data.get('transformers', [])
        
    def calculate_takeoff(self) -> Dict[str, Any]:
        """
        Calculate complete material takeoff report
        Returns detailed breakdown of all materials needed
        """
        takeoff = {
            'summary': self._calculate_summary(),
            'poles': self._calculate_pole_materials(),
            'conductors': self._calculate_conductor_materials(),
            'connections': self._calculate_connection_materials(),
            'transformers': self._calculate_transformer_materials(),
            'hardware': self._estimate_hardware(),
            'totals': {}
        }
        
        # Calculate totals
        takeoff['totals'] = self._calculate_totals(takeoff)
        
        return takeoff
    
    def _calculate_summary(self) -> Dict[str, Any]:
        """Calculate summary statistics"""
        return {
            'total_poles': len(self.poles),
            'total_connections': len(self.connections),
            'total_conductors': len(self.conductors),
            'total_transformers': len(self.transformers),
            'network_length_m': sum(c.get('length', 0) for c in self.conductors)
        }
    
    def _calculate_pole_materials(self) -> Dict[str, Any]:
        """Calculate pole materials by type and class"""
        pole_breakdown = defaultdict(lambda: defaultdict(int))
        
        for pole in self.poles:
            pole_type = pole.get('pole_type', 'UNKNOWN')
            pole_class = pole.get('pole_class', 'UNKNOWN')
            angle_class = pole.get('angle_class', 'UNKNOWN')
            
            # Combine class and angle for full specification
            pole_spec = f"{pole_class}_{angle_class}" if angle_class != 'UNKNOWN' else pole_class
            pole_breakdown[pole_type][pole_spec] += 1
        
        # Convert to regular dict and add summary
        result = {
            'by_type': dict(pole_breakdown),
            'details': []
        }
        
        # Create detailed list
        for pole_type, specs in pole_breakdown.items():
            for spec, count in specs.items():
                result['details'].append({
                    'type': pole_type,
                    'specification': spec,
                    'quantity': count,
                    'unit': 'poles'
                })
        
        # Sort by quantity descending
        result['details'].sort(key=lambda x: x['quantity'], reverse=True)
        
        return result
    
    def _calculate_conductor_materials(self) -> Dict[str, Any]:
        """Calculate conductor materials by type and specification"""
        conductor_breakdown = defaultdict(lambda: {
            'count': 0,
            'total_length': 0,
            'specifications': defaultdict(float)
        })
        
        for conductor in self.conductors:
            cond_type = conductor.get('conductor_type', 'UNKNOWN')
            cond_spec = conductor.get('conductor_spec', conductor.get('conductor_size', '50'))
            length = conductor.get('length', 0)
            
            conductor_breakdown[cond_type]['count'] += 1
            conductor_breakdown[cond_type]['total_length'] += length
            conductor_breakdown[cond_type]['specifications'][cond_spec] += length
        
        # Convert to regular dict
        result = {
            'by_type': {},
            'details': []
        }
        
        for cond_type, data in conductor_breakdown.items():
            result['by_type'][cond_type] = {
                'count': data['count'],
                'total_length_m': round(data['total_length'], 2),
                'total_length_km': round(data['total_length'] / 1000, 3),
                'specifications': dict(data['specifications'])
            }
            
            # Add to details
            for spec, length in data['specifications'].items():
                result['details'].append({
                    'type': cond_type,
                    'specification': spec,
                    'length_m': round(length, 2),
                    'length_km': round(length / 1000, 3),
                    'count': sum(1 for c in self.conductors 
                               if c.get('conductor_type') == cond_type 
                               and c.get('conductor_spec', c.get('conductor_size', '50')) == spec),
                    'unit': 'meters'
                })
        
        # Sort by length descending
        result['details'].sort(key=lambda x: x['length_m'], reverse=True)
        
        return result
    
    def _calculate_connection_materials(self) -> Dict[str, Any]:
        """Calculate connection/meter materials"""
        meter_status = defaultdict(int)
        
        for connection in self.connections:
            st_code_3 = connection.get('st_code_3', 0)
            meter_status[st_code_3] += 1
        
        # Map status codes to descriptions
        status_descriptions = {
            0: 'Not installed',
            1: 'Meter box installed',
            2: 'Meter installed',
            3: 'Meter wired',
            4: 'Meter tested',
            5: 'Meter commissioned',
            6: 'Meter active',
            7: 'Meter reading taken',
            8: 'Meter verified',
            9: 'Meter operational',
            10: 'Meter fully functional'
        }
        
        result = {
            'total': len(self.connections),
            'by_status': {},
            'meter_boxes_needed': 0,
            'meters_needed': 0
        }
        
        for status, count in meter_status.items():
            result['by_status'][status] = {
                'count': count,
                'description': status_descriptions.get(status, f'Status {status}')
            }
            
            # Calculate materials needed
            if status == 0:
                result['meter_boxes_needed'] += count
                result['meters_needed'] += count
            elif status == 1:
                result['meters_needed'] += count
        
        return result
    
    def _calculate_transformer_materials(self) -> Dict[str, Any]:
        """Calculate transformer materials"""
        transformer_breakdown = defaultdict(lambda: defaultdict(int))
        
        for transformer in self.transformers:
            trans_type = transformer.get('type', 'UNKNOWN')
            capacity = transformer.get('capacity_kva', 0)
            transformer_breakdown[trans_type][f"{capacity}kVA"] += 1
        
        result = {
            'total': len(self.transformers),
            'by_type': dict(transformer_breakdown),
            'details': []
        }
        
        for trans_type, capacities in transformer_breakdown.items():
            for capacity, count in capacities.items():
                result['details'].append({
                    'type': trans_type,
                    'capacity': capacity,
                    'quantity': count,
                    'unit': 'transformers'
                })
        
        return result
    
    def _estimate_hardware(self) -> Dict[str, Any]:
        """Estimate hardware requirements based on network topology"""
        hardware = {
            'stay_wires': 0,
            'stay_blocks': 0,
            'cross_arms': 0,
            'insulators': 0,
            'clamps': 0,
            'lugs': 0
        }
        
        # Estimate based on poles and angles
        for pole in self.poles:
            angle_class = pole.get('angle_class', 'I')
            pole_class = pole.get('pole_class', 'LV')
            
            # Stay wires for angle poles
            if angle_class in ['A', 'T', 'D']:
                hardware['stay_wires'] += 2 if angle_class == 'A' else 1
                hardware['stay_blocks'] += 2 if angle_class == 'A' else 1
            
            # Cross arms for MV poles
            if 'MV' in pole_class or '_M' in pole.get('pole_id', ''):
                hardware['cross_arms'] += 1
                hardware['insulators'] += 3  # 3-phase
            else:
                hardware['insulators'] += 1  # Single phase
            
            # Clamps for connections
            # Count conductors connected to this pole
            pole_id = pole.get('pole_id')
            connected_conductors = sum(1 for c in self.conductors 
                                      if c.get('from_pole') == pole_id 
                                      or c.get('to_pole') == pole_id)
            hardware['clamps'] += connected_conductors
        
        # Lugs for connections
        hardware['lugs'] = len(self.connections) * 2  # In and out
        
        return hardware
    
    def _calculate_totals(self, takeoff: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate total costs and weights (placeholder for actual pricing)"""
        return {
            'poles': takeoff['summary']['total_poles'],
            'conductors_km': round(takeoff['summary']['network_length_m'] / 1000, 3),
            'connections': takeoff['summary']['total_connections'],
            'transformers': takeoff['summary']['total_transformers'],
            'estimated_cost': 'Requires pricing data',
            'estimated_weight_tons': 'Requires material specifications'
        }
    
    def export_to_dict(self) -> Dict[str, Any]:
        """Export takeoff report as dictionary for JSON serialization"""
        return self.calculate_takeoff()
