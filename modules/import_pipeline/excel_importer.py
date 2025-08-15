"""
Excel Importer Module
====================
Imports uGridPLAN Excel files with the following sheets:
- PoleClasses: Pole locations and types
- NetworkLength: Main network conductors
- DropLines: Service drop conductors
- Connections: Customer connection points
- NetworkCalculations: Voltage drop calculations
- Transformers: Transformer specifications
- RetProgress: Reticulation progress tracking
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


class ExcelImporter:
    """Import and parse uGridPLAN Excel files"""
    
    REQUIRED_SHEETS = [
        'PoleClasses',
        'NetworkLength',
        'DropLines',
        'Connections',
        'NetworkCalculations',
        'Transformers'
    ]
    
    def __init__(self, file_path: str):
        """
        Initialize importer with Excel file path
        
        Args:
            file_path: Path to uGridPLAN Excel file
        """
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"Excel file not found: {file_path}")
        
        self.excel_file = None
        self.data = {}
        self.metadata = {
            'import_timestamp': datetime.now().isoformat(),
            'file_path': str(self.file_path),
            'file_size': self.file_path.stat().st_size
        }
    
    def validate_structure(self) -> Tuple[bool, List[str]]:
        """
        Validate Excel file has required sheets and columns
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        try:
            xl = pd.ExcelFile(self.file_path)
            sheet_names = xl.sheet_names
            
            # Check required sheets
            missing_sheets = set(self.REQUIRED_SHEETS) - set(sheet_names)
            if missing_sheets:
                errors.append(f"Missing required sheets: {missing_sheets}")
            
            # Check critical columns in each sheet
            column_requirements = {
                'PoleClasses': ['ID', 'Type', 'UTM_X', 'UTM_Y', 'GPS_X', 'GPS_Y'],
                'NetworkLength': ['Node 1', 'Node 2', 'Length', 'Cable_size'],
                'Connections': ['Survey ID', 'UTM_X', 'UTM_Y', 'GPS_X', 'GPS_Y'],
                'NetworkCalculations': ['SubNetwork', 'Branch', 'Length', 'Current', 'NominalVoltage']
            }
            
            for sheet, required_cols in column_requirements.items():
                if sheet in sheet_names:
                    df = pd.read_excel(xl, sheet_name=sheet, nrows=1)
                    missing_cols = set(required_cols) - set(df.columns)
                    if missing_cols:
                        errors.append(f"Sheet '{sheet}' missing columns: {missing_cols}")
            
            xl.close()
            
        except Exception as e:
            errors.append(f"Error reading Excel file: {str(e)}")
        
        return len(errors) == 0, errors
    
    def import_poles(self) -> Dict[str, Any]:
        """
        Import pole data from PoleClasses sheet
        
        Returns:
            Dictionary with pole data and statistics
        """
        df = pd.read_excel(self.file_path, sheet_name='PoleClasses')
        
        # Clean and process data
        df = df.dropna(subset=['ID'])
        
        poles = []
        for _, row in df.iterrows():
            # Get status codes from Excel as per MGD045V03 SOP
            st_code_1 = row.get('St_code_1', 0)  # Pole Construction Progress (0-9)
            st_code_2 = row.get('St_code_2', 'NA')  # Further Pole Progress
            
            # Derive installation status from St_code_1 (construction progress)
            # Based on MGD045V03 SOP Table 2: Status codes 1 (Pole Progress)
            if st_code_1 >= 7:
                # 7=Pole planted, 8=Poletop dressed, 9=Conductor attached
                status = 'installed'
            elif st_code_1 >= 1:
                # 1-6 = Various planning/preparation stages
                status = 'planned'
            else:
                # 0 = uGridNET output (default)
                status = 'as_designed'
            
            pole = {
                'pole_id': str(row['ID']),
                'pole_type': row.get('Type', 'standard'),
                'angle_class': row.get('AngleClass'),
                'elevation': row.get('elevation'),
                'utm_x': row.get('UTM_X'),
                'utm_y': row.get('UTM_Y'),
                'gps_lat': row.get('GPS_Y'),  # Note: Y is latitude
                'gps_lng': row.get('GPS_X'),  # Note: X is longitude
                'subnetwork': row.get('SubNetwork', 'main'),
                'status': status,
                'st_code_1': st_code_1,  # Keep original codes for reference
                'st_code_2': st_code_2
            }
            poles.append(pole)
        
        return {
            'poles': poles,
            'count': len(poles),
            'types': df['Type'].value_counts().to_dict() if 'Type' in df.columns else {},
            'subnetworks': df['SubNetwork'].unique().tolist() if 'SubNetwork' in df.columns else []
        }
    
    def import_conductors(self) -> Dict[str, Any]:
        """
        Import conductor data from NetworkLength and DropLines sheets
        
        Returns:
            Dictionary with conductor data and statistics
        """
        # Main network conductors
        network_df = pd.read_excel(self.file_path, sheet_name='NetworkLength')
        network_df['conductor_type'] = 'network'
        
        # Service drop conductors
        drops_df = pd.read_excel(self.file_path, sheet_name='DropLines')
        drops_df['conductor_type'] = 'drop'
        
        # Combine both
        df = pd.concat([network_df, drops_df], ignore_index=True)
        
        conductors = []
        for _, row in df.iterrows():
            conductor = {
                'from_pole': str(row['Node 1']),
                'to_pole': str(row['Node 2']),
                'length_m': float(row['Length']) if pd.notna(row['Length']) else 0,
                'cable_size': row.get('Cable_size'),
                'conductor_type': row['conductor_type'],
                'subnetwork': row.get('SubNetwork', 'main'),
                'status_code': row.get('St_code_4'),
                'notes': row.get('Line_Notes'),
                'status': 'as_designed'  # Default status
            }
            conductors.append(conductor)
        
        total_length = df['Length'].sum() if 'Length' in df.columns else 0
        
        return {
            'conductors': conductors,
            'count': len(conductors),
            'total_length_m': total_length,
            'total_length_km': total_length / 1000,
            'cable_sizes': df['Cable_size'].value_counts().to_dict() if 'Cable_size' in df.columns else {},
            'by_type': {
                'network': len(network_df),
                'drops': len(drops_df)
            }
        }
    
    def import_connections(self) -> Dict[str, Any]:
        """
        Import customer connection points
        
        Returns:
            Dictionary with connection data
        """
        df = pd.read_excel(self.file_path, sheet_name='Connections')
        df = df.dropna(subset=['Survey ID'])
        
        connections = []
        for _, row in df.iterrows():
            connection = {
                'survey_id': str(row['Survey ID']),
                'elevation': row.get('elevation'),
                'utm_x': row.get('UTM_X'),
                'utm_y': row.get('UTM_Y'),
                'latitude': row.get('GPS_Y'),  # Changed from gps_lat
                'longitude': row.get('GPS_X'),  # Changed from gps_lng
                'subnetwork': row.get('SubNetwork', 'main'),
                'status_code': row.get('St_code_3'),
                'meter_serial': row.get('Meter_Serial'),
                'status': 'planned'  # Default status
            }
            connections.append(connection)
        
        return {
            'connections': connections,
            'count': len(connections),
            'subnetworks': df['SubNetwork'].unique().tolist() if 'SubNetwork' in df.columns else []
        }
    
    def import_calculations(self) -> Dict[str, Any]:
        """
        Import network calculations including voltage drop
        
        Returns:
            Dictionary with calculation data
        """
        df = pd.read_excel(self.file_path, sheet_name='NetworkCalculations')
        
        calculations = []
        max_voltage_drop = 0
        violations = []
        
        for _, row in df.iterrows():
            calc = {
                'subnetwork': row.get('SubNetwork'),
                'branch': row.get('Branch'),
                'connections': row.get('Connections'),
                'line_type': row.get('LineType'),
                'cable_type': row.get('CableType'),
                'nominal_voltage': row.get('NominalVoltage'),
                'minimum_voltage': row.get('MinimumVoltage'),
                'length': row.get('Length'),
                'current': row.get('Current'),
                'voltage_drop': row.get('VoltageDrop'),
                'voltage_drop_percent': row.get('VoltageDropPercent')
            }
            
            # Check for voltage drop violations (7% threshold)
            if calc['voltage_drop_percent'] and calc['voltage_drop_percent'] > 7.0:
                violations.append({
                    'branch': calc['branch'],
                    'voltage_drop': calc['voltage_drop_percent']
                })
                max_voltage_drop = max(max_voltage_drop, calc['voltage_drop_percent'])
            
            calculations.append(calc)
        
        return {
            'calculations': calculations,
            'count': len(calculations),
            'max_voltage_drop_percent': max_voltage_drop,
            'violations': violations,
            'has_violations': len(violations) > 0
        }
    
    def import_transformers(self) -> Dict[str, Any]:
        """
        Import transformer specifications
        
        Returns:
            Dictionary with transformer data
        """
        try:
            df = pd.read_excel(self.file_path, sheet_name='Transformers')
            
            transformers = []
            for _, row in df.iterrows():
                transformer = {
                    'transformer_id': row.get('ID', row.get('TransformerID')),
                    'capacity_kva': row.get('Capacity_kVA', row.get('Capacity')),
                    'primary_voltage': row.get('PrimaryVoltage', row.get('Primary_V')),
                    'secondary_voltage': row.get('SecondaryVoltage', row.get('Secondary_V')),
                    'location_pole': row.get('LocationPole', row.get('Pole_ID')),
                    'utm_x': row.get('UTM_X'),
                    'utm_y': row.get('UTM_Y'),
                    'gps_lat': row.get('GPS_Y'),
                    'gps_lng': row.get('GPS_X'),
                    'type': row.get('Type', 'distribution')
                }
                transformers.append(transformer)
            
            return {
                'transformers': transformers,
                'count': len(transformers),
                'total_capacity_kva': df['Capacity_kVA'].sum() if 'Capacity_kVA' in df.columns else 0
            }
        except Exception as e:
            logger.warning(f"Could not import transformers: {e}")
            return {
                'transformers': [],
                'count': 0,
                'error': str(e)
            }
    
    def import_all(self) -> Dict[str, Any]:
        """
        Import all data from Excel file
        
        Returns:
            Complete import dictionary with all sheets
        """
        is_valid, errors = self.validate_structure()
        if not is_valid:
            return {
                'success': False,
                'errors': errors,
                'metadata': self.metadata
            }
        
        try:
            result = {
                'success': True,
                'metadata': self.metadata,
                'poles': self.import_poles(),
                'conductors': self.import_conductors(),
                'connections': self.import_connections(),
                'calculations': self.import_calculations(),
                'transformers': self.import_transformers()
            }
            
            # Add summary statistics
            result['summary'] = {
                'total_poles': result['poles']['count'],
                'total_conductors': result['conductors']['count'],
                'total_connections': result['connections']['count'],
                'total_length_km': result['conductors']['total_length_km'],
                'has_voltage_violations': result['calculations']['has_violations'],
                'max_voltage_drop': result['calculations']['max_voltage_drop_percent']
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Import failed: {e}")
            return {
                'success': False,
                'errors': [str(e)],
                'metadata': self.metadata
            }
    
    def to_json(self, output_path: Optional[str] = None) -> str:
        """
        Export imported data to JSON
        
        Args:
            output_path: Optional path to save JSON file
            
        Returns:
            JSON string
        """
        data = self.import_all()
        
        # Convert numpy types to Python types for JSON serialization
        def convert(obj):
            if isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif pd.isna(obj):
                return None
            return obj
        
        json_str = json.dumps(data, default=convert, indent=2)
        
        if output_path:
            with open(output_path, 'w') as f:
                f.write(json_str)
        
        return json_str
