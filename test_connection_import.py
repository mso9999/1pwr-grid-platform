#!/usr/bin/env python3
"""
Test script to verify connections are imported correctly from Excel
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from utils.excel_importer import ExcelImporter

def test_connection_import():
    # Test with the KET network report
    excel_file = 'KET_network_report.xlsx'
    
    if not os.path.exists(excel_file):
        print(f"Error: {excel_file} not found")
        return
    
    print(f"Testing import from {excel_file}")
    print("="*60)
    
    # Import the Excel file
    importer = ExcelImporter(excel_file)
    network_data = importer.import_excel()
    
    # Check results
    print(f"\nImport Results:")
    print(f"  Poles: {len(network_data.get('poles', []))}")
    print(f"  Connections: {len(network_data.get('connections', []))}")
    print(f"  Conductors: {len(network_data.get('conductors', []))}")
    print(f"  Transformers: {len(network_data.get('transformers', []))}")
    
    # Check for connections
    connections = network_data.get('connections', [])
    if connections:
        print(f"\nSample connections (first 5):")
        for i, conn in enumerate(connections[:5]):
            print(f"  {i+1}. ID: {conn.get('survey_id', conn.get('pole_id'))}")
            print(f"     Lat: {conn.get('latitude')}, Lng: {conn.get('longitude')}")
            print(f"     Type: {conn.get('pole_type')}, Connection: {conn.get('connection_type')}")
            print(f"     Status codes: SC1={conn.get('st_code_1')}, SC2={conn.get('st_code_2')}, SC3={conn.get('st_code_3')}")
    else:
        print("\n⚠️  No connections found in import!")
    
    # Check poles to ensure no duplicate connections
    poles = network_data.get('poles', [])
    pole_ids = set(p.get('pole_id') for p in poles)
    connection_ids = set(c.get('survey_id', c.get('pole_id')) for c in connections)
    
    print(f"\nData integrity check:")
    print(f"  Unique pole IDs: {len(pole_ids)}")
    print(f"  Unique connection IDs: {len(connection_ids)}")
    
    # Check for overlap
    overlap = pole_ids.intersection(connection_ids)
    if overlap:
        print(f"  ⚠️  Warning: {len(overlap)} IDs appear in both poles and connections")
        print(f"     Sample overlaps: {list(overlap)[:5]}")
    else:
        print(f"  ✓ No overlap between pole and connection IDs")
    
    # Check conductor endpoints
    conductors = network_data.get('conductors', [])
    if conductors:
        print(f"\nConductor endpoint check (first 5):")
        for i, cond in enumerate(conductors[:5]):
            from_node = cond.get('from_pole')
            to_node = cond.get('to_pole')
            from_type = "pole" if from_node in pole_ids else ("connection" if from_node in connection_ids else "unknown")
            to_type = "pole" if to_node in pole_ids else ("connection" if to_node in connection_ids else "unknown")
            print(f"  {cond.get('conductor_id')}: {from_node} ({from_type}) -> {to_node} ({to_type})")

if __name__ == "__main__":
    test_connection_import()
