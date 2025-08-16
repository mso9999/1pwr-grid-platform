from typing import Dict, List, Any, Set, Optional
from collections import defaultdict
import networkx as nx


class NetworkValidator:
    """Validates network topology and data integrity"""
    
    def __init__(self):
        self.issues = []
        self.warnings = []
        self.info = []
        
    def validate_network(self, poles: List[Dict], conductors: List[Dict]) -> Dict[str, Any]:
        """
        Perform comprehensive network validation
        
        Args:
            poles: List of pole dictionaries
            conductors: List of conductor dictionaries
            
        Returns:
            Dictionary containing validation results
        """
        results = {
            'orphaned_poles': [],
            'invalid_conductors': [],
            'duplicate_pole_ids': [],
            'disconnected_components': [],
            'statistics': {
                'total_poles': len(poles),
                'total_conductors': len(conductors),
                'validation_rate': 0.0
            }
        }
        
        # Create pole ID lookup
        pole_ids = set()
        pole_id_counts = defaultdict(int)
        
        for pole in poles:
            pole_id = pole.get('pole_id') or pole.get('id')
            if pole_id:
                pole_ids.add(pole_id)
                pole_id_counts[pole_id] += 1
        
        # Check for duplicate pole IDs
        for pole_id, count in pole_id_counts.items():
            if count > 1:
                results['duplicate_pole_ids'].append(pole_id)
        
        # Validate conductors
        connected_poles = set()
        invalid_conductors = []
        
        for conductor in conductors:
            conductor_id = conductor.get('conductor_id') or conductor.get('id')
            from_pole = conductor.get('from_pole') or conductor.get('from')
            to_pole = conductor.get('to_pole') or conductor.get('to')
            
            issues = []
            if not from_pole:
                issues.append('Missing from_pole reference')
            elif from_pole not in pole_ids:
                issues.append(f'Invalid from_pole reference: {from_pole}')
            else:
                connected_poles.add(from_pole)
                
            if not to_pole:
                issues.append('Missing to_pole reference')
            elif to_pole not in pole_ids:
                issues.append(f'Invalid to_pole reference: {to_pole}')
            else:
                connected_poles.add(to_pole)
                
            if issues:
                invalid_conductors.append({
                    'id': conductor_id,
                    'reason': '; '.join(issues)
                })
        
        results['invalid_conductors'] = invalid_conductors
        
        # Find orphaned poles (poles with no conductors)
        orphaned_poles = pole_ids - connected_poles
        results['orphaned_poles'] = list(orphaned_poles)
        
        # Check network connectivity using NetworkX
        if conductors and poles:
            G = nx.Graph()
            
            # Add all poles as nodes
            for pole in poles:
                pole_id = pole.get('pole_id') or pole.get('id')
                if pole_id:
                    G.add_node(pole_id)
            
            # Add conductors as edges
            for conductor in conductors:
                from_pole = conductor.get('from_pole') or conductor.get('from')
                to_pole = conductor.get('to_pole') or conductor.get('to')
                
                if from_pole in pole_ids and to_pole in pole_ids:
                    G.add_edge(from_pole, to_pole)
            
            # Find disconnected components
            components = list(nx.connected_components(G))
            if len(components) > 1:
                # Sort components by size
                components = sorted(components, key=len, reverse=True)
                results['disconnected_components'] = [list(comp) for comp in components]
        
        # Calculate validation rate
        total_items = len(poles) + len(conductors)
        valid_items = len(poles) - len(results['orphaned_poles']) - len(results['duplicate_pole_ids'])
        valid_items += len(conductors) - len(results['invalid_conductors'])
        
        if total_items > 0:
            results['statistics']['validation_rate'] = (valid_items / total_items) * 100
        
        return results
    
    def validate_voltage_drop(self, voltage_results: Dict, threshold: float = 7.0) -> List[Dict]:
        """
        Validate voltage drop results against threshold
        
        Args:
            voltage_results: Voltage calculation results
            threshold: Maximum allowed voltage drop percentage
            
        Returns:
            List of voltage drop issues
        """
        issues = []
        
        if not voltage_results:
            return issues
            
        conductor_voltages = voltage_results.get('conductor_voltages', {})
        
        for conductor_id, voltage_data in conductor_voltages.items():
            voltage_drop = voltage_data.get('voltage_drop_percent', 0)
            
            if voltage_drop > threshold:
                issues.append({
                    'type': 'warning',
                    'conductor_id': conductor_id,
                    'voltage_drop': voltage_drop,
                    'threshold': threshold,
                    'message': f'Voltage drop {voltage_drop:.1f}% exceeds threshold {threshold}%'
                })
        
        return issues
    
    def validate_status_codes(self, elements: List[Dict], element_type: str) -> List[Dict]:
        """
        Validate status codes for consistency
        
        Args:
            elements: List of element dictionaries
            element_type: Type of element ('pole', 'conductor', 'connection')
            
        Returns:
            List of status code issues
        """
        issues = []
        
        for element in elements:
            element_id = element.get('id') or element.get(f'{element_type}_id')
            
            # Check SC1 (construction progress)
            sc1 = element.get('st_code_1')
            if sc1 is not None:
                if not isinstance(sc1, (int, float)) or sc1 < 0 or sc1 > 9:
                    issues.append({
                        'type': 'error',
                        'element_id': element_id,
                        'element_type': element_type,
                        'field': 'st_code_1',
                        'value': sc1,
                        'message': f'Invalid SC1 value: {sc1} (must be 0-9)'
                    })
            
            # Check SC2 (further progress)
            sc2 = element.get('st_code_2')
            valid_sc2 = ['NA', 'SP', 'SI', 'KP', 'KI', 'TP', 'TI', 'TC', 'MP', 'MI', 'MC', 'EP', 'EI']
            if sc2 and sc2 not in valid_sc2:
                issues.append({
                    'type': 'warning',
                    'element_id': element_id,
                    'element_type': element_type,
                    'field': 'st_code_2',
                    'value': sc2,
                    'message': f'Unknown SC2 value: {sc2}'
                })
        
        return issues
    
    def validate_conductor_lengths(self, conductors: List[Dict]) -> List[Dict]:
        """
        Validate conductor lengths are within reasonable ranges
        
        Args:
            conductors: List of conductor dictionaries
            
        Returns:
            List of conductor length issues
        """
        issues = []
        
        # Define reasonable length ranges by conductor type
        length_ranges = {
            'MV': (10, 5000),  # 10m to 5km for MV lines
            'LV': (5, 1000),   # 5m to 1km for LV lines
            'DROP': (3, 200),  # 3m to 200m for drop lines
            'SERVICE': (3, 100) # 3m to 100m for service lines
        }
        
        for conductor in conductors:
            conductor_id = conductor.get('conductor_id') or conductor.get('id')
            conductor_type = conductor.get('conductor_type', 'LV').upper()
            length = conductor.get('length', 0)
            
            # Check if length is positive
            if length <= 0:
                issues.append({
                    'type': 'error',
                    'conductor_id': conductor_id,
                    'length': length,
                    'message': f'Invalid conductor length: {length}m (must be positive)'
                })
                continue
            
            # Check if within reasonable range for type
            min_length, max_length = length_ranges.get(conductor_type, (1, 10000))
            if length < min_length or length > max_length:
                issues.append({
                    'type': 'warning',
                    'conductor_id': conductor_id,
                    'conductor_type': conductor_type,
                    'length': length,
                    'message': f'Unusual {conductor_type} conductor length: {length}m (expected {min_length}-{max_length}m)'
                })
        
        return issues
    
    def validate_pole_coordinates(self, poles: List[Dict]) -> List[Dict]:
        """
        Validate pole coordinates are within reasonable bounds
        
        Args:
            poles: List of pole dictionaries
            
        Returns:
            List of coordinate issues
        """
        issues = []
        
        # South Africa approximate bounds
        lat_bounds = (-35.0, -22.0)
        lng_bounds = (16.0, 33.0)
        
        for pole in poles:
            pole_id = pole.get('pole_id') or pole.get('id')
            lat = pole.get('latitude', 0)
            lng = pole.get('longitude', 0)
            
            # Check if coordinates are valid
            if lat == 0 and lng == 0:
                issues.append({
                    'type': 'error',
                    'pole_id': pole_id,
                    'message': 'Pole has no coordinates (0,0)'
                })
                continue
            
            # Check if within South Africa bounds
            if not (lat_bounds[0] <= lat <= lat_bounds[1]):
                issues.append({
                    'type': 'warning',
                    'pole_id': pole_id,
                    'latitude': lat,
                    'message': f'Pole latitude {lat} outside expected range {lat_bounds}'
                })
            
            if not (lng_bounds[0] <= lng <= lng_bounds[1]):
                issues.append({
                    'type': 'warning',
                    'pole_id': pole_id,
                    'longitude': lng,
                    'message': f'Pole longitude {lng} outside expected range {lng_bounds}'
                })
        
        return issues
    
    def validate_pole_spacing(self, poles: List[Dict], conductors: List[Dict]) -> List[Dict]:
        """
        Validate spacing between connected poles
        
        Args:
            poles: List of pole dictionaries
            conductors: List of conductor dictionaries
            
        Returns:
            List of spacing issues
        """
        issues = []
        
        # Create pole lookup by ID
        pole_lookup = {
            (pole.get('pole_id') or pole.get('id')): pole 
            for pole in poles
        }
        
        # Check spacing for each conductor
        for conductor in conductors:
            conductor_id = conductor.get('conductor_id') or conductor.get('id')
            from_pole_id = conductor.get('from_pole') or conductor.get('from')
            to_pole_id = conductor.get('to_pole') or conductor.get('to')
            
            from_pole = pole_lookup.get(from_pole_id)
            to_pole = pole_lookup.get(to_pole_id)
            
            if from_pole and to_pole:
                # Calculate distance between poles
                lat1, lng1 = from_pole.get('latitude', 0), from_pole.get('longitude', 0)
                lat2, lng2 = to_pole.get('latitude', 0), to_pole.get('longitude', 0)
                
                if lat1 and lng1 and lat2 and lng2:
                    # Haversine formula for distance
                    import math
                    R = 6371000  # Earth radius in meters
                    lat1_rad, lat2_rad = math.radians(lat1), math.radians(lat2)
                    dlat = math.radians(lat2 - lat1)
                    dlng = math.radians(lng2 - lng1)
                    
                    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlng/2)**2
                    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
                    distance = R * c
                    
                    conductor_length = conductor.get('length', 0)
                    
                    # Check if conductor length matches pole spacing
                    if conductor_length > 0:
                        length_diff = abs(distance - conductor_length)
                        if length_diff > conductor_length * 0.2:  # More than 20% difference
                            issues.append({
                                'type': 'warning',
                                'conductor_id': conductor_id,
                                'from_pole': from_pole_id,
                                'to_pole': to_pole_id,
                                'calculated_distance': round(distance, 2),
                                'conductor_length': conductor_length,
                                'difference': round(length_diff, 2),
                                'message': f'Conductor length {conductor_length}m differs from pole spacing {distance:.1f}m'
                            })
        
        return issues
