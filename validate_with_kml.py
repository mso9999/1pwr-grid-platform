#!/usr/bin/env python3
"""
KML Cross-Reference Validation Script
Validates and fixes pole references using KML ground truth data
"""

import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from modules.import_pipeline import ExcelImporter
from modules.kml_validator import KMLValidator

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# Configuration
EXCEL_FILE = "/Users/mattmso/Projects/uGridPREDICT/Updated_20250806_1518/Excel_Files/uGridPlan.xlsx"
KML_DIR = "/Users/mattmso/Projects/uGridPREDICT/Updated_20250806_1518/KML_Files"
OUTPUT_DIR = Path("kml_validation_output")
PILOT_SITE = "KET"  # Focus on Ketane site

def filter_site_data(data: Dict, site_code: str) -> Dict:
    """Filter data for specific site"""
    filtered = {
        'poles': {'count': 0, 'list': []},
        'conductors': {'count': 0, 'list': []},
        'connections': {'count': 0, 'list': []},
        'transformers': {'count': 0, 'list': []}
    }
    
    # Filter poles
    for pole in data['poles']['poles']:
        if pole.get('pole_id', '').startswith(site_code):
            filtered['poles']['list'].append(pole)
    filtered['poles']['count'] = len(filtered['poles']['list'])
    
    # Filter conductors
    for conductor in data['conductors']['conductors']:
        if (conductor.get('from_pole', '').startswith(site_code) or 
            conductor.get('to_pole', '').startswith(site_code)):
            filtered['conductors']['list'].append(conductor)
    filtered['conductors']['count'] = len(filtered['conductors']['list'])
    
    # Filter connections
    for connection in data['connections']['connections']:
        if (connection.get('connection_id', '').startswith(site_code) or
            connection.get('pole_id', '').startswith(site_code)):
            filtered['connections']['list'].append(connection)
    filtered['connections']['count'] = len(filtered['connections']['list'])
    
    # Filter transformers
    for transformer in data['transformers']['transformers']:
        transformer_id = transformer.get('transformer_id')
        if transformer_id and transformer_id.startswith(f"TX_{site_code}"):
            filtered['transformers']['list'].append(transformer)
    filtered['transformers']['count'] = len(filtered['transformers']['list'])
    
    return filtered

def apply_fixes(data: Dict, validation_results: Dict) -> Dict:
    """Apply suggested fixes to data"""
    fixed_data = data.copy()
    fixes_applied = {
        'conductors_fixed': 0,
        'connections_fixed': 0,
        'poles_mapped': 0
    }
    
    # Fix conductor references
    suggested_fixes = validation_results.get('suggested_fixes', {})
    for conductor in fixed_data['conductors']['list']:
        key = f"{conductor['from_pole']}->{conductor['to_pole']}"
        if key in suggested_fixes:
            fix = suggested_fixes[key]
            conductor['from_pole'] = fix['fixed_from']
            conductor['to_pole'] = fix['fixed_to']
            fixes_applied['conductors_fixed'] += 1
    
    # Fix connection references
    connection_fixes = {fix['original_pole']: fix['fixed_pole'] 
                       for fix in validation_results.get('connection_fixes', [])}
    
    for connection in fixed_data['connections']['list']:
        if connection['pole_id'] in connection_fixes:
            connection['pole_id'] = connection_fixes[connection['pole_id']]
            fixes_applied['connections_fixed'] += 1
    
    return fixed_data, fixes_applied

def main():
    """Main validation process"""
    
    print("=" * 70)
    print("KML CROSS-REFERENCE VALIDATION")
    print("=" * 70)
    
    # Create output directory
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    # Step 1: Load Excel data
    print("\n📊 Loading Excel data...")
    importer = ExcelImporter(EXCEL_FILE)
    data = importer.import_all()
    
    print(f"✓ Loaded: {data['poles']['count']} poles, {data['conductors']['count']} conductors")
    print(f"          {data['connections']['count']} connections, {data['transformers']['count']} transformers")
    
    # Step 2: Filter for pilot site
    print(f"\n🎯 Filtering for {PILOT_SITE} site...")
    site_data = filter_site_data(data, PILOT_SITE)
    
    print(f"✓ Filtered: {site_data['poles']['count']} poles, {site_data['conductors']['count']} conductors")
    print(f"           {site_data['connections']['count']} connections, {site_data['transformers']['count']} transformers")
    
    # Step 3: Load KML files
    print(f"\n🗺️ Loading KML files from {KML_DIR}...")
    validator = KMLValidator(KML_DIR)
    kml_counts = validator.load_kml_files()
    
    print(f"✓ KML data loaded:")
    for key, count in kml_counts.items():
        print(f"  • {key}: {count}")
    
    # Step 4: Cross-reference validation
    print("\n🔍 Cross-referencing Excel data with KML...")
    validation_results = validator.cross_reference_data(
        site_data['poles'],
        site_data['conductors'],
        site_data['connections']
    )
    
    print(f"\n✓ Validation Results:")
    print(f"  • Pole matches: {validation_results['pole_matches']}")
    print(f"  • Pole mismatches: {len(validation_results['pole_mismatches'])}")
    print(f"  • Valid conductors: {validation_results['conductor_matches']}")
    print(f"  • Invalid conductors: {len(validation_results['conductor_invalid'])}")
    print(f"  • Connection fixes available: {len(validation_results['connection_fixes'])}")
    print(f"  • Conductor fixes available: {len(validation_results['suggested_fixes'])}")
    
    # Step 5: Show sample issues and fixes
    if validation_results['pole_mismatches']:
        print(f"\n⚠️ Sample pole mismatches (first 5):")
        for pole in validation_results['pole_mismatches'][:5]:
            print(f"    - {pole}")
    
    if validation_results['conductor_invalid']:
        print(f"\n⚠️ Sample invalid conductors (first 5):")
        for conductor in validation_results['conductor_invalid'][:5]:
            print(f"    - {conductor['from']} -> {conductor['to']}")
    
    if validation_results['suggested_fixes']:
        print(f"\n✅ Sample conductor fixes (first 5):")
        for key, fix in list(validation_results['suggested_fixes'].items())[:5]:
            print(f"    - {fix['original_from']} -> {fix['original_to']}")
            print(f"      Fixed to: {fix['fixed_from']} -> {fix['fixed_to']}")
    
    if validation_results['connection_fixes']:
        print(f"\n✅ Sample connection fixes (first 5):")
        for fix in validation_results['connection_fixes'][:5]:
            print(f"    - Connection {fix['connection_id']}: {fix['original_pole']} -> {fix['fixed_pole']}")
    
    # Step 6: Apply fixes
    print("\n🔧 Applying fixes to data...")
    fixed_data, fixes_applied = apply_fixes(site_data, validation_results)
    
    print(f"✓ Fixes applied:")
    for key, count in fixes_applied.items():
        print(f"  • {key}: {count}")
    
    # Step 7: Export results
    print("\n💾 Saving validation results...")
    
    # Save validation report
    report_file = OUTPUT_DIR / f"{PILOT_SITE}_kml_validation_report.json"
    validator.export_validation_report(validation_results, str(report_file))
    print(f"✓ Validation report: {report_file}")
    
    # Save fixed data
    fixed_data_file = OUTPUT_DIR / f"{PILOT_SITE}_fixed_data.json"
    with open(fixed_data_file, 'w') as f:
        json.dump(fixed_data, f, indent=2)
    print(f"✓ Fixed data: {fixed_data_file}")
    
    # Step 8: Summary
    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)
    
    total_issues = (len(validation_results['pole_mismatches']) + 
                   len(validation_results['conductor_invalid']))
    total_fixes = (len(validation_results['suggested_fixes']) + 
                  len(validation_results['connection_fixes']))
    
    if total_issues == 0:
        print("✅ All references validated successfully!")
    else:
        print(f"⚠️ Found {total_issues} validation issues")
        print(f"✅ Can automatically fix {total_fixes} issues")
        print(f"❌ {total_issues - total_fixes} issues require manual review")
    
    print("\n📋 Next steps:")
    print("1. Review the validation report for detailed findings")
    print("2. Use fixed_data.json for further processing")
    print("3. Manually review unresolved pole mismatches")
    print("4. Update source data with validated references")
    
    print("\n✓ KML validation complete!")

if __name__ == "__main__":
    main()
