"""
Transformer Detector
====================
Automatically detects and identifies transformer locations in the network.
"""

from typing import Dict, List, Any, Optional, Tuple
import logging
import re

logger = logging.getLogger(__name__)


class TransformerDetector:
    """Detects transformer locations based on network patterns and naming conventions"""
    
    def __init__(self):
        """Initialize transformer detector"""
        self.transformer_patterns = [
            r'[Tt]rans',
            r'[Tt]x',
            r'[Ss]tep[- _]?[Uu]p',
            r'[Ss]tep[- _]?[Dd]own',
            r'[Ss]ubstation',
            r'[Gg]en[- _]?[Ss]ite',
            r'[Pp]ower[- _]?[Hh]ouse',
            r'[Ss]ource',
            r'M1$',  # Common pattern in data (e.g., KET_28_M1)
        ]
        
        self.voltage_level_patterns = {
            'high': [r'19[kK][Vv]', r'11[kK][Vv]', r'33[kK][Vv]'],
            'medium': [r'11[kK][Vv]', r'6\.6[kK][Vv]'],
            'low': [r'400[Vv]', r'230[Vv]', r'415[Vv]']
        }
    
    def detect_transformers(
        self, poles: List[Dict], conductors: List[Dict]
    ) -> List[Dict[str, Any]]:
        """
        Detect transformer locations in the network
        
        Args:
            poles: List of pole dictionaries
            conductors: List of conductor dictionaries
            
        Returns:
            List of detected transformer dictionaries
        """
        logger.info("Starting transformer detection")
        
        transformers = []
        
        # Method 1: Pattern-based detection from pole names
        pattern_transformers = self._detect_by_patterns(poles)
        transformers.extend(pattern_transformers)
        
        # Method 2: Network topology detection (high connectivity nodes)
        topology_transformers = self._detect_by_topology(poles, conductors)
        transformers.extend(topology_transformers)
        
        # Method 3: Subnetwork root detection
        subnetwork_transformers = self._detect_subnetwork_roots(poles, conductors)
        transformers.extend(subnetwork_transformers)
        
        # Deduplicate and merge
        transformers = self._deduplicate_transformers(transformers)
        
        logger.info(f"Detected {len(transformers)} transformers")
        return transformers
    
    def _detect_by_patterns(self, poles: List[Dict]) -> List[Dict]:
        """Detect transformers based on naming patterns"""
        transformers = []
        
        for pole in poles:
            pole_name = pole.get('pole_name', '')
            pole_id = pole.get('pole_id', '')
            
            # Check against patterns
            for pattern in self.transformer_patterns:
                if re.search(pattern, pole_name, re.IGNORECASE) or \
                   re.search(pattern, pole_id, re.IGNORECASE):
                    
                    transformer = self._create_transformer(
                        pole=pole,
                        detection_method='pattern',
                        confidence=0.8
                    )
                    transformers.append(transformer)
                    logger.debug(f"Pattern-detected transformer at {pole_id}")
                    break
        
        return transformers
    
    def _detect_by_topology(
        self, poles: List[Dict], conductors: List[Dict]
    ) -> List[Dict]:
        """Detect transformers based on network topology (high connectivity)"""
        transformers = []
        
        # Count connections per pole
        connection_count = {}
        for conductor in conductors:
            from_pole = conductor.get('from_pole')
            to_pole = conductor.get('to_pole')
            
            connection_count[from_pole] = connection_count.get(from_pole, 0) + 1
            connection_count[to_pole] = connection_count.get(to_pole, 0) + 1
        
        # Find poles with high connectivity (likely transformers or junction points)
        avg_connections = sum(connection_count.values()) / len(connection_count) if connection_count else 0
        threshold = max(avg_connections * 2, 4)  # At least 4 connections or 2x average
        
        pole_dict = {p['pole_id']: p for p in poles if 'pole_id' in p}
        
        for pole_id, count in connection_count.items():
            if count >= threshold and pole_id in pole_dict:
                pole = pole_dict[pole_id]
                
                # Additional check: is this a source node (no incoming)?
                has_incoming = any(
                    c.get('to_pole') == pole_id 
                    for c in conductors
                )
                
                confidence = 0.6 if has_incoming else 0.9
                
                transformer = self._create_transformer(
                    pole=pole,
                    detection_method='topology',
                    confidence=confidence,
                    connection_count=count
                )
                transformers.append(transformer)
                logger.debug(f"Topology-detected transformer at {pole_id} (connections: {count})")
        
        return transformers
    
    def _detect_subnetwork_roots(
        self, poles: List[Dict], conductors: List[Dict]
    ) -> List[Dict]:
        """Detect transformers as roots of subnetworks"""
        transformers = []
        
        # Build adjacency for each subnetwork
        subnetworks = {}
        pole_dict = {p['pole_id']: p for p in poles if 'pole_id' in p}
        
        for pole in poles:
            site_name = pole.get('site_name', '')
            if site_name:
                if site_name not in subnetworks:
                    subnetworks[site_name] = {
                        'poles': [],
                        'conductors': []
                    }
                subnetworks[site_name]['poles'].append(pole)
        
        for conductor in conductors:
            # Determine subnetwork from pole names
            from_pole = conductor.get('from_pole', '')
            site_match = re.match(r'^([A-Z]+)_', from_pole)
            if site_match:
                site_name = site_match.group(1)
                if site_name in subnetworks:
                    subnetworks[site_name]['conductors'].append(conductor)
        
        # Find root of each subnetwork
        for site_name, network_data in subnetworks.items():
            root = self._find_network_root(
                network_data['poles'],
                network_data['conductors']
            )
            
            if root and root in pole_dict:
                pole = pole_dict[root]
                transformer = self._create_transformer(
                    pole=pole,
                    detection_method='subnetwork_root',
                    confidence=0.7,
                    site_name=site_name
                )
                transformers.append(transformer)
                logger.debug(f"Subnetwork-root transformer at {root} for site {site_name}")
        
        return transformers
    
    def _find_network_root(
        self, poles: List[Dict], conductors: List[Dict]
    ) -> Optional[str]:
        """Find the root node of a network (node with no incoming edges)"""
        pole_ids = {p['pole_id'] for p in poles if 'pole_id' in p}
        
        # Find poles that have outgoing but no incoming
        has_incoming = set()
        has_outgoing = set()
        
        for conductor in conductors:
            from_pole = conductor.get('from_pole')
            to_pole = conductor.get('to_pole')
            
            if to_pole in pole_ids:
                has_incoming.add(to_pole)
            if from_pole in pole_ids:
                has_outgoing.add(from_pole)
        
        # Root nodes have outgoing but no incoming
        roots = has_outgoing - has_incoming
        
        if len(roots) == 1:
            return roots.pop()
        elif len(roots) > 1:
            # Multiple potential roots, pick the one with pattern match
            for root in roots:
                for pattern in self.transformer_patterns:
                    if re.search(pattern, root, re.IGNORECASE):
                        return root
            # Otherwise return first
            return sorted(roots)[0]
        
        return None
    
    def _create_transformer(
        self,
        pole: Dict,
        detection_method: str,
        confidence: float,
        **kwargs
    ) -> Dict[str, Any]:
        """Create transformer dictionary from pole data"""
        
        # Determine voltage levels based on context
        voltage_high = 19000  # Default 19kV SWER
        voltage_low = 400  # Default 400V
        
        # Check for voltage indicators in name
        pole_name = pole.get('pole_name', '')
        if '11kV' in pole_name or '11KV' in pole_name:
            voltage_high = 11000
        elif '33kV' in pole_name or '33KV' in pole_name:
            voltage_high = 33000
        
        return {
            'transformer_id': f"TX_{pole.get('pole_id', '')}",
            'pole_id': pole.get('pole_id'),
            'pole_name': pole.get('pole_name'),
            'latitude': pole.get('latitude'),
            'longitude': pole.get('longitude'),
            'utm_x': pole.get('utm_x'),
            'utm_y': pole.get('utm_y'),
            'rating_kva': 100,  # Default rating, should be configurable
            'voltage_high': voltage_high,
            'voltage_low': voltage_low,
            'type': 'distribution',
            'detection_method': detection_method,
            'confidence': confidence,
            **kwargs
        }
    
    def _deduplicate_transformers(self, transformers: List[Dict]) -> List[Dict]:
        """Remove duplicate transformer detections"""
        unique = {}
        
        for transformer in transformers:
            pole_id = transformer.get('pole_id')
            
            if pole_id not in unique:
                unique[pole_id] = transformer
            else:
                # Keep the one with higher confidence
                if transformer.get('confidence', 0) > unique[pole_id].get('confidence', 0):
                    unique[pole_id] = transformer
        
        return list(unique.values())
    
    def add_transformers_to_data(
        self,
        data: Dict[str, Any],
        detected_transformers: List[Dict]
    ) -> Dict[str, Any]:
        """
        Add detected transformers to the data structure
        
        Args:
            data: Original data dictionary
            detected_transformers: List of detected transformers
            
        Returns:
            Updated data dictionary with transformers
        """
        data['transformers'] = detected_transformers
        
        # Also mark transformer poles
        transformer_poles = {t['pole_id'] for t in detected_transformers}
        
        for pole in data.get('poles', []):
            if pole.get('pole_id') in transformer_poles:
                pole['has_transformer'] = True
        
        return data
