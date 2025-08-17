from typing import Dict, List, Any, Optional, Set, Tuple
import math
import networkx as nx
from collections import deque


class VoltageCalculator:
    """Calculate voltage drops across the network using electrical formulas"""
    
    # Standard conductor specifications (mm² -> R ohm/km)
    CONDUCTOR_RESISTANCE = {
        '16': 1.91,    # 16mm² AAC
        '25': 1.20,    # 25mm² AAC
        '35': 0.868,   # 35mm² AAC
        '50': 0.641,   # 50mm² AAC
        '70': 0.443,   # 70mm² AAC
        '95': 0.320,   # 95mm² AAC
        '120': 0.253,  # 120mm² AAC
        '150': 0.206,  # 150mm² AAC
        '185': 0.164,  # 185mm² AAC
        '240': 0.125,  # 240mm² AAC
        '10': 3.08,    # 10mm² service cable
        '6': 5.13,     # 6mm² service cable
        '4': 7.70,     # 4mm² service cable
    }
    
    # Standard conductor reactance (ohm/km) - approximate values
    CONDUCTOR_REACTANCE = {
        'MV': 0.35,  # Medium voltage typical
        'LV': 0.08,  # Low voltage typical  
        'DROP': 0.06  # Service drop typical
    }
    
    def __init__(self):
        self.network = None
        self.pole_voltages = {}
        self.conductor_currents = {}
        
    def calculate_voltage_drop(self, 
                              poles: List[Dict], 
                              conductors: List[Dict],
                              source_voltage: float = 11000,
                              source_pole_id: Optional[str] = None,
                              power_factor: float = 0.85) -> Dict[str, Any]:
        """
        Calculate voltage drop for each conductor and pole using power flow analysis
        
        Args:
            poles: List of pole dictionaries
            conductors: List of conductor dictionaries
            source_voltage: Source voltage in volts
            source_pole_id: ID of the source pole (auto-detect if None)
            power_factor: System power factor (default 0.85)
            
        Returns:
            Dictionary with voltage calculations
        """
        # Build network graph
        self._build_network(poles, conductors)
        
        # Find source pole if not specified
        if not source_pole_id:
            source_pole_id = self._find_source_pole(poles, conductors)
            
        if not source_pole_id:
            return self._empty_results(source_voltage)
            
        # Initialize results
        results = {
            'source_voltage': source_voltage,
            'source_pole': source_pole_id,
            'conductor_voltages': {},
            'pole_voltages': {},
            'statistics': {}
        }
        
        # Calculate voltage drops using BFS from source
        self._calculate_network_voltages(
            source_pole_id, 
            source_voltage, 
            conductors, 
            power_factor
        )
        
        # Store conductor voltage drops
        for conductor in conductors:
            cond_id = conductor['conductor_id']
            from_pole = conductor.get('from_pole')
            to_pole = conductor.get('to_pole')
            
            if from_pole in self.pole_voltages and to_pole in self.pole_voltages:
                from_voltage = self.pole_voltages[from_pole]
                to_voltage = self.pole_voltages[to_pole]
                voltage_drop = abs(from_voltage - to_voltage)
                voltage_drop_percent = (voltage_drop / source_voltage) * 100
                
                results['conductor_voltages'][cond_id] = {
                    'from_voltage': from_voltage,
                    'to_voltage': to_voltage,
                    'voltage_drop_volts': voltage_drop,
                    'voltage_drop_percent': voltage_drop_percent,
                    'length': conductor.get('length', 0),
                    'conductor_type': conductor.get('conductor_type', 'Unknown')
                }
        
        # Store pole voltages
        for pole in poles:
            pole_id = pole['pole_id']
            if pole_id in self.pole_voltages:
                voltage = self.pole_voltages[pole_id]
                voltage_drop_percent = ((source_voltage - voltage) / source_voltage) * 100
                
                results['pole_voltages'][pole_id] = {
                    'voltage': voltage,
                    'voltage_drop_percent': voltage_drop_percent,
                    'pole_type': pole.get('pole_type', 'POLE')
                }
        
        # Calculate statistics
        if self.pole_voltages:
            voltages = list(self.pole_voltages.values())
            results['statistics'] = {
                'total_poles': len(poles),
                'total_conductors': len(conductors),
                'poles_analyzed': len(self.pole_voltages),
                'max_voltage': max(voltages),
                'min_voltage': min(voltages),
                'avg_voltage': sum(voltages) / len(voltages),
                'max_voltage_drop_percent': ((source_voltage - min(voltages)) / source_voltage) * 100,
                'poles_below_threshold': sum(1 for v in voltages if ((source_voltage - v) / source_voltage) * 100 > 7.0)
            }
        else:
            results['statistics'] = self._empty_statistics(len(poles), len(conductors))
            
        return results
    
    def _build_network(self, poles: List[Dict], conductors: List[Dict]):
        """Build NetworkX graph from poles and conductors"""
        self.network = nx.Graph()
        
        # Add nodes
        for pole in poles:
            self.network.add_node(pole['pole_id'], **pole)
            
        # Add edges
        for conductor in conductors:
            from_pole = conductor.get('from_pole')
            to_pole = conductor.get('to_pole')
            if from_pole and to_pole:
                self.network.add_edge(from_pole, to_pole, **conductor)
    
    def _find_source_pole(self, poles: List[Dict], conductors: List[Dict]) -> Optional[str]:
        """Auto-detect source pole (typically substation or transformer)"""
        # Strategy 1: Look for poles connected to MV lines (likely substation)
        mv_poles = set()
        for conductor in conductors:
            if conductor.get('conductor_type') == 'MV':
                if conductor.get('from_pole'):
                    mv_poles.add(conductor['from_pole'])
                if conductor.get('to_pole'):
                    mv_poles.add(conductor['to_pole'])
        
        # Find MV pole with highest connectivity (likely the substation)
        if mv_poles and self.network:
            mv_connectivity = {}
            for pole in mv_poles:
                if pole in self.network:
                    mv_connectivity[pole] = self.network.degree(pole)
            if mv_connectivity:
                # Return MV pole with highest degree
                source = max(mv_connectivity, key=mv_connectivity.get)
                print(f"Found source pole by MV connectivity: {source} (degree: {mv_connectivity[source]})")
                return source
        
        # Strategy 2: Look for transformers or explicitly marked generation sites
        # (Removed incorrect BB assumption - BB is just Branch B, Sub-branch B in topology)
        
        # Strategy 3: Look for poles with high connectivity (likely substation)
        if self.network:
            degree_centrality = nx.degree_centrality(self.network)
            if degree_centrality:
                # Get pole with highest degree centrality
                source = max(degree_centrality, key=degree_centrality.get)
                print(f"Found source pole by degree centrality: {source}")
                return source
                
        # Fallback: return first pole
        if poles:
            print(f"Using fallback source pole: {poles[0]['pole_id']}")
            return poles[0]['pole_id']
        return None
    
    def _calculate_network_voltages(self, 
                                   source_pole_id: str, 
                                   source_voltage: float,
                                   conductors: List[Dict],
                                   power_factor: float):
        """Calculate voltages throughout network using simplified load flow"""
        # Initialize source voltage
        self.pole_voltages = {source_pole_id: source_voltage}
        
        # BFS to propagate voltage calculations
        visited = set()
        queue = deque([(source_pole_id, source_voltage)])
        
        while queue:
            current_pole, current_voltage = queue.popleft()
            
            if current_pole in visited:
                continue
            visited.add(current_pole)
            
            # Get connected conductors
            if current_pole in self.network:
                for neighbor in self.network.neighbors(current_pole):
                    if neighbor not in visited:
                        # Get conductor between poles
                        edge_data = self.network.get_edge_data(current_pole, neighbor)
                        
                        # Calculate voltage drop
                        voltage_drop = self._calculate_conductor_voltage_drop(
                            edge_data,
                            current_voltage,
                            power_factor
                        )
                        
                        # Calculate neighbor voltage
                        neighbor_voltage = current_voltage - voltage_drop
                        
                        # Store voltage if not already calculated or if better path found
                        if neighbor not in self.pole_voltages or self.pole_voltages[neighbor] < neighbor_voltage:
                            self.pole_voltages[neighbor] = max(0, neighbor_voltage)
                            queue.append((neighbor, self.pole_voltages[neighbor]))
    
    def _calculate_conductor_voltage_drop(self, 
                                         conductor: Dict,
                                         input_voltage: float,
                                         power_factor: float) -> float:
        """Calculate voltage drop for a single conductor"""
        # Get conductor parameters
        length_km = conductor.get('length', 0) / 1000  # Convert m to km
        conductor_spec = str(conductor.get('conductor_spec', '50'))
        conductor_type = conductor.get('conductor_type', 'LV')
        
        # Get resistance
        resistance = self.CONDUCTOR_RESISTANCE.get(conductor_spec, 0.641)  # Default to 50mm²
        reactance = self.CONDUCTOR_REACTANCE.get(conductor_type, 0.08)
        
        # Estimate current (simplified - assume 10A per connection for residential)
        estimated_current = 10.0  # Amperes
        
        # Calculate voltage drop using simplified formula
        # ΔV = I × L × (R × cos(φ) + X × sin(φ))
        cos_phi = power_factor
        sin_phi = math.sqrt(1 - power_factor**2)
        
        voltage_drop = estimated_current * length_km * (
            resistance * cos_phi + reactance * sin_phi
        )
        
        # For three-phase system, multiply by sqrt(3)
        if conductor_type == 'MV':
            voltage_drop *= math.sqrt(3)
            
        return voltage_drop
    
    def _empty_results(self, source_voltage: float) -> Dict[str, Any]:
        """Return empty results structure"""
        return {
            'source_voltage': source_voltage,
            'source_pole': None,
            'conductor_voltages': {},
            'pole_voltages': {},
            'statistics': {
                'total_poles': 0,
                'total_conductors': 0,
                'poles_analyzed': 0,
                'max_voltage': source_voltage,
                'min_voltage': source_voltage,
                'avg_voltage': source_voltage,
                'max_voltage_drop_percent': 0,
                'poles_below_threshold': 0
            }
        }
    
    def _empty_statistics(self, pole_count: int, conductor_count: int) -> Dict[str, Any]:
        """Return empty statistics"""
        return {
            'total_poles': pole_count,
            'total_conductors': conductor_count,
            'poles_analyzed': 0,
            'max_voltage': 0,
            'min_voltage': 0,
            'avg_voltage': 0,
            'max_voltage_drop_percent': 0,
            'poles_below_threshold': 0
        }
