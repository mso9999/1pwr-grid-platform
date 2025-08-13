"""
Data Cleaner
============
Main data cleaning coordinator for imported network data.
"""

from typing import Dict, List, Any, Tuple
import logging
import re

logger = logging.getLogger(__name__)


class DataCleaner:
    """Cleans and fixes common data issues in imported network data"""
    
    def __init__(self):
        """Initialize data cleaner"""
        self.cleaning_stats = {
            'invalid_references_fixed': 0,
            'missing_cable_sizes_filled': 0,
            'duplicate_poles_removed': 0,
            'orphaned_connections_removed': 0,
            'coordinates_fixed': 0
        }
    
    def clean_data(self, data: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Clean imported data
        
        Args:
            data: Dictionary with poles, conductors, connections, transformers, etc.
            
        Returns:
            Tuple of (cleaned_data, cleaning_report)
        """
        logger.info("Starting data cleaning process")
        
        # Create a copy to avoid modifying original
        cleaned = {
            'poles': data.get('poles', []).copy(),
            'conductors': data.get('conductors', []).copy(),
            'connections': data.get('connections', []).copy(),
            'transformers': data.get('transformers', []).copy()
        }
        
        # Step 1: Build pole reference index
        pole_refs = self._build_pole_index(cleaned['poles'])
        
        # Step 2: Fix invalid pole references in conductors
        cleaned['conductors'] = self._fix_conductor_references(
            cleaned['conductors'], pole_refs
        )
        
        # Step 3: Fill missing cable sizes
        cleaned['conductors'] = self._fill_missing_cable_sizes(cleaned['conductors'])
        
        # Step 4: Remove duplicate poles
        cleaned['poles'] = self._remove_duplicate_poles(cleaned['poles'])
        
        # Step 5: Clean orphaned connections
        cleaned['connections'] = self._clean_orphaned_connections(
            cleaned['connections'], pole_refs
        )
        
        # Step 6: Fix coordinate issues
        cleaned['poles'] = self._fix_coordinates(cleaned['poles'])
        
        report = {
            'cleaning_stats': self.cleaning_stats,
            'data_summary': {
                'poles_count': len(cleaned['poles']),
                'conductors_count': len(cleaned['conductors']),
                'connections_count': len(cleaned['connections']),
                'transformers_count': len(cleaned['transformers'])
            }
        }
        
        logger.info(f"Data cleaning complete: {self.cleaning_stats}")
        return cleaned, report
    
    def _build_pole_index(self, poles: List[Dict]) -> Dict[str, str]:
        """Build index of valid pole references"""
        pole_refs = {}
        for pole in poles:
            # Store both ID and name as valid references
            if 'pole_id' in pole:
                pole_refs[pole['pole_id']] = pole['pole_id']
            if 'pole_name' in pole:
                pole_refs[pole['pole_name']] = pole['pole_id']
                # Also handle variations (with/without spaces)
                pole_refs[pole['pole_name'].replace(' ', '')] = pole['pole_id']
                pole_refs[pole['pole_name'].replace('_', ' ')] = pole['pole_id']
        return pole_refs
    
    def _fix_conductor_references(
        self, conductors: List[Dict], pole_refs: Dict[str, str]
    ) -> List[Dict]:
        """Fix invalid pole references in conductors"""
        fixed_conductors = []
        
        for conductor in conductors:
            from_pole = conductor.get('from_pole', '')
            to_pole = conductor.get('to_pole', '')
            
            # Try to fix references
            fixed_from = self._find_closest_match(from_pole, pole_refs)
            fixed_to = self._find_closest_match(to_pole, pole_refs)
            
            if fixed_from and fixed_to:
                conductor['from_pole'] = fixed_from
                conductor['to_pole'] = fixed_to
                fixed_conductors.append(conductor)
                
                if fixed_from != from_pole or fixed_to != to_pole:
                    self.cleaning_stats['invalid_references_fixed'] += 1
                    logger.debug(f"Fixed conductor reference: {from_pole}->{to_pole} to {fixed_from}->{fixed_to}")
            else:
                # Skip conductors with unfixable references
                logger.warning(f"Skipping conductor with invalid references: {from_pole} -> {to_pole}")
        
        return fixed_conductors
    
    def _find_closest_match(self, reference: str, valid_refs: Dict[str, str]) -> str:
        """Find closest matching pole reference"""
        if reference in valid_refs:
            return valid_refs[reference]
        
        # Try variations
        variations = [
            reference.replace(' ', ''),
            reference.replace('_', ' '),
            reference.upper(),
            reference.replace('HH1', ''),  # Common suffix in data
            reference.replace('HHSME', ''),
            reference.replace('KET ', 'KET_'),  # Site prefix variations
        ]
        
        for variant in variations:
            if variant in valid_refs:
                return valid_refs[variant]
        
        # Try fuzzy matching for close matches
        reference_clean = re.sub(r'[^A-Z0-9]', '', reference.upper())
        for valid_ref in valid_refs:
            valid_clean = re.sub(r'[^A-Z0-9]', '', valid_ref.upper())
            if reference_clean == valid_clean:
                return valid_refs[valid_ref]
        
        return None
    
    def _fill_missing_cable_sizes(self, conductors: List[Dict]) -> List[Dict]:
        """Fill missing cable sizes with defaults based on context"""
        default_sizes = {
            'main': 'AAC_50',  # Main feeder
            'branch': 'AAC_35',  # Branch lines
            'drop': 'ABC_16',  # Drop lines to customers
        }
        
        for conductor in conductors:
            if not conductor.get('cable_size'):
                # Determine type based on naming or connections
                cond_id = conductor.get('conductor_id', '').lower()
                
                if 'drop' in cond_id or 'hh' in cond_id:
                    conductor['cable_size'] = default_sizes['drop']
                elif 'm' in cond_id or 'main' in cond_id:
                    conductor['cable_size'] = default_sizes['main']
                else:
                    conductor['cable_size'] = default_sizes['branch']
                
                self.cleaning_stats['missing_cable_sizes_filled'] += 1
                logger.debug(f"Filled cable size for {conductor.get('conductor_id')}: {conductor['cable_size']}")
        
        return conductors
    
    def _remove_duplicate_poles(self, poles: List[Dict]) -> List[Dict]:
        """Remove duplicate poles based on ID or coordinates"""
        seen_ids = set()
        seen_coords = set()
        unique_poles = []
        
        for pole in poles:
            pole_id = pole.get('pole_id')
            coords = (pole.get('latitude'), pole.get('longitude'))
            
            # Check for duplicates
            if pole_id in seen_ids:
                self.cleaning_stats['duplicate_poles_removed'] += 1
                logger.debug(f"Removing duplicate pole: {pole_id}")
                continue
            
            if coords != (None, None) and coords in seen_coords:
                self.cleaning_stats['duplicate_poles_removed'] += 1
                logger.debug(f"Removing pole with duplicate coordinates: {pole_id} at {coords}")
                continue
            
            seen_ids.add(pole_id)
            if coords != (None, None):
                seen_coords.add(coords)
            unique_poles.append(pole)
        
        return unique_poles
    
    def _clean_orphaned_connections(
        self, connections: List[Dict], pole_refs: Dict[str, str]
    ) -> List[Dict]:
        """Remove connections to non-existent poles"""
        valid_connections = []
        
        for connection in connections:
            pole_id = connection.get('pole_id')
            
            # Try to fix reference
            fixed_pole = self._find_closest_match(pole_id, pole_refs) if pole_id else None
            
            if fixed_pole:
                connection['pole_id'] = fixed_pole
                valid_connections.append(connection)
            else:
                self.cleaning_stats['orphaned_connections_removed'] += 1
                logger.debug(f"Removing orphaned connection: {connection.get('connection_id')}")
        
        return valid_connections
    
    def _fix_coordinates(self, poles: List[Dict]) -> List[Dict]:
        """Fix coordinate issues (invalid values, swapped lat/lon, etc.)"""
        for pole in poles:
            lat = pole.get('latitude')
            lon = pole.get('longitude')
            
            # Check if coordinates are valid
            if lat is not None and lon is not None:
                # Check if lat/lon might be swapped (common issue)
                if abs(lat) > 90 and abs(lon) <= 90:
                    pole['latitude'], pole['longitude'] = lon, lat
                    self.cleaning_stats['coordinates_fixed'] += 1
                    logger.debug(f"Swapped lat/lon for pole {pole.get('pole_id')}")
                
                # Ensure coordinates are within valid ranges
                if abs(pole['latitude']) > 90:
                    pole['latitude'] = None
                    pole['longitude'] = None
                    self.cleaning_stats['coordinates_fixed'] += 1
                    logger.warning(f"Invalid coordinates for pole {pole.get('pole_id')}, clearing")
        
        return poles
