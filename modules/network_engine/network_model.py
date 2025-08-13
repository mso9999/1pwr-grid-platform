"""
Network Model
=============
Core network topology model using NetworkX.
Manages poles, conductors, transformers, and connections.
"""

import networkx as nx
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class NetworkStats:
    """Network statistics summary"""
    total_poles: int = 0
    total_conductors: int = 0
    total_connections: int = 0
    total_transformers: int = 0
    total_length_km: float = 0.0
    voltage_levels: Set[str] = field(default_factory=set)
    subnetworks: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class NetworkModel:
    """
    Network topology model using NetworkX directed graph.
    Nodes represent poles/transformers, edges represent conductors.
    """
    
    def __init__(self, network_id: str = "main"):
        """
        Initialize network model
        
        Args:
            network_id: Unique identifier for this network
        """
        self.network_id = network_id
        self.graph = nx.DiGraph()  # Directed for power flow
        self.metadata = {
            'created': datetime.now().isoformat(),
            'version': '1.0.0',
            'network_id': network_id
        }
        self.transformers = {}  # transformer_id -> node_id mapping
        self.connections = {}  # connection_id -> pole_id mapping
        self.subnetworks = set()
    
    def add_pole(self, pole_id: str, **attributes) -> None:
        """
        Add a pole to the network
        
        Args:
            pole_id: Unique pole identifier
            **attributes: Pole attributes (type, utm_x, utm_y, gps_lat, gps_lng, etc.)
        """
        self.graph.add_node(pole_id, node_type='pole', **attributes)
        
        if 'subnetwork' in attributes:
            self.subnetworks.add(attributes['subnetwork'])
    
    def add_transformer(self, transformer_id: str, pole_id: str, **attributes) -> None:
        """
        Add a transformer at a pole location
        
        Args:
            transformer_id: Unique transformer identifier
            pole_id: Pole where transformer is located
            **attributes: Transformer attributes (capacity_kva, primary_v, secondary_v, etc.)
        """
        if pole_id not in self.graph:
            raise ValueError(f"Pole {pole_id} not found in network")
        
        # Update pole attributes
        self.graph.nodes[pole_id]['has_transformer'] = True
        self.graph.nodes[pole_id]['transformer_id'] = transformer_id
        self.graph.nodes[pole_id]['transformer_capacity_kva'] = attributes.get('capacity_kva')
        
        # Store transformer mapping
        self.transformers[transformer_id] = {
            'pole_id': pole_id,
            **attributes
        }
    
    def add_conductor(self, from_pole: str, to_pole: str, **attributes) -> None:
        """
        Add a conductor between two poles
        
        Args:
            from_pole: Source pole ID
            to_pole: Destination pole ID
            **attributes: Conductor attributes (length, cable_size, conductor_type, etc.)
        """
        # Ensure both poles exist
        if from_pole not in self.graph:
            self.add_pole(from_pole)
        if to_pole not in self.graph:
            self.add_pole(to_pole)
        
        # Add directed edge (power flows from -> to)
        self.graph.add_edge(from_pole, to_pole, edge_type='conductor', **attributes)
    
    def add_connection(self, connection_id: str, pole_id: str, **attributes) -> None:
        """
        Add a customer connection to a pole
        
        Args:
            connection_id: Unique connection identifier
            pole_id: Pole where connection is made
            **attributes: Connection attributes (utm_x, utm_y, meter_serial, etc.)
        """
        if pole_id not in self.graph:
            raise ValueError(f"Pole {pole_id} not found in network")
        
        # Update pole connection count
        current_count = self.graph.nodes[pole_id].get('connections_count', 0)
        self.graph.nodes[pole_id]['connections_count'] = current_count + 1
        
        # Store connection mapping
        self.connections[connection_id] = {
            'pole_id': pole_id,
            **attributes
        }
    
    def import_from_dict(self, data: Dict[str, Any]) -> None:
        """
        Import network from dictionary (e.g., from Excel/Pickle importer)
        
        Args:
            data: Dictionary containing poles, conductors, connections, transformers
        """
        # Import poles
        if 'poles' in data:
            poles_data = data['poles']
            poles_list = poles_data.get('poles', []) if isinstance(poles_data, dict) else poles_data
            
            for pole in poles_list:
                self.add_pole(
                    pole_id=pole['pole_id'],
                    pole_type=pole.get('pole_type', 'standard'),
                    utm_x=pole.get('utm_x'),
                    utm_y=pole.get('utm_y'),
                    gps_lat=pole.get('gps_lat'),
                    gps_lng=pole.get('gps_lng'),
                    elevation=pole.get('elevation'),
                    subnetwork=pole.get('subnetwork', 'main'),
                    status=pole.get('status', 'as_designed')
                )
        
        # Import conductors
        if 'conductors' in data:
            conductors_data = data['conductors']
            conductors_list = conductors_data.get('conductors', []) if isinstance(conductors_data, dict) else conductors_data
            
            for conductor in conductors_list:
                self.add_conductor(
                    from_pole=conductor['from_pole'],
                    to_pole=conductor['to_pole'],
                    length=conductor.get('length_m', 0),
                    cable_size=conductor.get('cable_size'),
                    conductor_type=conductor.get('conductor_type', 'network'),
                    subnetwork=conductor.get('subnetwork', 'main'),
                    status=conductor.get('status', 'as_designed')
                )
        
        # Import network lines (for pickle format)
        if 'network_lines' in data:
            lines_data = data['network_lines']
            lines_list = lines_data.get('conductors', []) if isinstance(lines_data, dict) else lines_data
            
            for line in lines_list:
                self.add_conductor(
                    from_pole=line['from_pole'],
                    to_pole=line['to_pole'],
                    length=line.get('length_m', 0),
                    cable_size=line.get('cable_size'),
                    conductor_type='network',
                    status=line.get('status', 'as_designed')
                )
        
        # Import transformers
        if 'transformers' in data:
            transformers_data = data['transformers']
            transformers_list = transformers_data.get('transformers', []) if isinstance(transformers_data, dict) else transformers_data
            
            for transformer in transformers_list:
                if transformer.get('location_pole'):
                    self.add_transformer(
                        transformer_id=str(transformer.get('transformer_id', 'T1')),
                        pole_id=str(transformer['location_pole']),
                        capacity_kva=transformer.get('capacity_kva'),
                        primary_voltage=transformer.get('primary_voltage'),
                        secondary_voltage=transformer.get('secondary_voltage')
                    )
        
        # Import connections
        if 'connections' in data:
            connections_data = data['connections']
            connections_list = connections_data.get('connections', []) if isinstance(connections_data, dict) else connections_data
            
            # For connections, we need to find nearest pole or use drop line info
            for conn in connections_list:
                # This is simplified - in reality would need spatial matching
                # or use drop line data to find connected pole
                conn_id = conn.get('survey_id', conn.get('customer_id'))
                if conn_id:
                    # For now, store as orphan connection
                    self.connections[conn_id] = conn
        
        # Import customers (for pickle format)
        if 'customers' in data:
            customers_data = data['customers']
            customers_list = customers_data.get('customers', []) if isinstance(customers_data, dict) else customers_data
            
            for customer in customers_list:
                cust_id = customer.get('customer_id')
                if cust_id:
                    self.connections[cust_id] = customer
    
    def get_subnetwork(self, subnetwork_name: str) -> nx.DiGraph:
        """
        Extract a subnetwork by name
        
        Args:
            subnetwork_name: Name of subnetwork
            
        Returns:
            Subgraph containing only specified subnetwork
        """
        nodes = [n for n, d in self.graph.nodes(data=True) 
                if d.get('subnetwork') == subnetwork_name]
        return self.graph.subgraph(nodes)
    
    def get_transformer_nodes(self) -> List[str]:
        """
        Get all nodes that have transformers
        
        Returns:
            List of pole IDs with transformers
        """
        return [n for n, d in self.graph.nodes(data=True) 
               if d.get('has_transformer', False)]
    
    def get_stats(self) -> NetworkStats:
        """
        Calculate network statistics
        
        Returns:
            NetworkStats object with summary statistics
        """
        stats = NetworkStats()
        
        # Count nodes by type
        for node, data in self.graph.nodes(data=True):
            if data.get('node_type') == 'pole':
                stats.total_poles += 1
        
        # Count edges and calculate total length
        for u, v, data in self.graph.edges(data=True):
            if data.get('edge_type') == 'conductor':
                stats.total_conductors += 1
                length_m = data.get('length', 0)
                stats.total_length_km += length_m / 1000
        
        # Count transformers and connections
        stats.total_transformers = len(self.transformers)
        stats.total_connections = len(self.connections)
        
        # Get voltage levels from transformers
        for transformer in self.transformers.values():
            if 'primary_voltage' in transformer:
                stats.voltage_levels.add(f"{transformer['primary_voltage']}V")
            if 'secondary_voltage' in transformer:
                stats.voltage_levels.add(f"{transformer['secondary_voltage']}V")
        
        # Get subnetworks
        stats.subnetworks = list(self.subnetworks)
        
        return stats
    
    def validate_topology(self) -> Tuple[bool, List[str]]:
        """
        Validate network topology for common issues
        
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []
        
        # Check for disconnected components
        if not nx.is_weakly_connected(self.graph):
            num_components = nx.number_weakly_connected_components(self.graph)
            issues.append(f"Network has {num_components} disconnected components")
        
        # Check for cycles (distribution network should be radial)
        if not nx.is_directed_acyclic_graph(self.graph):
            cycles = list(nx.simple_cycles(self.graph))[:5]  # First 5 cycles
            issues.append(f"Network contains cycles: {cycles}")
        
        # Check for transformers
        transformer_nodes = self.get_transformer_nodes()
        if len(transformer_nodes) == 0:
            issues.append("No transformers found in network")
        
        # Check for orphan nodes (no edges)
        orphans = [n for n in self.graph.nodes() if self.graph.degree(n) == 0]
        if orphans:
            issues.append(f"Found {len(orphans)} orphan nodes: {orphans[:10]}")
        
        # Check for missing conductor attributes
        missing_length = []
        for u, v, data in self.graph.edges(data=True):
            if 'length' not in data or data['length'] == 0:
                missing_length.append((u, v))
        
        if missing_length:
            issues.append(f"Found {len(missing_length)} conductors with missing/zero length")
        
        return len(issues) == 0, issues
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Export network to dictionary format
        
        Returns:
            Dictionary representation of network
        """
        return {
            'metadata': self.metadata,
            'network_id': self.network_id,
            'nodes': [
                {'id': n, **data}
                for n, data in self.graph.nodes(data=True)
            ],
            'edges': [
                {'from': u, 'to': v, **data}
                for u, v, data in self.graph.edges(data=True)
            ],
            'transformers': self.transformers,
            'connections': self.connections,
            'stats': self.get_stats().__dict__
        }
    
    def to_geojson(self) -> Dict[str, Any]:
        """
        Export network to GeoJSON format for map visualization
        
        Returns:
            GeoJSON FeatureCollection
        """
        features = []
        
        # Add poles as Point features
        for node, data in self.graph.nodes(data=True):
            if data.get('gps_lat') and data.get('gps_lng'):
                feature = {
                    'type': 'Feature',
                    'geometry': {
                        'type': 'Point',
                        'coordinates': [data['gps_lng'], data['gps_lat']]
                    },
                    'properties': {
                        'id': node,
                        'type': 'pole',
                        'pole_type': data.get('pole_type'),
                        'has_transformer': data.get('has_transformer', False),
                        'connections_count': data.get('connections_count', 0)
                    }
                }
                features.append(feature)
        
        # Add conductors as LineString features
        for u, v, data in self.graph.edges(data=True):
            u_data = self.graph.nodes[u]
            v_data = self.graph.nodes[v]
            
            if (u_data.get('gps_lat') and u_data.get('gps_lng') and
                v_data.get('gps_lat') and v_data.get('gps_lng')):
                
                feature = {
                    'type': 'Feature',
                    'geometry': {
                        'type': 'LineString',
                        'coordinates': [
                            [u_data['gps_lng'], u_data['gps_lat']],
                            [v_data['gps_lng'], v_data['gps_lat']]
                        ]
                    },
                    'properties': {
                        'from': u,
                        'to': v,
                        'length_m': data.get('length'),
                        'cable_size': data.get('cable_size'),
                        'conductor_type': data.get('conductor_type')
                    }
                }
                features.append(feature)
        
        return {
            'type': 'FeatureCollection',
            'features': features,
            'metadata': self.metadata
        }
