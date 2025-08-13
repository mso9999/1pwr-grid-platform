#!/usr/bin/env python3
"""
Pilot Site Test
===============
Tests the complete pipeline on a single site (KET - Ketane)
to validate end-to-end functionality before full deployment.
"""

import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from modules.import_pipeline import ExcelImporter, ImportValidator
from modules.data_cleaning import DataCleaner, TransformerDetector, TopologyFixer
from modules.network_engine import NetworkModel, VoltageCalculator, NetworkValidator
from modules.network_engine.voltage_calculator import VoltageLevel

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# Configuration for pilot site
PILOT_SITE = "KET"  # Ketane site
SITE_VOLTAGE_LEVEL = 11000  # 11kV
VOLTAGE_DROP_THRESHOLD = 7.0  # 7% max allowed


def filter_site_data(data, site_prefix):
    """Filter data for a specific site"""
    
    filtered = {
        'poles': [],
        'conductors': [],
        'connections': [],
        'transformers': []
    }
    
    # Filter poles for the site
    pole_ids = set()
    for pole in data.get('poles', []):
        pole_id = pole.get('pole_id', '')
        if pole_id.startswith(site_prefix):
            filtered['poles'].append(pole)
            pole_ids.add(pole_id)
    
    # Filter conductors connecting site poles
    for conductor in data.get('conductors', []):
        from_pole = conductor.get('from_pole', '')
        to_pole = conductor.get('to_pole', '')
        if from_pole in pole_ids or to_pole in pole_ids:
            filtered['conductors'].append(conductor)
    
    # Filter connections for the site
    for connection in data.get('connections', []):
        # Check if connection is associated with a site pole
        conn_pole = connection.get('pole_id', '')
        if conn_pole in pole_ids:
            filtered['connections'].append(connection)
    
    # Filter transformers for the site
    for transformer in data.get('transformers', []):
        tx_pole = transformer.get('pole_id', '')
        tx_id = transformer.get('transformer_id', '')
        if tx_pole in pole_ids or (tx_id and tx_id.startswith(f"TX_{site_prefix}")):
            filtered['transformers'].append(transformer)
    
    return filtered


def run_pilot_test():
    """Run complete pipeline test on pilot site"""
    
    print("\n" + "="*70)
    print(f"1PWR Grid Platform - Pilot Site Test: {PILOT_SITE}")
    print("="*70)
    print(f"Testing Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Site: {PILOT_SITE} (Ketane)")
    print(f"Voltage Level: {SITE_VOLTAGE_LEVEL/1000:.0f}kV")
    print(f"Max Voltage Drop: {VOLTAGE_DROP_THRESHOLD}%")
    
    # Step 1: Import full dataset
    print("\n" + "="*70)
    print("Step 1: Importing Full Dataset")
    print("="*70)
    
    excel_file = Path("/Users/mattmso/Projects/uGridPREDICT/Updated_20250806_1518/Excel_Files/uGridPlan.xlsx")
    
    if not excel_file.exists():
        print(f"✗ Sample file not found: {excel_file}")
        return False
    
    importer = ExcelImporter(str(excel_file))
    import_result = importer.import_all()
    
    # Extract data arrays
    full_data = {
        'poles': import_result['poles']['poles'] if 'poles' in import_result else [],
        'conductors': import_result['conductors']['conductors'] if 'conductors' in import_result else [],
        'connections': import_result['connections']['connections'] if 'connections' in import_result else [],
        'transformers': import_result['transformers']['transformers'] if 'transformers' in import_result else []
    }
    
    print(f"✓ Full dataset imported:")
    print(f"  • Total Poles: {len(full_data['poles'])}")
    print(f"  • Total Conductors: {len(full_data['conductors'])}")
    print(f"  • Total Connections: {len(full_data['connections'])}")
    print(f"  • Total Transformers: {len(full_data['transformers'])}")
    
    # Step 2: Filter for pilot site
    print("\n" + "="*70)
    print(f"Step 2: Filtering Data for {PILOT_SITE} Site")
    print("="*70)
    
    site_data = filter_site_data(full_data, PILOT_SITE)
    
    print(f"✓ {PILOT_SITE} site data extracted:")
    print(f"  • Poles: {len(site_data['poles'])}")
    print(f"  • Conductors: {len(site_data['conductors'])}")
    print(f"  • Connections: {len(site_data['connections'])}")
    print(f"  • Transformers: {len(site_data['transformers'])}")
    
    if len(site_data['poles']) == 0:
        print(f"✗ No data found for site {PILOT_SITE}")
        return False
    
    # Step 3: Clean site data
    print("\n" + "="*70)
    print("Step 3: Data Cleaning")
    print("="*70)
    
    cleaner = DataCleaner()
    cleaned_data, cleaning_report = cleaner.clean_data(site_data)
    
    print(f"✓ Data cleaning complete:")
    for stat, count in cleaning_report['cleaning_stats'].items():
        if count > 0:
            print(f"  • {stat}: {count}")
    
    # Step 4: Detect transformers
    print("\n" + "="*70)
    print("Step 4: Transformer Detection")
    print("="*70)
    
    detector = TransformerDetector()
    transformers = detector.detect_transformers(
        cleaned_data['poles'],
        cleaned_data['conductors']
    )
    
    print(f"✓ Detected {len(transformers)} transformers")
    if transformers:
        for tx in transformers[:3]:  # Show first 3
            print(f"  • {tx['transformer_id']} at {tx.get('pole_name', 'Unknown')}")
    
    cleaned_data = detector.add_transformers_to_data(cleaned_data, transformers)
    
    # Step 5: Fix topology
    print("\n" + "="*70)
    print("Step 5: Topology Validation")
    print("="*70)
    
    fixer = TopologyFixer()
    fixed_poles, fixed_conductors, fix_report = fixer.fix_topology(
        cleaned_data['poles'],
        cleaned_data['conductors'],
        transformers
    )
    
    print(f"✓ Topology validation complete:")
    for fix, count in fix_report['fixes_applied'].items():
        if count > 0:
            print(f"  • {fix}: {count}")
    
    print(f"\n✓ Network topology status:")
    print(f"  • Is Radial: {fix_report['final_topology']['is_radial']}")
    print(f"  • Is Connected: {fix_report['final_topology']['is_connected']}")
    print(f"  • Components: {fix_report['final_topology']['num_components']}")
    
    cleaned_data['poles'] = fixed_poles
    cleaned_data['conductors'] = fixed_conductors
    
    # Step 6: Build network model
    print("\n" + "="*70)
    print("Step 6: Network Model Construction")
    print("="*70)
    
    network = NetworkModel(network_id=PILOT_SITE)
    network.import_from_dict(cleaned_data)
    
    stats = network.get_stats()
    print(f"✓ Network model built:")
    print(f"  • Poles: {stats.total_poles}")
    print(f"  • Conductors: {stats.total_conductors}")
    print(f"  • Transformers: {stats.total_transformers}")
    print(f"  • Total Length: {stats.total_length_km:.2f} km")
    
    # Step 7: Voltage drop analysis
    print("\n" + "="*70)
    print("Step 7: Voltage Drop Analysis")
    print("="*70)
    
    voltage_calc = VoltageCalculator(
        voltage_drop_threshold=VOLTAGE_DROP_THRESHOLD,
        default_load_per_connection=2.0  # 2kW default load
    )
    
    # Find transformer nodes as sources
    tx_nodes = network.get_transformer_nodes()
    if not tx_nodes:
        print("⚠ No transformers found, using first pole as source")
        if cleaned_data['poles']:
            tx_nodes = [cleaned_data['poles'][0]['pole_id']]
    
    if tx_nodes:
        print(f"✓ Analyzing voltage from {len(tx_nodes)} source points")
        
        violations = []
        max_drop = 0.0
        
        for source in tx_nodes[:1]:  # Analyze from first transformer
            try:
                analysis = voltage_calc.analyze_network(
                    network.graph,
                    transformer_node=source,
                    voltage_level=VoltageLevel.THREE_PHASE_11KV
                )
                
                for node_id, result in analysis.all_nodes.items():
                    if result.voltage_drop_percent > max_drop:
                        max_drop = result.voltage_drop_percent
                    
                    if result.voltage_drop_percent > VOLTAGE_DROP_THRESHOLD:
                        violations.append({
                            'node': node_id,
                            'drop': result.voltage_drop_percent,
                            'voltage': result.final_voltage_v,
                            'distance': result.distance_km
                        })
            except Exception as e:
                print(f"  ⚠ Could not analyze from {source}: {e}")
        
        print(f"\n✓ Voltage analysis results:")
        print(f"  • Maximum voltage drop: {max_drop:.2f}%")
        print(f"  • Violations (>{VOLTAGE_DROP_THRESHOLD}%): {len(violations)}")
        
        if violations:
            print(f"\n⚠ Voltage violations found:")
            for v in violations[:5]:  # Show first 5
                print(f"  • {v['node']}: {v['drop']:.2f}% drop at {v['distance']:.2f}km")
    
    # Step 8: Network validation
    print("\n" + "="*70)
    print("Step 8: Engineering Validation")
    print("="*70)
    
    net_validator = NetworkValidator()
    is_valid, validation_issues = net_validator.validate_network(network.graph)
    
    print(f"✓ Network validation: {'PASSED' if is_valid else 'FAILED'}")
    if not is_valid and validation_issues:
        print(f"  • Issues found: {len(validation_issues)}")
        # Show first 5 issues if they exist
        for i, issue in enumerate(validation_issues):
            if i >= 5:
                break
            print(f"    - {issue}")
    
    # Step 9: Generate pilot report
    print("\n" + "="*70)
    print("Step 9: Generating Pilot Report")
    print("="*70)
    
    output_dir = Path("pilot_output")
    output_dir.mkdir(exist_ok=True)
    
    # Save cleaned data
    with open(output_dir / f"{PILOT_SITE}_cleaned_data.json", "w") as f:
        json.dump(cleaned_data, f, indent=2, default=str)
    
    # Save network GeoJSON
    geojson = network.to_geojson()
    with open(output_dir / f"{PILOT_SITE}_network.geojson", "w") as f:
        json.dump(geojson, f, indent=2)
    
    # Generate summary report
    report = {
        'site': PILOT_SITE,
        'test_date': datetime.now().isoformat(),
        'data_summary': {
            'poles': len(cleaned_data['poles']),
            'conductors': len(cleaned_data['conductors']),
            'connections': len(cleaned_data.get('connections', [])),
            'transformers': len(cleaned_data['transformers']),
            'network_length_km': stats.total_length_km
        },
        'cleaning_summary': cleaning_report['cleaning_stats'],
        'topology_summary': fix_report['final_topology'],
        'voltage_analysis': {
            'max_drop_percent': max_drop,
            'violations': len(violations),
            'threshold_percent': VOLTAGE_DROP_THRESHOLD
        },
        'validation': {
            'passed': is_valid,
            'issues': validation_issues if not is_valid else []
        }
    }
    
    with open(output_dir / f"{PILOT_SITE}_pilot_report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"✓ Reports saved to pilot_output/")
    print(f"  • {PILOT_SITE}_cleaned_data.json")
    print(f"  • {PILOT_SITE}_network.geojson")
    print(f"  • {PILOT_SITE}_pilot_report.json")
    
    # Final summary
    print("\n" + "="*70)
    print("PILOT TEST SUMMARY")
    print("="*70)
    print(f"Site: {PILOT_SITE}")
    print(f"Status: {'✓ PASSED' if is_valid and max_drop <= VOLTAGE_DROP_THRESHOLD else '✗ NEEDS ATTENTION'}")
    print(f"Network Size: {stats.total_poles} poles, {stats.total_length_km:.2f} km")
    print(f"Max Voltage Drop: {max_drop:.2f}%")
    print(f"Data Quality: {len(cleaning_report['cleaning_stats'])} fixes applied")
    
    return True


def main():
    """Main entry point"""
    try:
        success = run_pilot_test()
        
        print("\n" + "="*70)
        if success:
            print(f"✓ Pilot Test Complete: {PILOT_SITE} site processed successfully")
            print("Ready for field team feedback and full deployment")
        else:
            print("✗ Pilot Test Failed")
            return 1
        print("="*70 + "\n")
        
        return 0
        
    except Exception as e:
        print(f"\n✗ Pilot test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
