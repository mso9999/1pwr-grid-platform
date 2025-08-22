#!/usr/bin/env python3
"""
Add test connections to KET data for dropline testing
"""
import json
import random

# Load existing KET data
with open('kml_validation_output/KET_fixed_data.json', 'r') as f:
    data = json.load(f)

# Get poles and conductors for reference
poles = data.get('poles', {}).get('list', [])
conductors = data.get('conductors', {}).get('list', [])

print(f"Loaded {len(poles)} poles and {len(conductors)} conductors")

# Find poles with GPS coordinates and pole_id to place connections near
poles_with_gps = [p for p in poles if p.get('gps_lat') and p.get('gps_lng') and p.get('pole_id')][:20]

if not poles_with_gps:
    print("No poles found with GPS coordinates and pole_id")
    exit(1)

# Create sample connections near poles
connections_list = []
for i, pole in enumerate(poles_with_gps):
    # Create 2-3 connections near each selected pole
    num_connections = random.randint(2, 3)
    for j in range(num_connections):
        connection = {
            'id': f'CONN_{i}_{j}',
            'name': f'Connection {i}-{j}',
            'gps_lat': pole['gps_lat'] + random.uniform(-0.0002, 0.0002),  # Small offset
            'gps_lng': pole['gps_lng'] + random.uniform(-0.0002, 0.0002),
            'latitude': pole['gps_lat'] + random.uniform(-0.0002, 0.0002),
            'longitude': pole['gps_lng'] + random.uniform(-0.0002, 0.0002),
            'pole_id': pole['pole_id'],
            'st_code_3': random.choice([1, 2, 3]),  # Random status code
            'type': 'service_connection'
        }
        connections_list.append(connection)

print(f"Created {len(connections_list)} test connections")

# Add connections to data
if 'connections' not in data:
    data['connections'] = {}
data['connections']['list'] = connections_list

# Create dropline conductors from poles to connections
new_conductors = []
for conn in connections_list[:30]:  # Create droplines for first 30 connections
    conductor = {
        'from_pole': conn['pole_id'],
        'to_pole': conn['id'],
        'length_m': random.uniform(10, 50),
        'cable_size': 0.0,
        'conductor_type': 'dropline',
        'subnetwork': 'TEST',
        'status_code': random.choice([1, 2, 3]),
        'status': 'as_designed'
    }
    new_conductors.append(conductor)

# Add new dropline conductors to existing conductors
existing_conductors = data.get('conductors', {}).get('list', [])
existing_conductors.extend(new_conductors)
data['conductors']['list'] = existing_conductors

print(f"Added {len(new_conductors)} dropline conductors")

# Save updated data
with open('kml_validation_output/KET_fixed_data.json', 'w') as f:
    json.dump(data, f, indent=2)

print("Updated KET_fixed_data.json with test connections and droplines")

# Print summary
print("\nSummary:")
print(f"  Total poles: {len(poles)}")
print(f"  Total connections: {len(connections_list)}")
print(f"  Total conductors: {len(existing_conductors)}")
print(f"  Dropline conductors: {len(new_conductors)}")
