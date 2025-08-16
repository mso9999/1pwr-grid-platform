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
            
            # Import PoleClasses sheet (poles data)
            if 'PoleClasses' in xls.sheet_names:
                df_poles = pd.read_excel(xls, 'PoleClasses')
                for _, row in df_poles.iterrows():
                    pole = {
                        'pole_id': str(row.get('ID', '')),
                        'latitude': float(row.get('GPS_Y', 0)) if pd.notna(row.get('GPS_Y')) else 0,
                        'longitude': float(row.get('GPS_X', 0)) if pd.notna(row.get('GPS_X')) else 0,
                        'pole_type': str(row.get('Type', 'POLE')),
                        'pole_class': str(row.get('AngleClass', 'Unknown')),
                        'st_code_1': int(row.get('St_code_1', 0)) if pd.notna(row.get('St_code_1')) else 0,
                        'st_code_2': str(row.get('St_code_2', 'NA')) if pd.notna(row.get('St_code_2')) else 'NA'
                    }
                    if pole['pole_id']:
                        network_data['poles'].append(pole)
            
            # Import Connections sheet (customer connections)
            if 'Connections' in xls.sheet_names:
                df_connections = pd.read_excel(xls, 'Connections')
                for _, row in df_connections.iterrows():
                    connection = {
                        'pole_id': str(row.get('Survey ID', '')),
                        'latitude': float(row.get('GPS_Y', 0)) if pd.notna(row.get('GPS_Y')) else 0,
                        'longitude': float(row.get('GPS_X', 0)) if pd.notna(row.get('GPS_X')) else 0,
                        'pole_type': 'CUSTOMER_CONNECTION',
                        'connection_type': 'CUSTOMER',
                        'st_code_1': 0,  # Connections don't have st_code_1
                        'st_code_2': 'NA',  # Connections don't have st_code_2
                        'st_code_3': int(row.get('St_code_3', 0)) if pd.notna(row.get('St_code_3')) else 0
                    }
                    if connection['pole_id']:
                        network_data['connections'].append(connection)
                        # Also add as a pole for conductor references
                        network_data['poles'].append(connection)
            
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
            
            # Import NetworkLength sheet (MV and LV lines)
            if 'NetworkLength' in xls.sheet_names:
                df_network = pd.read_excel(xls, 'NetworkLength')
                for idx, row in df_network.iterrows():
                    line_type = str(row.get('Type', '')).upper()
                    if line_type in ['MV', 'LV']:
                        conductor = {
                            'conductor_id': f"{line_type}_{idx}",
                            'from_pole': str(row.get('Node 1', '')),
                            'to_pole': str(row.get('Node 2', '')),
                            'conductor_type': line_type,
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
