#!/usr/bin/env python3
"""
Test Import Script
==================
Tests the import pipeline with sample data.
Validates Excel import, network construction, and voltage calculations.
"""

import sys
import json
from pathlib import Path
from pprint import pprint

# Add modules to path
sys.path.insert(0, str(Path(__file__).parent))

from modules.import_pipeline import ExcelImporter, ImportValidator
from modules.network_engine import NetworkModel, VoltageCalculator, VoltageLevel


def test_excel_import(file_path: str):
    """Test importing Excel file"""
    print(f"\n{'='*60}")
    print(f"Testing Excel Import: {file_path}")
    print(f"{'='*60}\n")
    
    # Initialize importer
    importer = ExcelImporter(file_path)
    
    # Validate structure
    is_valid, errors = importer.validate_structure()
    print(f"✓ Structure validation: {'PASSED' if is_valid else 'FAILED'}")
    if errors:
        for error in errors:
            print(f"  ⚠ {error}")
    
    # Import all data
    data = importer.import_all()
    
    if data['success']:
        print(f"\n✓ Import successful!")
        print(f"\nSummary:")
        for key, value in data['summary'].items():
            print(f"  • {key}: {value}")
        
        # Validate imported data
        validator = ImportValidator()
        validation_result = validator.validate_import(data)
        
        print(f"\n✓ Validation: {'PASSED' if validation_result.is_valid else 'FAILED'}")
        print(f"  Errors: {len(validation_result.errors)}")
        print(f"  Warnings: {len(validation_result.warnings)}")
        
        if validation_result.errors:
            print("\nFirst 5 errors:")
            for error in validation_result.errors[:5]:
                print(f"  ✗ {error}")
        
        if validation_result.warnings:
            print("\nFirst 5 warnings:")
            for warning in validation_result.warnings[:5]:
                print(f"  ⚠ {warning}")
        
        return data
    else:
        print(f"\n✗ Import failed!")
        for error in data.get('errors', []):
            print(f"  ✗ {error}")
        return None


def test_network_construction(import_data: dict):
    """Test building network from imported data"""
    print(f"\n{'='*60}")
    print(f"Testing Network Construction")
    print(f"{'='*60}\n")
    
    # Create network model
    network = NetworkModel("test_network")
    
    # Import data into network
    network.import_from_dict(import_data)
    
    # Get statistics
    stats = network.get_stats()
    print(f"Network Statistics:")
    print(f"  • Total poles: {stats.total_poles}")
    print(f"  • Total conductors: {stats.total_conductors}")
    print(f"  • Total connections: {stats.total_connections}")
    print(f"  • Total transformers: {stats.total_transformers}")
    print(f"  • Total length: {stats.total_length_km:.2f} km")
    print(f"  • Voltage levels: {stats.voltage_levels}")
    print(f"  • Subnetworks: {stats.subnetworks}")
    
    # Validate topology
    is_valid, issues = network.validate_topology()
    print(f"\n✓ Topology validation: {'PASSED' if is_valid else 'FAILED'}")
    if issues:
        print("  Issues found:")
        for issue in issues:
            print(f"    ⚠ {issue}")
    
    return network


def test_voltage_calculations(network: NetworkModel):
    """Test voltage drop calculations"""
    print(f"\n{'='*60}")
    print(f"Testing Voltage Drop Calculations")
    print(f"{'='*60}\n")
    
    # Get transformer nodes
    transformer_nodes = network.get_transformer_nodes()
    
    if not transformer_nodes:
        print("⚠ No transformer nodes found, cannot perform voltage calculations")
        return None
    
    print(f"Found {len(transformer_nodes)} transformer node(s): {transformer_nodes[:5]}")
    
    # Create voltage calculator
    calculator = VoltageCalculator(voltage_drop_threshold=7.0)
    
    # Test with first transformer
    transformer_node = transformer_nodes[0]
    print(f"\nAnalyzing network from transformer at node: {transformer_node}")
    
    # Perform analysis (default 11kV 3-phase)
    try:
        analysis = calculator.analyze_network(
            network.graph,
            transformer_node,
            voltage_level=VoltageLevel.THREE_PHASE_11KV
        )
        
        print(f"\nVoltage Analysis Results:")
        print(f"  • Source voltage: {analysis.source_voltage}V")
        print(f"  • Max voltage drop: {analysis.max_voltage_drop_percent:.2f}%")
        print(f"  • Threshold: {analysis.threshold_percent}%")
        print(f"  • Valid network: {'YES' if analysis.is_valid else 'NO'}")
        print(f"  • Violations: {len(analysis.violations)}")
        
        if analysis.violations:
            print(f"\nFirst 5 voltage violations:")
            for violation in analysis.violations[:5]:
                print(f"    ✗ Node {violation.node_id}: {violation.voltage_drop_percent:.2f}% drop at {violation.distance_km:.2f}km")
        
        if analysis.warnings:
            print(f"\nWarnings:")
            for warning in analysis.warnings[:5]:
                print(f"    ⚠ {warning}")
        
        return analysis
        
    except Exception as e:
        print(f"✗ Voltage calculation failed: {e}")
        return None


def save_results(data: dict, network: NetworkModel, output_dir: str = "output"):
    """Save test results to files"""
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Save imported data as JSON
    import_file = output_path / "imported_data.json"
    with open(import_file, 'w') as f:
        # Handle non-serializable types
        def default(obj):
            if hasattr(obj, '__dict__'):
                return obj.__dict__
            return str(obj)
        json.dump(data, f, indent=2, default=default)
    print(f"\n✓ Saved import data to: {import_file}")
    
    # Save network as JSON
    network_file = output_path / "network.json"
    with open(network_file, 'w') as f:
        json.dump(network.to_dict(), f, indent=2, default=str)
    print(f"✓ Saved network to: {network_file}")
    
    # Save GeoJSON for visualization
    geojson_file = output_path / "network.geojson"
    with open(geojson_file, 'w') as f:
        json.dump(network.to_geojson(), f, indent=2)
    print(f"✓ Saved GeoJSON to: {geojson_file}")


def main():
    """Main test function"""
    print("\n" + "="*60)
    print("1PWR Grid Platform - Import Pipeline Test")
    print("="*60)
    
    # Check for sample data
    sample_dir = Path("/Users/mattmso/Projects/uGridPREDICT/Updated_20250806_1518/Excel_Files")
    excel_file = sample_dir / "uGridPlan.xlsx"
    
    if not excel_file.exists():
        print(f"\n✗ Sample Excel file not found: {excel_file}")
        print("Please ensure the sample data is available.")
        return 1
    
    # Test Excel import
    import_data = test_excel_import(str(excel_file))
    if not import_data:
        return 1
    
    # Test network construction
    network = test_network_construction(import_data)
    if not network:
        return 1
    
    # Test voltage calculations
    voltage_analysis = test_voltage_calculations(network)
    
    # Save results
    save_results(import_data, network)
    
    print("\n" + "="*60)
    print("✓ All tests completed!")
    print("="*60 + "\n")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
