#!/usr/bin/env python3
"""
Test Enhanced Data Model with KET Site Data
Validates the new data model that distinguishes network conductors from customer droplines
"""

import json
import os
from pathlib import Path
from typing import Dict, Any

# Add project root to path
import sys
sys.path.append(str(Path(__file__).parent))

from modules.import_pipeline.excel_importer import ExcelImporter
from modules.kml_validator.kml_validator import KMLValidator
from modules.data_model.data_converter import DataConverter
from modules.data_model.enhanced_model import EnhancedNetworkModel

def main():
    """Test enhanced data model with KET site"""
    
    # Configuration
    EXCEL_FILE = "/Users/mattmso/Projects/uGridPREDICT/Updated_20250806_1518/Excel_Files/uGridPlan.xlsx"
    KML_DIR = "/Users/mattmso/Projects/uGridPREDICT/Updated_20250806_1518/KML_Files"
    PILOT_SITE = "KET"
    OUTPUT_DIR = Path("enhanced_model_output")
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    print("=" * 70)
    print("ENHANCED DATA MODEL TEST - KET SITE")
    print("=" * 70)
    
    # Step 1: Import Excel data
    print("\n📊 Loading Excel data...")
    importer = ExcelImporter(EXCEL_FILE)
    excel_data = importer.import_all()
    
    if not excel_data['success']:
        print(f"❌ Failed to import data: {excel_data.get('errors')}")
        return
    
    print(f"✓ Loaded: {excel_data['poles']['count']} poles, "
          f"{excel_data['conductors']['count']} conductors")
    
    # Step 2: Convert to enhanced model
    print(f"\n🔄 Converting to enhanced model for {PILOT_SITE}...")
    converter = DataConverter(PILOT_SITE)
    
    # Filter and convert poles
    site_poles = [p for p in excel_data['poles']['poles'] 
                  if p.get('pole_id', '').startswith(PILOT_SITE)]
    pole_mapping = converter.convert_poles(site_poles)
    print(f"✓ Converted {len(pole_mapping)} poles")
    
    # Filter and convert conductors
    site_conductors = [c for c in excel_data['conductors']['conductors']
                      if (c.get('from_pole', '').startswith(PILOT_SITE) or
                          c.get('to_pole', '').startswith(PILOT_SITE))]
    network_count, dropline_count = converter.convert_conductors(site_conductors)
    print(f"✓ Separated {network_count} network conductors and {dropline_count} customer droplines")
    
    # Convert transformers
    site_transformers = []
    for t in excel_data['transformers']['transformers']:
        if t and t.get('transformer_id'):
            tx_id = t.get('transformer_id')
            if tx_id.startswith(f"TX_{PILOT_SITE}"):
                site_transformers.append(t)
    tx_count = converter.convert_transformers(site_transformers)
    print(f"✓ Converted {tx_count} transformers")
    
    # Step 3: Load and apply KML validation
    print(f"\n🗺️ Loading KML validation data...")
    validator = KMLValidator(KML_DIR)
    
    try:
        validator.load_all_files()
        kml_data = {
            'poles_mv': validator.poles_mv,
            'poles_lv': validator.poles_lv,
            'customers': validator.customers
        }
        validated_count = converter.apply_kml_validation(kml_data)
        print(f"✓ Applied KML validation to {validated_count} components")
    except Exception as e:
        print(f"⚠️ Could not load KML data: {e}")
    
    # Step 4: Build network segments
    print(f"\n🔗 Building network segments...")
    segment_count = converter.build_network_segments()
    print(f"✓ Built {segment_count} network segments")
    
    # Step 5: Get enhanced model and statistics
    model = converter.get_model()
    stats = model.get_statistics()
    
    print("\n" + "=" * 70)
    print("ENHANCED MODEL STATISTICS")
    print("=" * 70)
    
    print(f"\n📊 Poles:")
    print(f"  • Total: {stats['poles']['total']}")
    print(f"  • KML Validated: {stats['poles']['validated']}")
    print(f"  • Validation Rate: {stats['poles']['validation_rate']:.1%}")
    
    print(f"\n🔌 Conductors:")
    print(f"  • Total Network: {stats['conductors']['total']}")
    print(f"  • Backbone (MV): {stats['conductors']['backbone']}")
    print(f"  • Distribution (LV): {stats['conductors']['distribution']}")
    
    print(f"\n👥 Customer Connections:")
    print(f"  • Total: {stats['customers']['total']}")
    print(f"  • Connected: {stats['customers']['connected']}")
    print(f"  • Pending: {stats['customers']['pending']}")
    
    print(f"\n⚡ Transformers:")
    print(f"  • Total: {stats['transformers']['total']}")
    print(f"  • Total Capacity: {stats['transformers']['total_capacity_kva']} kVA")
    
    print(f"\n🗺️ Network Segments:")
    print(f"  • Total: {stats['segments']['total']}")
    
    # Step 6: Validate network integrity
    print("\n🔍 Validating network integrity...")
    is_valid, issues = model.validate_network()
    
    if is_valid:
        print("✅ Network validation passed!")
    else:
        print(f"⚠️ Found {len(issues)} validation issues:")
        for issue in issues[:5]:  # Show first 5 issues
            print(f"  • {issue}")
        if len(issues) > 5:
            print(f"  ... and {len(issues) - 5} more")
    
    # Step 7: Export results
    print(f"\n💾 Exporting results...")
    
    # Export summary
    summary = converter.export_summary()
    summary_file = OUTPUT_DIR / f"{PILOT_SITE}_enhanced_model_summary.json"
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"✓ Summary: {summary_file}")
    
    # Export detailed model (sample)
    model_sample = {
        "site_code": model.site_code,
        "poles_sample": {
            pole_id: {
                "utm_x": pole.utm_x,
                "utm_y": pole.utm_y,
                "voltage_level": pole.voltage_level.name if pole.voltage_level else None,
                "kml_validated": pole.kml_validated,
                "kml_source": pole.kml_source
            }
            for pole_id, pole in list(model.poles.items())[:10]
        },
        "network_conductors_sample": {
            cond_id: {
                "from_pole": cond.from_pole,
                "to_pole": cond.to_pole,
                "cable_type": cond.cable_type,
                "voltage_level": cond.voltage_level.name,
                "conductor_type": cond.conductor_type.name,
                "is_backbone": cond.is_backbone()
            }
            for cond_id, cond in list(model.network_conductors.items())[:10]
        },
        "customer_connections_sample": {
            cust_id: {
                "customer_number": cust.customer_number,
                "connection_type": cust.connection_type.name,
                "pole_id": cust.pole_id,
                "dropline_length_m": cust.dropline_length_m,
                "kml_validated": cust.kml_validated
            }
            for cust_id, cust in list(model.customer_connections.items())[:10]
        }
    }
    
    model_file = OUTPUT_DIR / f"{PILOT_SITE}_enhanced_model_sample.json"
    with open(model_file, 'w') as f:
        json.dump(model_sample, f, indent=2)
    print(f"✓ Model sample: {model_file}")
    
    print("\n" + "=" * 70)
    print("ENHANCED MODEL TEST COMPLETE")
    print("=" * 70)
    print("\n✅ Successfully converted data to enhanced model!")
    print("📍 Customer droplines properly separated from network conductors")
    print("🔗 Network segments built for voltage drop analysis")
    print("✓ Ready for web UI development with clean data structure")

if __name__ == "__main__":
    main()
