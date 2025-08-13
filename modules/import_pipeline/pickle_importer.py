"""
Pickle Importer Module
=====================
Imports legacy uGridPLAN pickle files:
- poles.pickle
- networklines.pickle
- droplines.pickle
- customers.pickle
- analytics.pickle
- networkCost.pickle
"""

import pickle
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class PickleImporter:
    """Import legacy pickle files from uGridPLAN"""
    
    PICKLE_FILES = {
        'poles': 'poles.pickle',
        'network_lines': 'networklines.pickle',
        'drop_lines': 'droplines.pickle',
        'customers': 'customers.pickle',
        'analytics': 'analytics.pickle',
        'network_cost': 'networkCost.pickle'
    }
    
    def __init__(self, pickle_dir: str):
        """
        Initialize importer with pickle directory
        
        Args:
            pickle_dir: Directory containing pickle files
        """
        self.pickle_dir = Path(pickle_dir)
        if not self.pickle_dir.exists():
            raise FileNotFoundError(f"Pickle directory not found: {pickle_dir}")
        
        self.data = {}
        self.metadata = {
            'pickle_dir': str(self.pickle_dir),
            'files_found': []
        }
    
    def load_pickle(self, file_name: str) -> Any:
        """
        Load a single pickle file
        
        Args:
            file_name: Name of pickle file
            
        Returns:
            Unpickled data
        """
        file_path = self.pickle_dir / file_name
        
        if not file_path.exists():
            logger.warning(f"Pickle file not found: {file_path}")
            return None
        
        try:
            with open(file_path, 'rb') as f:
                data = pickle.load(f)
                self.metadata['files_found'].append(file_name)
                return data
        except Exception as e:
            logger.error(f"Error loading pickle file {file_name}: {e}")
            return None
    
    def import_poles(self) -> Dict[str, Any]:
        """
        Import poles from pickle file
        
        Returns:
            Dictionary with pole data
        """
        poles_data = self.load_pickle(self.PICKLE_FILES['poles'])
        
        if poles_data is None:
            return {'poles': [], 'count': 0, 'error': 'Failed to load poles.pickle'}
        
        # Handle different possible formats
        if isinstance(poles_data, dict):
            # Assuming dictionary with pole IDs as keys
            poles = []
            for pole_id, pole_info in poles_data.items():
                pole = {
                    'pole_id': str(pole_id),
                    'pole_type': pole_info.get('type', 'standard'),
                    'utm_x': pole_info.get('utm_x'),
                    'utm_y': pole_info.get('utm_y'),
                    'gps_lat': pole_info.get('lat'),
                    'gps_lng': pole_info.get('lng'),
                    'elevation': pole_info.get('elevation'),
                    'status': pole_info.get('status', 'as_designed')
                }
                poles.append(pole)
        elif isinstance(poles_data, list):
            # Assuming list of pole objects
            poles = []
            for p in poles_data:
                if isinstance(p, dict):
                    poles.append(p)
                else:
                    # Try to extract attributes if it's an object
                    pole = {
                        'pole_id': str(getattr(p, 'id', p)),
                        'pole_type': getattr(p, 'type', 'standard'),
                        'utm_x': getattr(p, 'utm_x', None),
                        'utm_y': getattr(p, 'utm_y', None),
                        'gps_lat': getattr(p, 'lat', None),
                        'gps_lng': getattr(p, 'lng', None),
                        'status': getattr(p, 'status', 'as_designed')
                    }
                    poles.append(pole)
        else:
            poles = []
            logger.warning(f"Unexpected poles data format: {type(poles_data)}")
        
        return {
            'poles': poles,
            'count': len(poles),
            'raw_type': str(type(poles_data))
        }
    
    def import_network_lines(self) -> Dict[str, Any]:
        """
        Import network conductors from pickle file
        
        Returns:
            Dictionary with conductor data
        """
        lines_data = self.load_pickle(self.PICKLE_FILES['network_lines'])
        
        if lines_data is None:
            return {'conductors': [], 'count': 0, 'error': 'Failed to load networklines.pickle'}
        
        conductors = []
        total_length = 0
        
        # Handle different possible formats
        if isinstance(lines_data, list):
            for line in lines_data:
                if isinstance(line, dict):
                    conductor = {
                        'from_pole': str(line.get('from', line.get('node1', ''))),
                        'to_pole': str(line.get('to', line.get('node2', ''))),
                        'length_m': float(line.get('length', 0)),
                        'cable_size': line.get('cable_size', line.get('conductor_type')),
                        'conductor_type': 'network',
                        'status': line.get('status', 'as_designed')
                    }
                else:
                    # Try object attributes
                    conductor = {
                        'from_pole': str(getattr(line, 'from_pole', '')),
                        'to_pole': str(getattr(line, 'to_pole', '')),
                        'length_m': float(getattr(line, 'length', 0)),
                        'cable_size': getattr(line, 'cable_size', None),
                        'conductor_type': 'network',
                        'status': getattr(line, 'status', 'as_designed')
                    }
                
                conductors.append(conductor)
                total_length += conductor['length_m']
        
        return {
            'conductors': conductors,
            'count': len(conductors),
            'total_length_m': total_length,
            'total_length_km': total_length / 1000
        }
    
    def import_drop_lines(self) -> Dict[str, Any]:
        """
        Import service drop lines from pickle file
        
        Returns:
            Dictionary with drop line data
        """
        drops_data = self.load_pickle(self.PICKLE_FILES['drop_lines'])
        
        if drops_data is None:
            return {'drops': [], 'count': 0, 'error': 'Failed to load droplines.pickle'}
        
        drops = []
        total_length = 0
        
        if isinstance(drops_data, list):
            for drop in drops_data:
                if isinstance(drop, dict):
                    drop_line = {
                        'from_pole': str(drop.get('from', drop.get('pole', ''))),
                        'to_connection': str(drop.get('to', drop.get('customer', ''))),
                        'length_m': float(drop.get('length', 0)),
                        'cable_size': drop.get('cable_size'),
                        'conductor_type': 'drop',
                        'status': drop.get('status', 'planned')
                    }
                    drops.append(drop_line)
                    total_length += drop_line['length_m']
        
        return {
            'drops': drops,
            'count': len(drops),
            'total_length_m': total_length,
            'total_length_km': total_length / 1000
        }
    
    def import_customers(self) -> Dict[str, Any]:
        """
        Import customer connections from pickle file
        
        Returns:
            Dictionary with customer data
        """
        customers_data = self.load_pickle(self.PICKLE_FILES['customers'])
        
        if customers_data is None:
            return {'customers': [], 'count': 0, 'error': 'Failed to load customers.pickle'}
        
        customers = []
        
        if isinstance(customers_data, list):
            for customer in customers_data:
                if isinstance(customer, dict):
                    cust = {
                        'customer_id': str(customer.get('id', customer.get('survey_id', ''))),
                        'utm_x': customer.get('utm_x'),
                        'utm_y': customer.get('utm_y'),
                        'gps_lat': customer.get('lat'),
                        'gps_lng': customer.get('lng'),
                        'meter_serial': customer.get('meter_serial'),
                        'status': customer.get('status', 'planned')
                    }
                    customers.append(cust)
        elif isinstance(customers_data, dict):
            for cust_id, cust_info in customers_data.items():
                cust = {
                    'customer_id': str(cust_id),
                    'utm_x': cust_info.get('utm_x'),
                    'utm_y': cust_info.get('utm_y'),
                    'gps_lat': cust_info.get('lat'),
                    'gps_lng': cust_info.get('lng'),
                    'meter_serial': cust_info.get('meter_serial'),
                    'status': cust_info.get('status', 'planned')
                }
                customers.append(cust)
        
        return {
            'customers': customers,
            'count': len(customers)
        }
    
    def import_analytics(self) -> Dict[str, Any]:
        """
        Import analytics/calculations from pickle file
        
        Returns:
            Dictionary with analytics data
        """
        analytics_data = self.load_pickle(self.PICKLE_FILES['analytics'])
        
        if analytics_data is None:
            return {'analytics': {}, 'error': 'Failed to load analytics.pickle'}
        
        # Analytics might contain voltage drop calculations, power flow, etc.
        return {
            'analytics': analytics_data if isinstance(analytics_data, dict) else {},
            'raw_type': str(type(analytics_data))
        }
    
    def import_network_cost(self) -> Dict[str, Any]:
        """
        Import network cost data from pickle file
        
        Returns:
            Dictionary with cost data
        """
        cost_data = self.load_pickle(self.PICKLE_FILES['network_cost'])
        
        if cost_data is None:
            return {'cost': {}, 'error': 'Failed to load networkCost.pickle'}
        
        return {
            'cost': cost_data if isinstance(cost_data, dict) else {},
            'raw_type': str(type(cost_data))
        }
    
    def import_all(self) -> Dict[str, Any]:
        """
        Import all pickle files
        
        Returns:
            Complete import dictionary
        """
        result = {
            'success': True,
            'metadata': self.metadata,
            'poles': self.import_poles(),
            'network_lines': self.import_network_lines(),
            'drop_lines': self.import_drop_lines(),
            'customers': self.import_customers(),
            'analytics': self.import_analytics(),
            'network_cost': self.import_network_cost()
        }
        
        # Combine network and drop lines for total conductors
        total_conductors = result['network_lines']['count'] + result['drop_lines']['count']
        total_length_km = result['network_lines']['total_length_km'] + result['drop_lines']['total_length_km']
        
        result['summary'] = {
            'files_loaded': len(self.metadata['files_found']),
            'total_poles': result['poles']['count'],
            'total_conductors': total_conductors,
            'total_connections': result['customers']['count'],
            'total_length_km': total_length_km
        }
        
        return result
    
    def to_json(self, output_path: Optional[str] = None) -> str:
        """
        Export imported data to JSON
        
        Args:
            output_path: Optional path to save JSON file
            
        Returns:
            JSON string
        """
        data = self.import_all()
        
        # Handle any non-serializable objects
        def default_handler(obj):
            if hasattr(obj, '__dict__'):
                return obj.__dict__
            else:
                return str(obj)
        
        json_str = json.dumps(data, default=default_handler, indent=2)
        
        if output_path:
            with open(output_path, 'w') as f:
                f.write(json_str)
        
        return json_str
