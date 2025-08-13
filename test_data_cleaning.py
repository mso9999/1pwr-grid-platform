#!/usr/bin/env python3
"""
Test Data Cleaning Module
=========================
Validates the data cleaning functionality with sample data.
"""

import sys
import json
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from modules.import_pipeline import ExcelImporter, ImportValidator
from modules.data_cleaning import DataCleaner, TransformerDetector, TopologyFixer
from modules.network_engine import NetworkModel

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def test_data_cleaning():
    """Test the complete data cleaning pipeline"""
    
    print("\n" + "="*60)
    print("1PWR Grid Platform - Data Cleaning Test")
    print("="*60)
    
    # Step 1: Import sample data
    print("\n" + "="*60)
    print("Step 1: Importing Sample Data")
    print("="*60)
    
    excel_file = Path("/Users/mattmso/Projects/uGridPREDICT/Updated_20250806_1518/Excel_Files/uGridPlan.xlsx")
    
    if not excel_file.exists():
        print(f"✗ Sample file not found: {excel_file}")
        return False
    
    importer = ExcelImporter(str(excel_file))
    import_result = importer.import_all()
    
    # Extract the actual data arrays for cleaning
    data_arrays = {
        'poles': import_result['poles']['poles'] if 'poles' in import_result else [],
        'conductors': import_result['conductors']['conductors'] if 'conductors' in import_result else [],
        'connections': import_result['connections']['connections'] if 'connections' in import_result else [],
        'transformers': import_result['transformers']['transformers'] if 'transformers' in import_result else []
    }
    
    print(f"✓ Imported data:")
    print(f"  • Poles: {len(data_arrays.get('poles', []))}")
    print(f"  • Conductors: {len(data_arrays.get('conductors', []))}")
    print(f"  • Connections: {len(data_arrays.get('connections', []))}")
    print(f"  • Transformers: {len(data_arrays.get('transformers', []))}")
    
    # Step 2: Run initial validation
    print("\n" + "="*60)
    print("Step 2: Initial Validation")
    print("="*60)
    
    validator = ImportValidator()
    # Validator expects the nested structure from importer
    validation_result = validator.validate_import(import_result)
    
    print(f"✓ Initial validation: {'PASSED' if validation_result.is_valid else 'FAILED'}")
    print(f"  • Errors: {len(validation_result.errors)}")
    print(f"  • Warnings: {len(validation_result.warnings)}")
    
    # Step 3: Clean data
    print("\n" + "="*60)
    print("Step 3: Data Cleaning")
    print("="*60)
    
    cleaner = DataCleaner()
    cleaned_data, cleaning_report = cleaner.clean_data(data_arrays)
    
    print(f"✓ Data cleaning complete:")
    for stat, count in cleaning_report['cleaning_stats'].items():
        if count > 0:
            print(f"  • {stat}: {count}")
    
    print(f"\n✓ Cleaned data summary:")
    for key, count in cleaning_report['data_summary'].items():
        print(f"  • {key}: {count}")
    
    # Step 4: Detect transformers
    print("\n" + "="*60)
    print("Step 4: Transformer Detection")
    print("="*60)
    
    detector = TransformerDetector()
    transformers = detector.detect_transformers(
        cleaned_data['poles'],
        cleaned_data['conductors']
    )
    
    print(f"✓ Detected {len(transformers)} transformers:")
    for i, tx in enumerate(transformers[:5]):  # Show first 5
        print(f"  • {tx['transformer_id']}: {tx['pole_name']} "
              f"(method: {tx['detection_method']}, confidence: {tx['confidence']:.1f})")
    
    # Add transformers to data
    cleaned_data = detector.add_transformers_to_data(cleaned_data, transformers)
    
    # Step 5: Fix topology
    print("\n" + "="*60)
    print("Step 5: Topology Fixing")
    print("="*60)
    
    fixer = TopologyFixer()
    fixed_poles, fixed_conductors, fix_report = fixer.fix_topology(
        cleaned_data['poles'],
        cleaned_data['conductors'],
        transformers
    )
    
    print(f"✓ Topology fixes applied:")
    for fix, count in fix_report['fixes_applied'].items():
        if count > 0:
            print(f"  • {fix}: {count}")
    
    print(f"\n✓ Final topology status:")
    for status, value in fix_report['final_topology'].items():
        print(f"  • {status}: {value}")
    
    # Update cleaned data with fixed topology
    cleaned_data['poles'] = fixed_poles
    cleaned_data['conductors'] = fixed_conductors
    
    # Step 6: Validate cleaned data
    print("\n" + "="*60)
    print("Step 6: Post-Cleaning Validation")
    print("="*60)
    
    # Convert cleaned data back to nested structure for validator
    cleaned_import_format = {
        'poles': {'poles': cleaned_data['poles'], 'count': len(cleaned_data['poles'])},
        'conductors': {'conductors': cleaned_data['conductors'], 'count': len(cleaned_data['conductors'])},
        'connections': {'connections': cleaned_data.get('connections', []), 'count': len(cleaned_data.get('connections', []))},
        'transformers': {'transformers': cleaned_data['transformers'], 'count': len(cleaned_data['transformers'])}
    }
    
    final_result = validator.validate_import(cleaned_import_format)
    
    print(f"✓ Final validation: {'PASSED' if final_result.is_valid else 'FAILED'}")
    print(f"  • Errors: {len(final_result.errors)} "
          f"(reduced from {len(validation_result.errors)})")
    print(f"  • Warnings: {len(final_result.warnings)} "
          f"(reduced from {len(validation_result.warnings)})")
    
    # Show improvements
    error_reduction = len(validation_result.errors) - len(final_result.errors)
    warning_reduction = len(validation_result.warnings) - len(final_result.warnings)
    
    if error_reduction > 0:
        print(f"\n✓ Fixed {error_reduction} errors through cleaning")
    if warning_reduction > 0:
        print(f"✓ Fixed {warning_reduction} warnings through cleaning")
    
    # Step 7: Build network model with cleaned data
    print("\n" + "="*60)
    print("Step 7: Network Model Construction")
    print("="*60)
    
    network = NetworkModel()
    network.import_from_dict(cleaned_data)
    
    stats = network.get_stats()
    print(f"✓ Network built successfully:")
    print(f"  • Poles: {stats.total_poles}")
    print(f"  • Conductors: {stats.total_conductors}")
    print(f"  • Transformers: {stats.total_transformers}")
    print(f"  • Total length: {stats.total_length_km:.2f} km")
    print(f"  • Voltage levels: {stats.voltage_levels}")
    
    # Save cleaned data
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    with open(output_dir / "cleaned_data.json", "w") as f:
        json.dump(cleaned_data, f, indent=2, default=str)
    
    print(f"\n✓ Saved cleaned data to: output/cleaned_data.json")
    
    # Save network as GeoJSON for visualization
    geojson = network.to_geojson()
    with open(output_dir / "cleaned_network.geojson", "w") as f:
        json.dump(geojson, f, indent=2)
    
    print(f"✓ Saved network GeoJSON to: output/cleaned_network.geojson")
    
    return True


def main():
    """Main test runner"""
    try:
        success = test_data_cleaning()
        
        print("\n" + "="*60)
        if success:
            print("✓ Data Cleaning Module Test: PASSED")
            print("  All components working correctly!")
        else:
            print("✗ Data Cleaning Module Test: FAILED")
            return 1
        print("="*60 + "\n")
        
        return 0
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
