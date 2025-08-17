import pandas as pd
import numpy as np
from typing import Dict, List, Any
import math


class ExcelImporter:
    """Import Excel files from uGridPREDICT format"""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        
    def import_excel(self) -> Dict[str, Any]:
        """Import Excel file and return network data"""
        try:
            # Read Excel sheets
            xls = pd.ExcelFile(self.file_path)
            
            # Initialize network data
            network_data = {
                'poles': [],
                'connections': [],
                'conductors': [],
                'transformers': [],
                'generation': []
            }
            
            # Import Connections sheet FIRST to get connection IDs
            connection_ids = set()
            if 'Connections' in xls.sheet_names:
                df_connections = pd.read_excel(xls, 'Connections')
                for _, row in df_connections.iterrows():
                    # Map the correct column names from the actual Excel file
                    connection = {
                        'survey_id': str(row.get('pole_id', row.get('Survey ID', ''))),  # Use pole_id or Survey ID
                        'pole_id': str(row.get('pole_id', row.get('Survey ID', ''))),  # Keep both for compatibility
                        'latitude': float(row.get('latitude', row.get('GPS_Y', 0))) if pd.notna(row.get('latitude', row.get('GPS_Y'))) else 0,
                        'longitude': float(row.get('longitude', row.get('GPS_X', 0))) if pd.notna(row.get('longitude', row.get('GPS_X'))) else 0,
                        'pole_type': str(row.get('pole_type', 'CUSTOMER_CONNECTION')),
                        'connection_type': str(row.get('connection_type', 'CUSTOMER')),
                        'st_code_1': int(row.get('st_code_1', 0)) if pd.notna(row.get('st_code_1')) else 0,
                        'st_code_2': str(row.get('st_code_2', 'NA')) if pd.notna(row.get('st_code_2')) else 'NA',
                        'st_code_3': int(row.get('st_code_3', row.get('St_code_3', 0))) if pd.notna(row.get('st_code_3', row.get('St_code_3'))) else 0
                    }
                    if connection['survey_id']:
                        network_data['connections'].append(connection)
                        connection_ids.add(connection['pole_id'])  # Track connection IDs
            
            # Import PoleClasses or Poles sheet, filtering out connections
            poles_sheet = 'PoleClasses' if 'PoleClasses' in xls.sheet_names else 'Poles' if 'Poles' in xls.sheet_names else None
            if poles_sheet:
                df_poles = pd.read_excel(xls, poles_sheet)
                for _, row in df_poles.iterrows():
                    pole_id = str(row.get('pole_id', row.get('ID', '')))
                    
                    # Skip if this ID is already in connections
                    if pole_id in connection_ids:
                        continue
                    
                    pole = {
                        'pole_id': pole_id,
                        'latitude': float(row.get('latitude', row.get('GPS_Y', 0))) if pd.notna(row.get('latitude', row.get('GPS_Y'))) else 0,
                        'longitude': float(row.get('longitude', row.get('GPS_X', 0))) if pd.notna(row.get('longitude', row.get('GPS_X'))) else 0,
                        'pole_type': str(row.get('pole_type', row.get('Type', 'standard'))),
                        'angle_class': str(row.get('pole_class', row.get('angle_class', row.get('Angle_Class', 'Unknown')))),
                        'utm_x': float(row.get('utm_x', row.get('UTM_X', 0))) if pd.notna(row.get('utm_x', row.get('UTM_X'))) else 0,
                        'utm_y': float(row.get('utm_y', row.get('UTM_Y', 0))) if pd.notna(row.get('utm_y', row.get('UTM_Y'))) else 0,
                        'status': str(row.get('status', row.get('Status', 'as_designed'))),
                        'st_code_1': int(row.get('st_code_1', row.get('St_code_1', 0))) if pd.notna(row.get('st_code_1', row.get('St_code_1'))) else 0,
                        'st_code_2': str(row.get('st_code_2', row.get('St_code_2', 'NA'))) if pd.notna(row.get('st_code_2', row.get('St_code_2'))) else 'NA'
                    }
                    if pole['pole_id']:
                        network_data['poles'].append(pole)
            
            # Import NetworkLength or Conductors sheet (MV and LV lines)
            conductors_sheet = 'NetworkLength' if 'NetworkLength' in xls.sheet_names else 'Conductors' if 'Conductors' in xls.sheet_names else None
            if conductors_sheet:
                df_network = pd.read_excel(xls, conductors_sheet)
                for idx, row in df_network.iterrows():
                    conductor = {
                        'conductor_id': str(row.get('conductor_id', f"{row.get('conductor_type', row.get('Type', 'UNKNOWN'))}_{idx}")),
                        'from_pole': str(row.get('from_pole', row.get('Node 1', ''))),
                        'to_pole': str(row.get('to_pole', row.get('Node 2', ''))),
                        'conductor_type': str(row.get('conductor_type', row.get('Type', 'UNKNOWN'))),  # MV or LV
                        'length': float(row.get('length', row.get('Length', 0))) if pd.notna(row.get('length', row.get('Length'))) else 0,
                        'conductor_size': str(row.get('conductor_size', row.get('Conductor_Size', ''))) if pd.notna(row.get('conductor_size', row.get('Conductor_Size'))) else '',
                        'status_code': int(row.get('st_code_4', row.get('St_code_4', 0))) if pd.notna(row.get('st_code_4', row.get('St_code_4'))) else 0
                    }
                    if conductor['from_pole'] and conductor['to_pole']:
                        network_data['conductors'].append(conductor)
            
            # Import DropLines (service drops to customers)
            if 'DropLines' in xls.sheet_names:
                df_droplines = pd.read_excel(xls, 'DropLines')
                for idx, row in df_droplines.iterrows():
                    conductor = {
                        'conductor_id': f"DROP_{idx}",
                        'from_pole': str(row.get('Node 1', '')),
                        'to_pole': str(row.get('Node 2', '')),
                        'conductor_type': 'DROP',
                        'length': float(row.get('Length', 0)) if pd.notna(row.get('Length')) else 0,
                        'conductor_spec': str(row.get('Cable_size', '')) if pd.notna(row.get('Cable_size')) else '',
                        'st_code_4': int(row.get('St_code_4', 0)) if pd.notna(row.get('St_code_4')) else 0
                    }
                    # Only add if both from and to poles exist
                    if conductor['from_pole'] and conductor['to_pole']:
                        network_data['conductors'].append(conductor)
            
            # Import Transformers sheet
            if 'Transformers' in xls.sheet_names:
                df_transformers = pd.read_excel(xls, 'Transformers')
                for _, row in df_transformers.iterrows():
                    transformer = {
                        'transformer_id': str(row.get('transformer_id', '')),
                        'pole_id': str(row.get('survey_id', '')),
                        'rating_kva': float(row.get('rating_kva', 0)) if pd.notna(row.get('rating_kva')) else 0,
                        'type': str(row.get('type', '')),
                        'st_code_1': int(row.get('St_code_1', 0)) if pd.notna(row.get('St_code_1')) else 0
                    }
                    if transformer['transformer_id']:
                        network_data['transformers'].append(transformer)
            
            # Import Generation sheet
            if 'Generation' in xls.sheet_names:
                df_generation = pd.read_excel(xls, 'Generation')
                for _, row in df_generation.iterrows():
                    generation = {
                        'generation_id': str(row.get('generation_id', '')),
                        'pole_id': str(row.get('survey_id', '')),
                        'capacity_kw': float(row.get('capacity_kw', 0)) if pd.notna(row.get('capacity_kw')) else 0,
                        'type': str(row.get('type', '')),
                        'st_code_5': int(row.get('St_code_5', 0)) if pd.notna(row.get('St_code_5')) else 0
                    }
                    if generation['generation_id']:
                        network_data['generation'].append(generation)
            
            return network_data
            
        except Exception as e:
            print(f"Error importing Excel: {str(e)}")
            raise e
