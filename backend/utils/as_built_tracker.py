"""
As-built tracking utilities for comparing planned vs actual construction
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import math
from collections import defaultdict

from models.as_built import (
    AsBuiltPole, AsBuiltConnection, AsBuiltConductor, 
    AsBuiltSnapshot, AsBuiltComparison, AsBuiltStatus
)

class AsBuiltTracker:
    """Track and compare as-built vs planned network data"""
    
    def __init__(self, planned_data: Dict[str, Any]):
        """Initialize with planned network data"""
        self.planned_poles = {p['pole_id']: p for p in planned_data.get('poles', [])}
        self.planned_connections = {c.get('connection_id', c.get('survey_id')): c 
                                   for c in planned_data.get('connections', [])}
        self.planned_conductors = {c['conductor_id']: c for c in planned_data.get('conductors', [])}
        self.planned_transformers = {t.get('transformer_id'): t 
                                    for t in planned_data.get('transformers', [])}
    
    def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points in meters using Haversine formula"""
        R = 6371000  # Earth radius in meters
        
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)
        
        a = math.sin(delta_phi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    def match_pole(self, as_built_pole: AsBuiltPole, threshold_meters: float = 10) -> Tuple[Optional[str], float]:
        """
        Find matching planned pole within threshold distance
        Returns (pole_id, distance) or (None, 0) if no match
        """
        best_match = None
        min_distance = float('inf')
        
        for pole_id, planned in self.planned_poles.items():
            distance = self.calculate_distance(
                as_built_pole.latitude, as_built_pole.longitude,
                planned['latitude'], planned['longitude']
            )
            if distance < min_distance and distance <= threshold_meters:
                min_distance = distance
                best_match = pole_id
        
        return (best_match, min_distance) if best_match else (None, 0)
    
    def match_connection(self, as_built_conn: AsBuiltConnection, threshold_meters: float = 10) -> Tuple[Optional[str], float]:
        """Find matching planned connection within threshold distance"""
        best_match = None
        min_distance = float('inf')
        
        for conn_id, planned in self.planned_connections.items():
            distance = self.calculate_distance(
                as_built_conn.latitude, as_built_conn.longitude,
                planned['latitude'], planned['longitude']
            )
            if distance < min_distance and distance <= threshold_meters:
                min_distance = distance
                best_match = conn_id
        
        return (best_match, min_distance) if best_match else (None, 0)
    
    def process_as_built_snapshot(self, snapshot: AsBuiltSnapshot, 
                                 matching_threshold: float = 10) -> AsBuiltComparison:
        """
        Process as-built snapshot and compare with planned data
        Returns comparison report
        """
        comparison = AsBuiltComparison(
            site=snapshot.site,
            comparison_date=datetime.utcnow()
        )
        
        # Track matched items to find removed ones
        matched_poles = set()
        matched_connections = set()
        matched_conductors = set()
        
        # Process poles
        for as_built_pole in snapshot.poles:
            pole_match, distance = self.match_pole(as_built_pole, matching_threshold)
            
            if pole_match:
                matched_poles.add(pole_match)
                planned = self.planned_poles[pole_match]
                
                # Check if modified
                if distance > 1 or as_built_pole.pole_type != planned.get('pole_type'):
                    as_built_pole.status = AsBuiltStatus.MODIFIED
                    as_built_pole.deviation_distance = distance
                    comparison.poles_modified += 1
                    comparison.pole_differences.append({
                        'pole_id': pole_match,
                        'type': 'modified',
                        'deviation_m': distance,
                        'planned_location': [planned['latitude'], planned['longitude']],
                        'actual_location': [as_built_pole.latitude, as_built_pole.longitude]
                    })
                else:
                    as_built_pole.status = AsBuiltStatus.AS_PLANNED
                    comparison.poles_built += 1
            else:
                # New pole not in plan
                as_built_pole.status = AsBuiltStatus.ADDED
                comparison.poles_added += 1
                comparison.pole_differences.append({
                    'pole_id': as_built_pole.pole_id,
                    'type': 'added',
                    'location': [as_built_pole.latitude, as_built_pole.longitude]
                })
        
        # Process connections
        for as_built_conn in snapshot.connections:
            conn_match, distance = self.match_connection(as_built_conn, matching_threshold)
            
            if conn_match:
                matched_connections.add(conn_match)
                planned = self.planned_connections[conn_match]
                
                if distance > 1:
                    as_built_conn.status = AsBuiltStatus.MODIFIED
                    as_built_conn.deviation_distance = distance
                    comparison.connections_modified += 1
                    comparison.connection_differences.append({
                        'connection_id': conn_match,
                        'type': 'modified',
                        'deviation_m': distance,
                        'planned_location': [planned['latitude'], planned['longitude']],
                        'actual_location': [as_built_conn.latitude, as_built_conn.longitude]
                    })
                else:
                    as_built_conn.status = AsBuiltStatus.AS_PLANNED
                    comparison.connections_built += 1
            else:
                as_built_conn.status = AsBuiltStatus.ADDED
                comparison.connections_added += 1
                comparison.connection_differences.append({
                    'connection_id': as_built_conn.connection_id,
                    'type': 'added',
                    'location': [as_built_conn.latitude, as_built_conn.longitude]
                })
        
        # Process conductors
        built_length = 0
        for as_built_cond in snapshot.conductors:
            if as_built_cond.conductor_id in self.planned_conductors:
                matched_conductors.add(as_built_cond.conductor_id)
                planned = self.planned_conductors[as_built_cond.conductor_id]
                
                # Check if endpoints changed
                if (as_built_cond.from_pole != planned['from_pole'] or 
                    as_built_cond.to_pole != planned['to_pole']):
                    as_built_cond.status = AsBuiltStatus.MODIFIED
                    comparison.conductors_modified += 1
                    comparison.conductor_differences.append({
                        'conductor_id': as_built_cond.conductor_id,
                        'type': 'modified',
                        'planned_endpoints': [planned['from_pole'], planned['to_pole']],
                        'actual_endpoints': [as_built_cond.from_pole, as_built_cond.to_pole]
                    })
                else:
                    as_built_cond.status = AsBuiltStatus.AS_PLANNED
                    comparison.conductors_built += 1
                
                built_length += as_built_cond.actual_length or planned.get('length', 0)
            else:
                as_built_cond.status = AsBuiltStatus.ADDED
                comparison.conductors_added += 1
                comparison.conductor_differences.append({
                    'conductor_id': as_built_cond.conductor_id,
                    'type': 'added',
                    'endpoints': [as_built_cond.from_pole, as_built_cond.to_pole]
                })
                built_length += as_built_cond.actual_length or 0
        
        # Find removed items (in plan but not built)
        for pole_id in self.planned_poles:
            if pole_id not in matched_poles:
                comparison.poles_removed += 1
                planned = self.planned_poles[pole_id]
                comparison.pole_differences.append({
                    'pole_id': pole_id,
                    'type': 'removed',
                    'location': [planned['latitude'], planned['longitude']]
                })
        
        for conn_id in self.planned_connections:
            if conn_id not in matched_connections:
                comparison.connections_removed += 1
                planned = self.planned_connections[conn_id]
                comparison.connection_differences.append({
                    'connection_id': conn_id,
                    'type': 'removed',
                    'location': [planned['latitude'], planned['longitude']]
                })
        
        for cond_id in self.planned_conductors:
            if cond_id not in matched_conductors:
                comparison.conductors_removed += 1
                planned = self.planned_conductors[cond_id]
                comparison.conductor_differences.append({
                    'conductor_id': cond_id,
                    'type': 'removed',
                    'endpoints': [planned['from_pole'], planned['to_pole']]
                })
        
        # Set totals
        comparison.poles_planned = len(self.planned_poles)
        comparison.conductors_planned = len(self.planned_conductors)
        comparison.connections_planned = len(self.planned_connections)
        
        # Calculate lengths
        comparison.planned_length_km = sum(c.get('length', 0) for c in self.planned_conductors.values()) / 1000
        comparison.built_length_km = built_length / 1000
        
        # Calculate progress percentages
        if comparison.poles_planned > 0:
            comparison.pole_progress = (comparison.poles_built / comparison.poles_planned) * 100
        
        if comparison.conductors_planned > 0:
            comparison.conductor_progress = (comparison.conductors_built / comparison.conductors_planned) * 100
        
        if comparison.connections_planned > 0:
            comparison.connection_progress = (comparison.connections_built / comparison.connections_planned) * 100
        
        # Overall progress (weighted average)
        total_planned = comparison.poles_planned + comparison.conductors_planned + comparison.connections_planned
        total_built = comparison.poles_built + comparison.conductors_built + comparison.connections_built
        if total_planned > 0:
            comparison.overall_progress = (total_built / total_planned) * 100
        
        return comparison
    
    def generate_progress_report(self, comparison: AsBuiltComparison) -> Dict[str, Any]:
        """Generate a progress report from comparison"""
        return {
            'site': comparison.site,
            'report_date': comparison.comparison_date.isoformat(),
            'overall_progress': round(comparison.overall_progress, 1),
            'summary': {
                'poles': {
                    'planned': comparison.poles_planned,
                    'built': comparison.poles_built,
                    'modified': comparison.poles_modified,
                    'added': comparison.poles_added,
                    'removed': comparison.poles_removed,
                    'progress': round(comparison.pole_progress, 1)
                },
                'conductors': {
                    'planned': comparison.conductors_planned,
                    'built': comparison.conductors_built,
                    'modified': comparison.conductors_modified,
                    'added': comparison.conductors_added,
                    'removed': comparison.conductors_removed,
                    'progress': round(comparison.conductor_progress, 1),
                    'planned_km': round(comparison.planned_length_km, 2),
                    'built_km': round(comparison.built_length_km, 2)
                },
                'connections': {
                    'planned': comparison.connections_planned,
                    'built': comparison.connections_built,
                    'modified': comparison.connections_modified,
                    'added': comparison.connections_added,
                    'removed': comparison.connections_removed,
                    'progress': round(comparison.connection_progress, 1)
                }
            },
            'changes': {
                'poles': comparison.pole_differences[:10],  # Top 10 changes
                'conductors': comparison.conductor_differences[:10],
                'connections': comparison.connection_differences[:10]
            }
        }
