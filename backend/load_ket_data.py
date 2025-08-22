#!/usr/bin/env python3
"""
Load KET network data into the backend storage
"""
import json
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the shared storage
from backend.storage import network_storage

def load_ket_data():
    """Load KET data from JSON file into network storage"""
    
    # Path to KET data file
    data_file = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'kml_validation_output',
        'KET_fixed_data.json'
    )
    
    print(f"Loading KET data from: {data_file}")
    
    # Load the JSON data
    with open(data_file, 'r') as f:
        raw_data = json.load(f)
    
    # Convert the structure to match what the backend expects
    network_data = {
        'poles': raw_data.get('poles', {}).get('list', []),
        'conductors': raw_data.get('conductors', {}).get('list', []),
        'connections': raw_data.get('connections', {}).get('list', []),
        'transformers': raw_data.get('transformers', {}).get('list', []),
        'generation': []
    }
    
    # Fix field names for compatibility
    for pole in network_data['poles']:
        if 'gps_lat' in pole:
            pole['latitude'] = pole['gps_lat']
        if 'gps_lng' in pole:
            pole['longitude'] = pole['gps_lng']
    
    for connection in network_data['connections']:
        if 'gps_lat' in connection:
            connection['latitude'] = connection['gps_lat']
        if 'gps_lng' in connection:
            connection['longitude'] = connection['gps_lng']
    
    # Store in network storage
    network_storage['KET'] = network_data
    
    print(f"Loaded KET network data:")
    print(f"  - Poles: {len(network_data['poles'])}")
    print(f"  - Conductors: {len(network_data['conductors'])}")
    print(f"  - Connections: {len(network_data['connections'])}")
    print(f"  - Transformers: {len(network_data['transformers'])}")
    
    return network_data

if __name__ == "__main__":
    load_ket_data()
    print("\nKET data loaded successfully into network_storage")
    print(f"Available sites: {list(network_storage.keys())}")
