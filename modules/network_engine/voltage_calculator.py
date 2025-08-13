"""
Voltage Drop Calculator
=======================
Implements voltage drop calculations for network validation.
Default threshold: 7% (configurable)
Supports both SWER (19kV single phase) and 11kV 3-phase systems.
"""

import networkx as nx
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class VoltageLevel(Enum):
    """Supported voltage levels"""
    SWER_19KV = 19000  # Single Wire Earth Return
    THREE_PHASE_11KV = 11000  # 3-phase system
    LV_400V = 400  # Low voltage 3-phase
    LV_230V = 230  # Low voltage single phase


@dataclass
class ConductorSpec:
    """Conductor electrical specifications"""
    name: str
    resistance_ohm_per_km: float  # Resistance in Ohms/km
    reactance_ohm_per_km: float  # Reactance in Ohms/km  
    current_rating_amps: float  # Current carrying capacity
    
    def impedance_per_km(self) -> complex:
        """Return complex impedance per km"""
        return complex(self.resistance_ohm_per_km, self.reactance_ohm_per_km)


# Default conductor library (can be extended via UI)
DEFAULT_CONDUCTORS = {
    'AAC_50': ConductorSpec('AAC 50mm²', 0.641, 0.38, 184),
    'AAC_35': ConductorSpec('AAC 35mm²', 0.917, 0.39, 148),
    'AAC_25': ConductorSpec('AAC 25mm²', 1.283, 0.40, 122),
    'AAC_16': ConductorSpec('AAC 16mm²', 2.004, 0.41, 96),
    'ABC_50': ConductorSpec('ABC 50mm²', 0.641, 0.08, 150),
    'ABC_35': ConductorSpec('ABC 35mm²', 0.917, 0.09, 120),
    'ABC_25': ConductorSpec('ABC 25mm²', 1.283, 0.09, 95),
    'ABC_16': ConductorSpec('ABC 16mm²', 2.004, 0.10, 75),
}


@dataclass
class VoltageDropResult:
    """Result of voltage drop calculation for a node"""
    node_id: str
    distance_km: float
    voltage_drop_v: float
    voltage_drop_percent: float
    final_voltage_v: float
    current_amps: float
    within_limits: bool
    path_from_source: List[str]


@dataclass
class NetworkVoltageAnalysis:
    """Complete network voltage analysis results"""
    source_voltage: float
    voltage_level: VoltageLevel
    max_voltage_drop_percent: float
    threshold_percent: float
    violations: List[VoltageDropResult]
    all_nodes: Dict[str, VoltageDropResult]
    is_valid: bool
    warnings: List[str]


class VoltageCalculator:
    """Calculate voltage drops in electrical network"""
    
    def __init__(self, 
                 voltage_drop_threshold: float = 7.0,
                 default_load_per_connection: float = 2.0):  # kW
        """
        Initialize voltage calculator
        
        Args:
            voltage_drop_threshold: Maximum allowed voltage drop percentage (default 7%)
            default_load_per_connection: Default load per connection in kW for peak scenario
        """
        self.voltage_drop_threshold = voltage_drop_threshold
        self.default_load_per_connection = default_load_per_connection
        self.conductor_library = DEFAULT_CONDUCTORS.copy()
    
    def add_conductor_type(self, name: str, spec: ConductorSpec) -> None:
        """Add a new conductor type to the library"""
        self.conductor_library[name] = spec
    
    def calculate_current(self, power_kw: float, voltage_v: float, 
                         power_factor: float = 0.9, is_three_phase: bool = False) -> float:
        """
        Calculate current from power
        
        Args:
            power_kw: Power in kilowatts
            voltage_v: Voltage in volts
            power_factor: Power factor (default 0.9)
            is_three_phase: Whether system is 3-phase
            
        Returns:
            Current in amperes
        """
        if is_three_phase:
            # I = P / (√3 * V * PF)
            return (power_kw * 1000) / (np.sqrt(3) * voltage_v * power_factor)
        else:
            # I = P / (V * PF)
            return (power_kw * 1000) / (voltage_v * power_factor)
    
    def calculate_voltage_drop(self,
                              length_km: float,
                              current_amps: float,
                              conductor_type: str,
                              is_three_phase: bool = False) -> float:
        """
        Calculate voltage drop for a conductor segment
        
        Args:
            length_km: Conductor length in kilometers
            current_amps: Current in amperes
            conductor_type: Type of conductor from library
            is_three_phase: Whether system is 3-phase
            
        Returns:
            Voltage drop in volts
        """
        if conductor_type not in self.conductor_library:
            logger.warning(f"Unknown conductor type: {conductor_type}, using AAC_35")
            conductor_type = 'AAC_35'
        
        conductor = self.conductor_library[conductor_type]
        impedance = conductor.impedance_per_km()
        
        if is_three_phase:
            # V_drop = √3 * I * Z * L
            voltage_drop = np.sqrt(3) * current_amps * abs(impedance) * length_km
        else:
            # V_drop = 2 * I * Z * L (for single phase, considering return path)
            voltage_drop = 2 * current_amps * abs(impedance) * length_km
        
        return voltage_drop
    
    def analyze_network(self,
                       network: nx.Graph,
                       transformer_node: str,
                       voltage_level: VoltageLevel = VoltageLevel.THREE_PHASE_11KV,
                       load_profile: Optional[Dict[str, float]] = None) -> NetworkVoltageAnalysis:
        """
        Analyze voltage drops across entire network
        
        Args:
            network: NetworkX graph with conductor attributes
            transformer_node: Source transformer node ID
            voltage_level: System voltage level
            load_profile: Optional dict of node_id -> load_kw, uses default if not provided
            
        Returns:
            Complete network voltage analysis
        """
        if transformer_node not in network:
            raise ValueError(f"Transformer node {transformer_node} not in network")
        
        source_voltage = voltage_level.value
        is_three_phase = voltage_level in [VoltageLevel.THREE_PHASE_11KV, VoltageLevel.LV_400V]
        
        # Build load profile if not provided
        if load_profile is None:
            load_profile = {}
            for node in network.nodes():
                node_data = network.nodes[node]
                # Check if it's a connection/customer node
                if node_data.get('node_type') == 'connection':
                    load_profile[node] = self.default_load_per_connection
                elif node_data.get('connections_count', 0) > 0:
                    # Pole with connections
                    load_profile[node] = node_data['connections_count'] * self.default_load_per_connection
        
        results = {}
        max_voltage_drop_percent = 0
        violations = []
        warnings = []
        
        # Calculate shortest paths from transformer to all nodes
        try:
            paths = nx.single_source_dijkstra_path(network, transformer_node, weight='length')
            distances = nx.single_source_dijkstra_path_length(network, transformer_node, weight='length')
        except nx.NetworkXNoPath as e:
            warnings.append(f"Network is disconnected: {e}")
            return NetworkVoltageAnalysis(
                source_voltage=source_voltage,
                voltage_level=voltage_level,
                max_voltage_drop_percent=0,
                threshold_percent=self.voltage_drop_threshold,
                violations=[],
                all_nodes={},
                is_valid=False,
                warnings=warnings
            )
        
        # Calculate voltage drop for each node
        for node in network.nodes():
            if node == transformer_node:
                # Transformer node has no voltage drop
                results[node] = VoltageDropResult(
                    node_id=node,
                    distance_km=0,
                    voltage_drop_v=0,
                    voltage_drop_percent=0,
                    final_voltage_v=source_voltage,
                    current_amps=0,
                    within_limits=True,
                    path_from_source=[node]
                )
                continue
            
            if node not in paths:
                warnings.append(f"Node {node} is not connected to transformer")
                continue
            
            path = paths[node]
            total_voltage_drop = 0
            accumulated_current = 0
            
            # Calculate accumulated load and voltage drop along path
            for i in range(len(path) - 1):
                from_node = path[i]
                to_node = path[i + 1]
                
                # Get edge data
                edge_data = network[from_node][to_node]
                length_km = edge_data.get('length', 0) / 1000  # Convert m to km
                conductor_type = edge_data.get('conductor_type', 'AAC_35')
                
                # Calculate current for this segment
                # Current accumulates from downstream nodes
                segment_load = sum(load_profile.get(n, 0) for n in nx.descendants(network, to_node))
                segment_load += load_profile.get(to_node, 0)
                
                segment_current = self.calculate_current(
                    segment_load, 
                    source_voltage,
                    is_three_phase=is_three_phase
                )
                
                # Calculate voltage drop for segment
                v_drop = self.calculate_voltage_drop(
                    length_km,
                    segment_current,
                    conductor_type,
                    is_three_phase
                )
                
                total_voltage_drop += v_drop
                accumulated_current = max(accumulated_current, segment_current)
            
            # Calculate percentage drop
            voltage_drop_percent = (total_voltage_drop / source_voltage) * 100
            final_voltage = source_voltage - total_voltage_drop
            within_limits = voltage_drop_percent <= self.voltage_drop_threshold
            
            result = VoltageDropResult(
                node_id=node,
                distance_km=distances.get(node, 0) / 1000,
                voltage_drop_v=total_voltage_drop,
                voltage_drop_percent=voltage_drop_percent,
                final_voltage_v=final_voltage,
                current_amps=accumulated_current,
                within_limits=within_limits,
                path_from_source=path
            )
            
            results[node] = result
            max_voltage_drop_percent = max(max_voltage_drop_percent, voltage_drop_percent)
            
            if not within_limits:
                violations.append(result)
        
        # Check for overloaded conductors
        for u, v, data in network.edges(data=True):
            conductor_type = data.get('conductor_type', 'AAC_35')
            if conductor_type in self.conductor_library:
                conductor = self.conductor_library[conductor_type]
                edge_current = results.get(v, VoltageDropResult(
                    node_id=v, distance_km=0, voltage_drop_v=0, 
                    voltage_drop_percent=0, final_voltage_v=0, 
                    current_amps=0, within_limits=True, path_from_source=[]
                )).current_amps
                
                if edge_current > conductor.current_rating_amps:
                    warnings.append(
                        f"Conductor {u}-{v} overloaded: {edge_current:.1f}A > {conductor.current_rating_amps}A rating"
                    )
        
        return NetworkVoltageAnalysis(
            source_voltage=source_voltage,
            voltage_level=voltage_level,
            max_voltage_drop_percent=max_voltage_drop_percent,
            threshold_percent=self.voltage_drop_threshold,
            violations=violations,
            all_nodes=results,
            is_valid=len(violations) == 0,
            warnings=warnings
        )
    
    def validate_design_change(self,
                              old_network: nx.Graph,
                              new_network: nx.Graph,
                              transformer_node: str,
                              voltage_level: VoltageLevel = VoltageLevel.THREE_PHASE_11KV) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate that a design change doesn't violate voltage constraints
        
        Args:
            old_network: Original network graph
            new_network: Modified network graph
            transformer_node: Source transformer node
            voltage_level: System voltage level
            
        Returns:
            Tuple of (is_valid, validation_report)
        """
        # Analyze new network
        new_analysis = self.analyze_network(new_network, transformer_node, voltage_level)
        
        # Compare with old if provided
        comparison = {}
        if old_network is not None and len(old_network) > 0:
            old_analysis = self.analyze_network(old_network, transformer_node, voltage_level)
            
            comparison = {
                'voltage_drop_change': new_analysis.max_voltage_drop_percent - old_analysis.max_voltage_drop_percent,
                'new_violations': len(new_analysis.violations) - len(old_analysis.violations),
                'previous_max_drop': old_analysis.max_voltage_drop_percent,
                'improved': new_analysis.max_voltage_drop_percent < old_analysis.max_voltage_drop_percent
            }
        
        validation_report = {
            'is_valid': new_analysis.is_valid,
            'max_voltage_drop': new_analysis.max_voltage_drop_percent,
            'threshold': self.voltage_drop_threshold,
            'violations_count': len(new_analysis.violations),
            'violations': [
                {
                    'node': v.node_id,
                    'voltage_drop': v.voltage_drop_percent,
                    'distance_km': v.distance_km
                }
                for v in new_analysis.violations[:10]  # Limit to first 10
            ],
            'warnings': new_analysis.warnings,
            'comparison': comparison
        }
        
        return new_analysis.is_valid, validation_report
