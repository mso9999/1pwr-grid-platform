"""
Network Validator
=================
Validates network topology and electrical constraints.
"""

from typing import Dict, List, Tuple, Any, Optional
import networkx as nx
import logging

logger = logging.getLogger(__name__)


class NetworkValidator:
    """Validates network topology and electrical constraints"""
    
    def __init__(self):
        """Initialize network validator"""
        self.validation_rules = []
        self.errors = []
        self.warnings = []
    
    def validate_network(self, graph: nx.Graph) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate network graph
        
        Args:
            graph: NetworkX graph to validate
            
        Returns:
            Tuple of (is_valid, validation_report)
        """
        self.errors = []
        self.warnings = []
        
        # Run validation checks
        self._check_connectivity(graph)
        self._check_radial_topology(graph)
        self._check_transformer_presence(graph)
        self._check_edge_attributes(graph)
        
        is_valid = len(self.errors) == 0
        
        return is_valid, {
            'is_valid': is_valid,
            'errors': self.errors,
            'warnings': self.warnings,
            'node_count': graph.number_of_nodes(),
            'edge_count': graph.number_of_edges()
        }
    
    def _check_connectivity(self, graph: nx.Graph) -> None:
        """Check if network is connected"""
        if not nx.is_weakly_connected(graph):
            components = list(nx.weakly_connected_components(graph))
            self.errors.append(f"Network has {len(components)} disconnected components")
    
    def _check_radial_topology(self, graph: nx.Graph) -> None:
        """Check if network has radial topology (no cycles)"""
        if not nx.is_directed_acyclic_graph(graph):
            self.warnings.append("Network contains cycles (not radial)")
    
    def _check_transformer_presence(self, graph: nx.Graph) -> None:
        """Check for at least one transformer"""
        has_transformer = any(
            data.get('has_transformer', False) 
            for node, data in graph.nodes(data=True)
        )
        if not has_transformer:
            self.errors.append("No transformer found in network")
    
    def _check_edge_attributes(self, graph: nx.Graph) -> None:
        """Check edge attributes are complete"""
        for u, v, data in graph.edges(data=True):
            if 'length' not in data:
                self.warnings.append(f"Edge {u}-{v} missing length attribute")
            elif data['length'] <= 0:
                self.errors.append(f"Edge {u}-{v} has invalid length: {data['length']}")
