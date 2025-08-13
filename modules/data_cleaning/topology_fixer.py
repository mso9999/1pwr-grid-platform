"""
Topology Fixer
==============
Fixes network topology issues to ensure radial distribution network.
"""

from typing import Dict, List, Any, Tuple, Set
import networkx as nx
import logging

logger = logging.getLogger(__name__)


class TopologyFixer:
    """Fixes network topology to ensure radial structure without loops"""
    
    def __init__(self):
        """Initialize topology fixer"""
        self.fixes_applied = {
            'cycles_removed': 0,
            'disconnected_components_connected': 0,
            'direction_fixed': 0,
            'orphaned_nodes_removed': 0
        }
    
    def fix_topology(
        self,
        poles: List[Dict],
        conductors: List[Dict],
        transformers: List[Dict]
    ) -> Tuple[List[Dict], List[Dict], Dict[str, Any]]:
        """
        Fix network topology issues
        
        Args:
            poles: List of pole dictionaries
            conductors: List of conductor dictionaries
            transformers: List of transformer dictionaries
            
        Returns:
            Tuple of (fixed_poles, fixed_conductors, fix_report)
        """
        logger.info("Starting topology fixing")
        
        # Build network graph
        G = self._build_graph(poles, conductors, transformers)
        
        # Step 1: Remove cycles to ensure radial topology
        G = self._remove_cycles(G, transformers)
        
        # Step 2: Connect disconnected components
        G = self._connect_components(G, transformers)
        
        # Step 3: Fix edge directions (from source to load)
        G = self._fix_directions(G, transformers)
        
        # Step 4: Remove orphaned nodes
        G = self._remove_orphaned_nodes(G)
        
        # Convert back to lists
        fixed_poles, fixed_conductors = self._graph_to_lists(G)
        
        report = {
            'fixes_applied': self.fixes_applied,
            'final_topology': {
                'is_radial': nx.is_directed_acyclic_graph(G),
                'is_connected': nx.is_weakly_connected(G),
                'num_components': nx.number_weakly_connected_components(G),
                'has_cycles': not nx.is_directed_acyclic_graph(G)
            }
        }
        
        logger.info(f"Topology fixing complete: {self.fixes_applied}")
        return fixed_poles, fixed_conductors, report
    
    def _build_graph(
        self,
        poles: List[Dict],
        conductors: List[Dict],
        transformers: List[Dict]
    ) -> nx.DiGraph:
        """Build NetworkX directed graph from data"""
        G = nx.DiGraph()
        
        # Add nodes (poles)
        for pole in poles:
            pole_id = pole.get('pole_id')
            if pole_id:
                G.add_node(
                    pole_id,
                    **{k: v for k, v in pole.items() if v is not None}
                )
        
        # Mark transformer nodes
        transformer_poles = {t['pole_id'] for t in transformers if 'pole_id' in t}
        for node in G.nodes():
            if node in transformer_poles:
                G.nodes[node]['is_transformer'] = True
        
        # Add edges (conductors)
        for conductor in conductors:
            from_pole = conductor.get('from_pole')
            to_pole = conductor.get('to_pole')
            
            if from_pole and to_pole and from_pole in G and to_pole in G:
                G.add_edge(
                    from_pole,
                    to_pole,
                    **{k: v for k, v in conductor.items() if v is not None}
                )
        
        return G
    
    def _remove_cycles(self, G: nx.DiGraph, transformers: List[Dict]) -> nx.DiGraph:
        """Remove cycles to create radial topology"""
        # Find all cycles
        try:
            cycles = list(nx.simple_cycles(G))
        except:
            cycles = []
        
        if not cycles:
            return G
        
        logger.info(f"Found {len(cycles)} cycles to remove")
        
        # For each cycle, remove the edge with lowest importance
        for cycle in cycles:
            if len(cycle) < 2:
                continue
            
            # Find edge to remove (prefer non-main feeders)
            edges_in_cycle = []
            for i in range(len(cycle)):
                u = cycle[i]
                v = cycle[(i + 1) % len(cycle)]
                if G.has_edge(u, v):
                    edge_data = G.edges[u, v]
                    importance = self._calculate_edge_importance(edge_data)
                    edges_in_cycle.append((u, v, importance))
            
            if edges_in_cycle:
                # Remove edge with lowest importance
                edges_in_cycle.sort(key=lambda x: x[2])
                u, v, _ = edges_in_cycle[0]
                G.remove_edge(u, v)
                self.fixes_applied['cycles_removed'] += 1
                logger.debug(f"Removed edge {u}->{v} to break cycle")
        
        return G
    
    def _calculate_edge_importance(self, edge_data: Dict) -> float:
        """Calculate importance score for an edge"""
        importance = 1.0
        
        # Main feeders are more important
        conductor_id = edge_data.get('conductor_id', '').lower()
        if 'm' in conductor_id or 'main' in conductor_id:
            importance *= 10
        
        # Longer lines might be main feeders
        length = edge_data.get('length', 0)
        if length > 1000:  # meters
            importance *= 2
        
        # Higher voltage/cable size indicates importance
        cable_size = edge_data.get('cable_size', '')
        # Convert to string if it's a number
        cable_size_str = str(cable_size) if cable_size else ''
        if '50' in cable_size_str:
            importance *= 3
        elif '35' in cable_size_str:
            importance *= 2
        
        return importance
    
    def _connect_components(
        self, G: nx.DiGraph, transformers: List[Dict]
    ) -> nx.DiGraph:
        """Connect disconnected components to main network"""
        components = list(nx.weakly_connected_components(G))
        
        if len(components) <= 1:
            return G
        
        logger.info(f"Found {len(components)} disconnected components")
        
        # Find main component (one with transformers or largest)
        transformer_poles = {t['pole_id'] for t in transformers if 'pole_id' in t}
        
        main_component = None
        for comp in components:
            if any(node in transformer_poles for node in comp):
                main_component = comp
                break
        
        if not main_component:
            # Use largest component as main
            main_component = max(components, key=len)
        
        # Connect other components to main
        for comp in components:
            if comp == main_component:
                continue
            
            # Find closest nodes between components
            min_dist = float('inf')
            best_connection = None
            
            for node1 in main_component:
                if 'latitude' not in G.nodes[node1]:
                    continue
                    
                for node2 in comp:
                    if 'latitude' not in G.nodes[node2]:
                        continue
                    
                    dist = self._calculate_distance(
                        G.nodes[node1], G.nodes[node2]
                    )
                    
                    if dist < min_dist:
                        min_dist = dist
                        best_connection = (node1, node2)
            
            # Add connection
            if best_connection:
                u, v = best_connection
                G.add_edge(u, v, 
                    conductor_id=f"CONN_{u}_{v}",
                    length=min_dist,
                    cable_size='AAC_35',
                    auto_connected=True
                )
                self.fixes_applied['disconnected_components_connected'] += 1
                logger.debug(f"Connected component at {v} to main network at {u}")
        
        return G
    
    def _calculate_distance(self, node1_data: Dict, node2_data: Dict) -> float:
        """Calculate distance between two nodes"""
        import math
        
        # Try UTM first (more accurate for short distances)
        if 'utm_x' in node1_data and 'utm_x' in node2_data:
            dx = node1_data['utm_x'] - node2_data['utm_x']
            dy = node1_data['utm_y'] - node2_data['utm_y']
            return math.sqrt(dx*dx + dy*dy)
        
        # Fall back to lat/lon
        if 'latitude' in node1_data and 'latitude' in node2_data:
            lat1 = node1_data['latitude']
            lon1 = node1_data['longitude']
            lat2 = node2_data['latitude']
            lon2 = node2_data['longitude']
            
            # Simple Euclidean approximation (good enough for short distances)
            dx = (lon2 - lon1) * 111000 * math.cos(math.radians(lat1))
            dy = (lat2 - lat1) * 111000
            return math.sqrt(dx*dx + dy*dy)
        
        return float('inf')
    
    def _fix_directions(self, G: nx.DiGraph, transformers: List[Dict]) -> nx.DiGraph:
        """Fix edge directions to flow from source (transformer) to loads"""
        transformer_poles = {t['pole_id'] for t in transformers if 'pole_id' in t}
        
        if not transformer_poles:
            # No transformers, can't determine flow direction
            return G
        
        # BFS from each transformer to determine correct directions
        for tx_pole in transformer_poles:
            if tx_pole not in G:
                continue
            
            # Get subgraph reachable from this transformer
            reachable = nx.single_source_shortest_path(G.to_undirected(), tx_pole)
            
            # Build directed tree from transformer
            for target in reachable:
                if target == tx_pole:
                    continue
                
                path = reachable[target]
                for i in range(len(path) - 1):
                    u, v = path[i], path[i + 1]
                    
                    # Ensure edge goes in correct direction
                    if G.has_edge(v, u) and not G.has_edge(u, v):
                        # Reverse the edge
                        edge_data = G.edges[v, u].copy()
                        G.remove_edge(v, u)
                        G.add_edge(u, v, **edge_data)
                        self.fixes_applied['direction_fixed'] += 1
                        logger.debug(f"Reversed edge direction: {v}->{u} to {u}->{v}")
        
        return G
    
    def _remove_orphaned_nodes(self, G: nx.DiGraph) -> nx.DiGraph:
        """Remove nodes with no connections"""
        orphans = [
            node for node in G.nodes()
            if G.in_degree(node) == 0 and G.out_degree(node) == 0
        ]
        
        for node in orphans:
            G.remove_node(node)
            self.fixes_applied['orphaned_nodes_removed'] += 1
            logger.debug(f"Removed orphaned node: {node}")
        
        return G
    
    def _graph_to_lists(
        self, G: nx.DiGraph
    ) -> Tuple[List[Dict], List[Dict]]:
        """Convert graph back to pole and conductor lists"""
        poles = []
        for node, data in G.nodes(data=True):
            pole_dict = data.copy()
            pole_dict['pole_id'] = node
            poles.append(pole_dict)
        
        conductors = []
        for u, v, data in G.edges(data=True):
            conductor_dict = data.copy()
            conductor_dict['from_pole'] = u
            conductor_dict['to_pole'] = v
            if 'conductor_id' not in conductor_dict:
                conductor_dict['conductor_id'] = f"{u}-{v}"
            conductors.append(conductor_dict)
        
        return poles, conductors
