#!/usr/bin/env python3
"""
Test script for as-built tracking API endpoints
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"
SITE = "KET"

def test_as_built_endpoints():
    """Test all as-built API endpoints"""
    
    print("\n=== Testing As-Built Tracking API ===\n")
    
    # 1. Check initial state (no snapshots)
    print("1. Checking initial snapshots...")
    response = requests.get(f"{BASE_URL}/api/as-built/{SITE}/snapshots")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Initial snapshots: {len(data.get('snapshots', []))} found")
    else:
        print(f"❌ Failed to get snapshots: {response.status_code}")
        return
    
    # 2. Create first as-built snapshot with some field data
    print("\n2. Creating as-built snapshot...")
    snapshot_data = {
        "created_by": "field_team_1",
        "poles": [
            {
                "pole_id": "KET_01_AA1",
                "latitude": -29.532,
                "longitude": 27.886,
                "st_code_1": 7,  # Pole planted
                "st_code_2": "SI",  # Stay wires installed
                "installation_date": datetime.now().isoformat(),
                "installed_by": "Team A"
            },
            {
                "pole_id": "KET_01_AA2",
                "latitude": -29.533,
                "longitude": 27.887,
                "st_code_1": 8,  # Poletop dressed
                "st_code_2": "NA",
                "installation_date": datetime.now().isoformat(),
                "installed_by": "Team A"
            }
        ],
        "connections": [
            {
                "connection_id": "KET 001 HH1",
                "latitude": -29.5321,
                "longitude": 27.8861,
                "st_code_3": 9,  # Meter commissioned
                "meter_installed": True,
                "installation_date": datetime.now().isoformat()
            }
        ],
        "conductors": [
            {
                "conductor_id": "COND_001",
                "from_pole": "KET_01_AA1",
                "to_pole": "KET_01_AA2",
                "conductor_type": "LV",
                "st_code_4": 5,  # String complete
                "length": 45.5,
                "stringing_date": datetime.now().isoformat()
            }
        ],
        "metadata": {
            "weather": "Clear",
            "team_size": 5
        }
    }
    
    response = requests.post(
        f"{BASE_URL}/api/as-built/{SITE}/snapshot",
        json=snapshot_data
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Snapshot created")
        print(f"   - Snapshot ID: {data.get('snapshot_id')}")
        print(f"   - Overall progress: {data.get('summary', {}).get('overall_progress')}%")
    else:
        print(f"❌ Failed to create snapshot: {response.status_code}")
        print(f"   Error: {response.text}")
        return
    
    # 3. Get comparison with planned network
    print("\n3. Comparing as-built with planned...")
    response = requests.get(f"{BASE_URL}/api/as-built/{SITE}/comparison")
    
    if response.status_code == 200:
        data = response.json()
        report = data.get('report', {})
        print(f"✅ Comparison generated")
        print(f"   - Overall progress: {report.get('overall_progress', 0):.1f}%")
        print(f"   - Poles progress: {report.get('pole_progress', 0):.1f}%")
        print(f"   - Conductors progress: {report.get('conductor_progress', 0):.1f}%")
        print(f"   - Connections progress: {report.get('connection_progress', 0):.1f}%")
    else:
        print(f"❌ Failed to get comparison: {response.status_code}")
    
    # 4. Update construction progress
    print("\n4. Updating construction progress...")
    update_data = {
        "updated_by": "field_team_2",
        "poles": [
            {
                "pole_id": "KET_01_AA3",
                "latitude": -29.534,
                "longitude": 27.888,
                "st_code_1": 9,  # Conductor attached
                "st_code_2": "TI",  # Transformer installed
                "installation_date": datetime.now().isoformat(),
                "installed_by": "Team B"
            }
        ],
        "conductors": [
            {
                "conductor_id": "COND_002",
                "from_pole": "KET_01_AA2",
                "to_pole": "KET_01_AA3",
                "conductor_type": "LV",
                "st_code_4": 3,  # String in progress
                "length": 52.3
            }
        ]
    }
    
    response = requests.post(
        f"{BASE_URL}/api/as-built/{SITE}/update-progress",
        json=update_data
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Progress updated")
        print(f"   - New snapshot ID: {data.get('snapshot_id')}")
        print(f"   - Total poles: {data.get('summary', {}).get('poles')}")
        print(f"   - Total conductors: {data.get('summary', {}).get('conductors')}")
    else:
        print(f"❌ Failed to update progress: {response.status_code}")
    
    # 5. Get progress report
    print("\n5. Getting progress report...")
    response = requests.get(f"{BASE_URL}/api/as-built/{SITE}/progress-report")
    
    if response.status_code == 200:
        data = response.json()
        report = data.get('report', {})
        print(f"✅ Progress report retrieved")
        
        planned = report.get('planned', {})
        built = report.get('built', {})
        
        print(f"\n   Planned vs Built:")
        print(f"   - Poles: {built.get('poles', 0)}/{planned.get('poles', 0)}")
        print(f"   - Connections: {built.get('connections', 0)}/{planned.get('connections', 0)}")
        print(f"   - Conductors: {built.get('conductors', 0)}/{planned.get('conductors', 0)}")
        print(f"   - Length: {built.get('length_km', 0):.2f}/{planned.get('length_km', 0):.2f} km")
        
        status_summary = report.get('status_summary', {})
        if status_summary.get('poles_by_status'):
            print(f"\n   Poles by status code:")
            for code, count in status_summary['poles_by_status'].items():
                print(f"     SC1={code}: {count} poles")
    else:
        print(f"❌ Failed to get progress report: {response.status_code}")
    
    # 6. Export to Excel
    print("\n6. Testing Excel export...")
    response = requests.get(f"{BASE_URL}/api/as-built/{SITE}/export?format=excel")
    
    if response.status_code == 200:
        # Save the Excel file
        with open(f"test_as_built_{SITE}.xlsx", "wb") as f:
            f.write(response.content)
        print(f"✅ Excel export successful - saved as test_as_built_{SITE}.xlsx")
    else:
        print(f"❌ Failed to export Excel: {response.status_code}")
    
    # 7. List all snapshots
    print("\n7. Listing all snapshots...")
    response = requests.get(f"{BASE_URL}/api/as-built/{SITE}/snapshots")
    
    if response.status_code == 200:
        data = response.json()
        snapshots = data.get('snapshots', [])
        print(f"✅ Found {len(snapshots)} snapshots")
        for snapshot in snapshots:
            print(f"   - ID {snapshot['id']}: {snapshot['created_by']} ({snapshot['date']})")
            print(f"     Poles: {snapshot['poles']}, Connections: {snapshot['connections']}, Conductors: {snapshot['conductors']}")
    else:
        print(f"❌ Failed to list snapshots: {response.status_code}")
    
    print("\n=== As-Built API Testing Complete ===\n")

if __name__ == "__main__":
    test_as_built_endpoints()
