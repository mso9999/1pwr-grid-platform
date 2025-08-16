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
