"""
KML Validator Module
Cross-references pole and conductor data with KML files
"""

import logging
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Tuple, Set, Optional
import re
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)

@dataclass
class KMLPole:
    """Represents a pole from KML data"""
    id: str
    name: str
    lat: float
    lon: float
    description: str = ""
    pole_type: str = ""  # MV or LV
    
@dataclass
class KMLConnection:
    """Represents a customer connection from KML"""
    id: str
    name: str
    lat: float
    lon: float
    pole_ref: Optional[str] = None
    connection_type: str = ""

@dataclass
class KMLConductor:
    """Represents a conductor line from KML"""
    from_pole: str
    to_pole: str
    conductor_type: str = ""
    voltage_level: str = ""  # MV or LV

class KMLValidator:
    """Validates and cross-references data with KML files"""
    
    def __init__(self, kml_directory: str):
        """
        Initialize KML validator
        
        Args:
            kml_directory: Path to directory containing KML files
        """
        self.kml_dir = Path(kml_directory)
        self.poles_mv: Dict[str, KMLPole] = {}
        self.poles_lv: Dict[str, KMLPole] = {}
        self.customers: Dict[str, KMLConnection] = {}
        self.conductors_mv: List[KMLConductor] = []
        self.conductors_lv: List[KMLConductor] = []
        self.droplines: List[KMLConductor] = []
        
        # Name variations mapping
        self.pole_name_variants: Dict[str, str] = {}
        
    def load_kml_files(self) -> Dict[str, int]:
        """
        Load all KML files from directory
        
        Returns:
            Dictionary with counts of loaded elements
        """
        counts = {
            'poles_mv': 0,
            'poles_lv': 0,
            'customers': 0,
            'conductors_mv': 0,
            'conductors_lv': 0,
            'droplines': 0
        }
        
        # Load MV poles
        mv_poles_file = self.kml_dir / "poles_mv.kml"
        if mv_poles_file.exists():
            self.poles_mv = self._parse_poles_kml(mv_poles_file, "MV")
            counts['poles_mv'] = len(self.poles_mv)
            logger.info(f"Loaded {counts['poles_mv']} MV poles")
        
        # Load LV poles
        lv_poles_file = self.kml_dir / "poles_lv.kml"
        if lv_poles_file.exists():
            self.poles_lv = self._parse_poles_kml(lv_poles_file, "LV")
            counts['poles_lv'] = len(self.poles_lv)
            logger.info(f"Loaded {counts['poles_lv']} LV poles")
        
        # Load customers
        customers_file = self.kml_dir / "customers.kml"
        if customers_file.exists():
            self.customers = self._parse_customers_kml(customers_file)
            counts['customers'] = len(self.customers)
            logger.info(f"Loaded {counts['customers']} customers")
        
        # Load MV conductors
        mv_lines_file = self.kml_dir / "networklines_mv.kml"
        if mv_lines_file.exists():
            self.conductors_mv = self._parse_conductors_kml(mv_lines_file, "MV")
            counts['conductors_mv'] = len(self.conductors_mv)
            logger.info(f"Loaded {counts['conductors_mv']} MV conductors")
        
        # Load LV conductors
        lv_lines_file = self.kml_dir / "networklines_lv.kml"
        if lv_lines_file.exists():
            self.conductors_lv = self._parse_conductors_kml(lv_lines_file, "LV")
            counts['conductors_lv'] = len(self.conductors_lv)
            logger.info(f"Loaded {counts['conductors_lv']} LV conductors")
        
        # Load droplines
        droplines_file = self.kml_dir / "droplines.kml"
        if droplines_file.exists():
            self.droplines = self._parse_conductors_kml(droplines_file, "DROP")
            counts['droplines'] = len(self.droplines)
            logger.info(f"Loaded {counts['droplines']} droplines")
        
        # Build name variants mapping
        self._build_name_variants()
        
        return counts
    
    def _parse_poles_kml(self, file_path: Path, pole_type: str) -> Dict[str, KMLPole]:
        """Parse poles from KML file"""
        poles = {}
        
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Handle KML namespace
            ns = {'kml': 'http://www.opengis.net/kml/2.2'}
            
            # Find all Placemarks
            for placemark in root.findall('.//kml:Placemark', ns):
                name_elem = placemark.find('kml:name', ns)
                if name_elem is None:
                    continue
                    
                pole_name = name_elem.text.strip()
                
                # Get coordinates
                coords_elem = placemark.find('.//kml:coordinates', ns)
                if coords_elem is not None and coords_elem.text:
                    coords = coords_elem.text.strip().split(',')
                    if len(coords) >= 2:
                        lon = float(coords[0])
                        lat = float(coords[1])
                        
                        # Get description if available
                        desc_elem = placemark.find('kml:description', ns)
                        description = desc_elem.text if desc_elem is not None else ""
                        
                        pole = KMLPole(
                            id=pole_name,
                            name=pole_name,
                            lat=lat,
                            lon=lon,
                            description=description,
                            pole_type=pole_type
                        )
                        poles[pole_name] = pole
                        
        except Exception as e:
            logger.error(f"Error parsing poles KML {file_path}: {e}")
        
        return poles
    
    def _parse_customers_kml(self, file_path: Path) -> Dict[str, KMLConnection]:
        """Parse customer connections from KML file"""
        customers = {}
        
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            ns = {'kml': 'http://www.opengis.net/kml/2.2'}
            
            for placemark in root.findall('.//kml:Placemark', ns):
                name_elem = placemark.find('kml:name', ns)
                if name_elem is None:
                    continue
                    
                customer_name = name_elem.text.strip()
                
                # Get coordinates
                coords_elem = placemark.find('.//kml:coordinates', ns)
                if coords_elem is not None and coords_elem.text:
                    coords = coords_elem.text.strip().split(',')
                    if len(coords) >= 2:
                        lon = float(coords[0])
                        lat = float(coords[1])
                        
                        # Try to extract pole reference from name or description
                        desc_elem = placemark.find('kml:description', ns)
                        description = desc_elem.text if desc_elem is not None else ""
                        
                        # Parse pole reference from customer name (e.g., "KET 305 HH1")
                        pole_ref = self._extract_pole_ref(customer_name)
                        
                        customer = KMLConnection(
                            id=customer_name,
                            name=customer_name,
                            lat=lat,
                            lon=lon,
                            pole_ref=pole_ref,
                            connection_type=self._extract_connection_type(customer_name)
                        )
                        customers[customer_name] = customer
                        
        except Exception as e:
            logger.error(f"Error parsing customers KML {file_path}: {e}")
        
        return customers
    
    def _parse_conductors_kml(self, file_path: Path, conductor_type: str) -> List[KMLConductor]:
        """Parse conductor lines from KML file"""
        conductors = []
        
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            ns = {'kml': 'http://www.opengis.net/kml/2.2'}
            
            for placemark in root.findall('.//kml:Placemark', ns):
                # Get line string coordinates
                coords_elem = placemark.find('.//kml:coordinates', ns)
                if coords_elem is not None and coords_elem.text:
                    coords_text = coords_elem.text.strip()
                    coord_pairs = coords_text.split()
                    
                    if len(coord_pairs) >= 2:
                        # Extract start and end points
                        start_coords = coord_pairs[0].split(',')
                        end_coords = coord_pairs[-1].split(',')
                        
                        # Match coordinates to poles
                        from_pole = self._find_pole_by_coords(
                            float(start_coords[0]), 
                            float(start_coords[1])
                        )
                        to_pole = self._find_pole_by_coords(
                            float(end_coords[0]), 
                            float(end_coords[1])
                        )
                        
                        if from_pole and to_pole:
                            conductor = KMLConductor(
                                from_pole=from_pole,
                                to_pole=to_pole,
                                conductor_type=conductor_type,
                                voltage_level=conductor_type if conductor_type in ['MV', 'LV'] else ''
                            )
                            conductors.append(conductor)
                        
        except Exception as e:
            logger.error(f"Error parsing conductors KML {file_path}: {e}")
        
        return conductors
    
    def _extract_pole_ref(self, customer_name: str) -> Optional[str]:
        """Extract pole reference from customer name"""
        # Pattern: "KET XXX HH1" or similar
        patterns = [
            r'(KET[_\s]\d+[_\s][A-Z]+\d*)',  # KET_17_GA124 format
            r'(KET\s+\d+)',  # KET 305 format
        ]
        
        for pattern in patterns:
            match = re.search(pattern, customer_name)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_connection_type(self, customer_name: str) -> str:
        """Extract connection type from customer name"""
        if 'HH' in customer_name:
            return 'Household'
        elif 'SME' in customer_name:
            return 'SME'
        elif 'COM' in customer_name:
            return 'Commercial'
        return 'Unknown'
    
    def _find_pole_by_coords(self, lon: float, lat: float, tolerance: float = 0.0001) -> Optional[str]:
        """Find pole ID by coordinates with tolerance"""
        all_poles = {**self.poles_mv, **self.poles_lv}
        
        for pole_id, pole in all_poles.items():
            if abs(pole.lon - lon) < tolerance and abs(pole.lat - lat) < tolerance:
                return pole_id
        
        return None
    
    def _build_name_variants(self):
        """Build mapping of name variants to canonical pole names"""
        all_poles = {**self.poles_mv, **self.poles_lv}
        
        for pole_id in all_poles:
            # Add original name
            self.pole_name_variants[pole_id] = pole_id
            
            # Add variants without underscores
            variant1 = pole_id.replace('_', ' ')
            self.pole_name_variants[variant1] = pole_id
            
            # Add variants with different separators
            variant2 = pole_id.replace('_', '-')
            self.pole_name_variants[variant2] = pole_id
            
            # Extract site and pole number for additional variants
            if pole_id.startswith('KET'):
                # Handle format like KET_17_GA124
                parts = pole_id.split('_')
                if len(parts) >= 2:
                    # Create variant like "KET 17"
                    variant3 = f"KET {parts[1]}"
                    self.pole_name_variants[variant3] = pole_id
    
    def validate_pole_reference(self, pole_ref: str) -> Tuple[bool, Optional[str]]:
        """
        Validate a pole reference and return canonical name if found
        
        Args:
            pole_ref: Pole reference to validate
            
        Returns:
            Tuple of (is_valid, canonical_name)
        """
        # Direct match
        all_poles = {**self.poles_mv, **self.poles_lv}
        if pole_ref in all_poles:
            return True, pole_ref
        
        # Check variants
        if pole_ref in self.pole_name_variants:
            return True, self.pole_name_variants[pole_ref]
        
        # Try fuzzy matching for customer references
        # Pattern: "KET XXX HH1" -> extract pole part
        pole_part = self._extract_pole_ref(pole_ref)
        if pole_part and pole_part in self.pole_name_variants:
            return True, self.pole_name_variants[pole_part]
        
        return False, None
    
    def cross_reference_data(self, poles_data: Dict, conductors_data: Dict, 
                            connections_data: Dict) -> Dict[str, any]:
        """
        Cross-reference Excel data with KML data
        
        Args:
            poles_data: Poles from Excel import
            conductors_data: Conductors from Excel import
            connections_data: Connections from Excel import
            
        Returns:
            Validation results and fixes
        """
        results = {
            'pole_matches': 0,
            'pole_mismatches': [],
            'conductor_matches': 0,
            'conductor_invalid': [],
            'connection_fixes': [],
            'suggested_fixes': {}
        }
        
        # Validate poles
        excel_poles = set(pole.get('pole_id') for pole in poles_data.get('list', []) if pole.get('pole_id'))
        kml_poles = set(self.poles_mv.keys()) | set(self.poles_lv.keys())
        
        results['pole_matches'] = len(excel_poles & kml_poles)
        results['pole_mismatches'] = list(excel_poles - kml_poles)
        
        # Validate conductors
        for conductor in conductors_data.get('list', []):
            from_pole = conductor.get('from_pole')
            to_pole = conductor.get('to_pole')
            
            from_valid, from_canonical = self.validate_pole_reference(from_pole)
            to_valid, to_canonical = self.validate_pole_reference(to_pole)
            
            if from_valid and to_valid:
                results['conductor_matches'] += 1
                
                # Store fix if names changed
                if from_pole != from_canonical or to_pole != to_canonical:
                    key = f"{from_pole}->{to_pole}"
                    results['suggested_fixes'][key] = {
                        'original_from': from_pole,
                        'original_to': to_pole,
                        'fixed_from': from_canonical,
                        'fixed_to': to_canonical
                    }
            else:
                results['conductor_invalid'].append({
                    'from': from_pole,
                    'to': to_pole,
                    'from_valid': from_valid,
                    'to_valid': to_valid
                })
        
        # Validate and fix connections
        for connection in connections_data.get('list', []):
            conn_id = connection.get('connection_id')
            pole_ref = connection.get('pole_id')
            
            # Check if this connection exists in KML customers
            if conn_id in self.customers:
                kml_customer = self.customers[conn_id]
                
                # Try to find correct pole reference
                if kml_customer.pole_ref:
                    is_valid, canonical = self.validate_pole_reference(kml_customer.pole_ref)
                    if is_valid:
                        results['connection_fixes'].append({
                            'connection_id': conn_id,
                            'original_pole': pole_ref,
                            'fixed_pole': canonical,
                            'source': 'KML customer data'
                        })
        
        return results
    
    def export_validation_report(self, results: Dict, output_file: str):
        """Export validation results to JSON report"""
        report = {
            'kml_stats': {
                'poles_mv': len(self.poles_mv),
                'poles_lv': len(self.poles_lv),
                'customers': len(self.customers),
                'conductors_mv': len(self.conductors_mv),
                'conductors_lv': len(self.conductors_lv),
                'droplines': len(self.droplines)
            },
            'validation_results': results,
            'summary': {
                'total_pole_matches': results['pole_matches'],
                'total_pole_mismatches': len(results['pole_mismatches']),
                'total_conductor_matches': results['conductor_matches'],
                'total_conductor_invalid': len(results['conductor_invalid']),
                'total_connection_fixes': len(results['connection_fixes']),
                'total_suggested_fixes': len(results['suggested_fixes'])
            }
        }
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Validation report saved to {output_file}")
        
        return report
