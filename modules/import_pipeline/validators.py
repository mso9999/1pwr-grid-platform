"""
Import Validators
=================
Validates imported data for consistency and completeness.
Ensures data meets requirements before processing.
"""

from typing import Dict, List, Tuple, Any, Optional
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ValidationRule:
    """Single validation rule"""
    field: str
    rule_type: str  # required, numeric, range, format, reference
    params: Dict[str, Any]
    message: str


@dataclass 
class ValidationResult:
    """Result of validation check"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    stats: Dict[str, Any]


class ImportValidator:
    """Validates imported network data"""
    
    # Required fields for each entity type
    REQUIRED_FIELDS = {
        'pole': ['pole_id', 'utm_x', 'utm_y'],
        'conductor': ['from_pole', 'to_pole', 'length_m'],
        'connection': ['survey_id', 'utm_x', 'utm_y'],
        'transformer': ['transformer_id', 'capacity_kva', 'location_pole']
    }
    
    # Validation thresholds
    MAX_CONDUCTOR_LENGTH_M = 5000  # 5km max segment length
    MIN_CONDUCTOR_LENGTH_M = 1  # 1m minimum
    MAX_VOLTAGE_DROP_PERCENT = 7.0
    VALID_CABLE_SIZES = ['AAC_50', 'AAC_35', 'AAC_25', 'AAC_16', 
                         'ABC_50', 'ABC_35', 'ABC_25', 'ABC_16']
    VALID_VOLTAGE_LEVELS = [230, 400, 11000, 19000, 33000]
    
    def __init__(self):
        """Initialize validator"""
        self.errors = []
        self.warnings = []
        self.stats = {}
    
    def validate_poles(self, poles_data: List[Dict]) -> ValidationResult:
        """
        Validate pole data
        
        Args:
            poles_data: List of pole dictionaries
            
        Returns:
            ValidationResult
        """
        errors = []
        warnings = []
        stats = {
            'total_poles': len(poles_data),
            'missing_coordinates': 0,
            'duplicate_ids': 0
        }
        
        pole_ids = set()
        
        for i, pole in enumerate(poles_data):
            # Check required fields
            for field in self.REQUIRED_FIELDS['pole']:
                if field not in pole or pole[field] is None:
                    errors.append(f"Pole {i}: Missing required field '{field}'")
            
            # Check for duplicate IDs
            pole_id = pole.get('pole_id')
            if pole_id:
                if pole_id in pole_ids:
                    errors.append(f"Duplicate pole ID: {pole_id}")
                    stats['duplicate_ids'] += 1
                pole_ids.add(pole_id)
            
            # Validate coordinates
            utm_x = pole.get('utm_x')
            utm_y = pole.get('utm_y')
            
            if utm_x is None or utm_y is None:
                stats['missing_coordinates'] += 1
            elif not isinstance(utm_x, (int, float)) or not isinstance(utm_y, (int, float)):
                errors.append(f"Pole {pole_id}: Invalid coordinate format")
            
            # Check GPS coordinates if present
            gps_lat = pole.get('gps_lat')
            gps_lng = pole.get('gps_lng')
            
            if gps_lat is not None and gps_lng is not None:
                if not (-90 <= gps_lat <= 90):
                    warnings.append(f"Pole {pole_id}: Invalid latitude {gps_lat}")
                if not (-180 <= gps_lng <= 180):
                    warnings.append(f"Pole {pole_id}: Invalid longitude {gps_lng}")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            stats=stats
        )
    
    def validate_conductors(self, conductors_data: List[Dict], 
                          pole_ids: Optional[set] = None) -> ValidationResult:
        """
        Validate conductor data
        
        Args:
            conductors_data: List of conductor dictionaries
            pole_ids: Optional set of valid pole IDs for reference checking
            
        Returns:
            ValidationResult
        """
        errors = []
        warnings = []
        stats = {
            'total_conductors': len(conductors_data),
            'invalid_lengths': 0,
            'missing_cable_size': 0,
            'invalid_references': 0
        }
        
        for i, conductor in enumerate(conductors_data):
            # Check required fields
            for field in self.REQUIRED_FIELDS['conductor']:
                if field not in conductor or conductor[field] is None:
                    errors.append(f"Conductor {i}: Missing required field '{field}'")
            
            # Validate pole references
            from_pole = conductor.get('from_pole')
            to_pole = conductor.get('to_pole')
            
            if pole_ids:
                if from_pole and from_pole not in pole_ids:
                    errors.append(f"Conductor {i}: Invalid from_pole reference '{from_pole}'")
                    stats['invalid_references'] += 1
                if to_pole and to_pole not in pole_ids:
                    errors.append(f"Conductor {i}: Invalid to_pole reference '{to_pole}'")
                    stats['invalid_references'] += 1
            
            # Validate length
            length = conductor.get('length_m')
            if length is not None:
                try:
                    length_val = float(length)
                    if length_val < self.MIN_CONDUCTOR_LENGTH_M:
                        warnings.append(f"Conductor {from_pole}-{to_pole}: Very short length {length_val}m")
                        stats['invalid_lengths'] += 1
                    elif length_val > self.MAX_CONDUCTOR_LENGTH_M:
                        warnings.append(f"Conductor {from_pole}-{to_pole}: Very long length {length_val}m")
                        stats['invalid_lengths'] += 1
                except (ValueError, TypeError):
                    errors.append(f"Conductor {i}: Invalid length value '{length}'")
            
            # Validate cable size
            cable_size = conductor.get('cable_size')
            if not cable_size:
                stats['missing_cable_size'] += 1
                warnings.append(f"Conductor {from_pole}-{to_pole}: Missing cable size")
            elif cable_size not in self.VALID_CABLE_SIZES:
                warnings.append(f"Conductor {from_pole}-{to_pole}: Unknown cable size '{cable_size}'")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            stats=stats
        )
    
    def validate_connections(self, connections_data: List[Dict]) -> ValidationResult:
        """
        Validate connection/customer data
        
        Args:
            connections_data: List of connection dictionaries
            
        Returns:
            ValidationResult
        """
        errors = []
        warnings = []
        stats = {
            'total_connections': len(connections_data),
            'missing_coordinates': 0,
            'duplicate_ids': 0
        }
        
        connection_ids = set()
        
        for i, conn in enumerate(connections_data):
            # Check required fields
            conn_id = conn.get('survey_id') or conn.get('customer_id')
            if not conn_id:
                errors.append(f"Connection {i}: Missing identifier (survey_id or customer_id)")
            else:
                if conn_id in connection_ids:
                    errors.append(f"Duplicate connection ID: {conn_id}")
                    stats['duplicate_ids'] += 1
                connection_ids.add(conn_id)
            
            # Validate coordinates
            utm_x = conn.get('utm_x')
            utm_y = conn.get('utm_y')
            
            if utm_x is None or utm_y is None:
                stats['missing_coordinates'] += 1
                warnings.append(f"Connection {conn_id}: Missing coordinates")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            stats=stats
        )
    
    def validate_transformers(self, transformers_data: List[Dict],
                             pole_ids: Optional[set] = None) -> ValidationResult:
        """
        Validate transformer data
        
        Args:
            transformers_data: List of transformer dictionaries
            pole_ids: Optional set of valid pole IDs for reference checking
            
        Returns:
            ValidationResult
        """
        errors = []
        warnings = []
        stats = {
            'total_transformers': len(transformers_data),
            'invalid_capacity': 0,
            'invalid_voltage': 0
        }
        
        for i, transformer in enumerate(transformers_data):
            trans_id = transformer.get('transformer_id', f"T{i}")
            
            # Check required fields
            for field in self.REQUIRED_FIELDS['transformer']:
                if field not in transformer or transformer[field] is None:
                    errors.append(f"Transformer {trans_id}: Missing required field '{field}'")
            
            # Validate pole reference
            location_pole = transformer.get('location_pole')
            if location_pole and pole_ids:
                if location_pole not in pole_ids:
                    errors.append(f"Transformer {trans_id}: Invalid pole reference '{location_pole}'")
            
            # Validate capacity
            capacity = transformer.get('capacity_kva')
            if capacity is not None:
                try:
                    capacity_val = float(capacity)
                    if capacity_val <= 0:
                        errors.append(f"Transformer {trans_id}: Invalid capacity {capacity_val}")
                        stats['invalid_capacity'] += 1
                except (ValueError, TypeError):
                    errors.append(f"Transformer {trans_id}: Invalid capacity value '{capacity}'")
            
            # Validate voltages
            primary_v = transformer.get('primary_voltage')
            secondary_v = transformer.get('secondary_voltage')
            
            if primary_v and primary_v not in self.VALID_VOLTAGE_LEVELS:
                warnings.append(f"Transformer {trans_id}: Unusual primary voltage {primary_v}V")
                stats['invalid_voltage'] += 1
            
            if secondary_v and secondary_v not in self.VALID_VOLTAGE_LEVELS:
                warnings.append(f"Transformer {trans_id}: Unusual secondary voltage {secondary_v}V")
                stats['invalid_voltage'] += 1
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            stats=stats
        )
    
    def validate_voltage_calculations(self, calculations_data: List[Dict]) -> ValidationResult:
        """
        Validate voltage drop calculations
        
        Args:
            calculations_data: List of calculation dictionaries
            
        Returns:
            ValidationResult
        """
        errors = []
        warnings = []
        stats = {
            'total_calculations': len(calculations_data),
            'violations': 0,
            'max_voltage_drop': 0
        }
        
        for calc in calculations_data:
            voltage_drop = calc.get('voltage_drop_percent')
            
            if voltage_drop is not None:
                try:
                    drop_val = float(voltage_drop)
                    stats['max_voltage_drop'] = max(stats['max_voltage_drop'], drop_val)
                    
                    if drop_val > self.MAX_VOLTAGE_DROP_PERCENT:
                        branch = calc.get('branch', 'unknown')
                        errors.append(
                            f"Branch {branch}: Voltage drop {drop_val:.2f}% exceeds {self.MAX_VOLTAGE_DROP_PERCENT}% limit"
                        )
                        stats['violations'] += 1
                    elif drop_val > self.MAX_VOLTAGE_DROP_PERCENT * 0.9:
                        branch = calc.get('branch', 'unknown')
                        warnings.append(
                            f"Branch {branch}: Voltage drop {drop_val:.2f}% approaching limit"
                        )
                except (ValueError, TypeError):
                    pass
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            stats=stats
        )
    
    def validate_import(self, import_data: Dict[str, Any]) -> ValidationResult:
        """
        Validate complete import data
        
        Args:
            import_data: Complete import dictionary from Excel/Pickle importer
            
        Returns:
            ValidationResult with comprehensive validation
        """
        all_errors = []
        all_warnings = []
        all_stats = {}
        
        # Extract pole IDs for reference validation
        pole_ids = set()
        if 'poles' in import_data:
            poles_list = import_data['poles'].get('poles', [])
            pole_ids = {p['pole_id'] for p in poles_list if 'pole_id' in p}
            
            # Validate poles
            result = self.validate_poles(poles_list)
            all_errors.extend(result.errors)
            all_warnings.extend(result.warnings)
            all_stats['poles'] = result.stats
        
        # Validate conductors
        if 'conductors' in import_data:
            conductors_list = import_data['conductors'].get('conductors', [])
            result = self.validate_conductors(conductors_list, pole_ids)
            all_errors.extend(result.errors)
            all_warnings.extend(result.warnings)
            all_stats['conductors'] = result.stats
        
        # Validate connections
        if 'connections' in import_data:
            connections_list = import_data['connections'].get('connections', [])
            result = self.validate_connections(connections_list)
            all_errors.extend(result.errors)
            all_warnings.extend(result.warnings)
            all_stats['connections'] = result.stats
        
        # Validate transformers
        if 'transformers' in import_data:
            transformers_list = import_data['transformers'].get('transformers', [])
            result = self.validate_transformers(transformers_list, pole_ids)
            all_errors.extend(result.errors)
            all_warnings.extend(result.warnings)
            all_stats['transformers'] = result.stats
        
        # Validate calculations if present
        if 'calculations' in import_data:
            calculations_list = import_data['calculations'].get('calculations', [])
            result = self.validate_voltage_calculations(calculations_list)
            all_errors.extend(result.errors)
            all_warnings.extend(result.warnings)
            all_stats['calculations'] = result.stats
        
        # Overall summary
        all_stats['summary'] = {
            'total_errors': len(all_errors),
            'total_warnings': len(all_warnings),
            'is_valid': len(all_errors) == 0
        }
        
        return ValidationResult(
            is_valid=len(all_errors) == 0,
            errors=all_errors[:50],  # Limit to first 50 errors
            warnings=all_warnings[:50],  # Limit to first 50 warnings
            stats=all_stats
        )
