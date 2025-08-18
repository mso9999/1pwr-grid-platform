#!/usr/bin/env python3
"""
Test script for network editing API endpoints
Tests all CRUD operations for poles, connections, and conductors
"""

import requests
import json
import sys

BASE_URL = "http://localhost:8000"
SITE = "KET"

def test_api_endpoint(method, endpoint, data=None, expected_status=200):
    """Test an API endpoint and report results"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        elif method == "PUT":
            response = requests.put(url, json=data)
        elif method == "DELETE":
            response = requests.delete(url)
        else:
            return False, f"Unknown method: {method}"
        
        success = response.status_code == expected_status
        result = response.json() if response.content else {}
        
        return success, result
    except Exception as e:
        return False, str(e)

def main():
    print("=" * 60)
    print("NETWORK EDITING API TEST SUITE")
    print("=" * 60)
    
    # Test 1: Create a pole
    print("\n1. CREATE POLE TEST")
    pole_data = {
        "pole_type": "LV",
        "latitude": -30.055,
        "longitude": 27.885,
        "pole_class": "11M",
        "st_code_1": 0,
        "st_code_2": 0,
        "angle_class": "T",
        "notes": "Test pole from API test suite"
    }
    success, result = test_api_endpoint("POST", f"/api/network/poles/{SITE}", pole_data)
    test_pole_id = result.get("pole", {}).get("pole_id") if success else None
    print(f"   Result: {'✅ PASS' if success else '❌ FAIL'}")
    if success:
        print(f"   Created pole ID: {test_pole_id}")
    else:
        print(f"   Error: {result}")
    
    # Test 2: Update the pole
    print("\n2. UPDATE POLE TEST")
    if test_pole_id:
        update_data = {
            "st_code_1": 7,
            "notes": "Updated test pole - planted"
        }
        success, result = test_api_endpoint("PUT", f"/api/network/poles/{SITE}/{test_pole_id}", update_data)
        print(f"   Result: {'✅ PASS' if success else '❌ FAIL'}")
        if not success:
            print(f"   Error: {result}")
    else:
        print("   Result: ⏭️  SKIPPED (no pole to update)")
    
    # Test 3: Create a connection
    print("\n3. CREATE CONNECTION TEST")
    connection_data = {
        "latitude": -30.056,
        "longitude": 27.886,
        "pole_id": test_pole_id or "KET_17_GA100",
        "customer_name": "Test Customer",
        "st_code_3": 0,
        "meter_number": "TEST001",
        "notes": "Test connection from API test suite"
    }
    success, result = test_api_endpoint("POST", f"/api/network/connections/{SITE}", connection_data)
    test_connection_id = result.get("connection", {}).get("connection_id") if success else None
    print(f"   Result: {'✅ PASS' if success else '❌ FAIL'}")
    if success:
        print(f"   Created connection ID: {test_connection_id}")
    else:
        print(f"   Error: {result}")
    
    # Test 4: Create a conductor
    print("\n4. CREATE CONDUCTOR TEST")
    conductor_data = {
        "from_pole": test_pole_id or "KET_17_GA100",
        "to_pole": "KET_17_GA101",
        "conductor_type": "LV",
        "conductor_spec": "50",
        "st_code_4": 0,
        "notes": "Test conductor from API test suite"
    }
    success, result = test_api_endpoint("POST", f"/api/network/conductors/{SITE}", conductor_data)
    test_conductor_id = result.get("conductor", {}).get("conductor_id") if success else None
    print(f"   Result: {'✅ PASS' if success else '❌ FAIL'}")
    if success:
        print(f"   Created conductor ID: {test_conductor_id}")
    else:
        print(f"   Error: {result}")
    
    # Test 5: Update the conductor
    print("\n5. UPDATE CONDUCTOR TEST")
    if test_conductor_id:
        update_data = {
            "st_code_4": 5,
            "notes": "Updated test conductor - strung"
        }
        success, result = test_api_endpoint("PUT", f"/api/network/conductors/{SITE}/{test_conductor_id}", update_data)
        print(f"   Result: {'✅ PASS' if success else '❌ FAIL'}")
        if not success:
            print(f"   Error: {result}")
    else:
        print("   Result: ⏭️  SKIPPED (no conductor to update)")
    
    # Test 6: Split conductor
    print("\n6. SPLIT CONDUCTOR TEST")
    split_data = {
        "split_point": {"lat": -30.0555, "lng": 27.8855}
    }
    # Try with a known MV conductor
    success, result = test_api_endpoint("POST", f"/api/network/conductors/{SITE}/MV_0/split", split_data)
    print(f"   Result: {'✅ PASS' if success else '❌ FAIL'}")
    if not success:
        print(f"   Error: {result}")
        # Try alternative ID format
        print("   Retrying with alternative ID format...")
        success, result = test_api_endpoint("POST", f"/api/network/conductors/{SITE}/MV_1/split", split_data)
        print(f"   Retry Result: {'✅ PASS' if success else '❌ FAIL'}")
        if not success:
            print(f"   Error: {result}")
    
    # Test 7: Delete conductor
    print("\n7. DELETE CONDUCTOR TEST")
    if test_conductor_id:
        success, result = test_api_endpoint("DELETE", f"/api/network/conductors/{SITE}/{test_conductor_id}")
        print(f"   Result: {'✅ PASS' if success else '❌ FAIL'}")
        if not success:
            print(f"   Error: {result}")
    else:
        print("   Result: ⏭️  SKIPPED (no conductor to delete)")
    
    # Test 8: Delete connection
    print("\n8. DELETE CONNECTION TEST")
    if test_connection_id:
        success, result = test_api_endpoint("DELETE", f"/api/network/connections/{SITE}/{test_connection_id}")
        print(f"   Result: {'✅ PASS' if success else '❌ FAIL'}")
        if not success:
            print(f"   Error: {result}")
    else:
        print("   Result: ⏭️  SKIPPED (no connection to delete)")
    
    # Test 9: Delete pole
    print("\n9. DELETE POLE TEST")
    if test_pole_id:
        success, result = test_api_endpoint("DELETE", f"/api/network/poles/{SITE}/{test_pole_id}")
        print(f"   Result: {'✅ PASS' if success else '❌ FAIL'}")
        if not success:
            print(f"   Error: {result}")
    else:
        print("   Result: ⏭️  SKIPPED (no pole to delete)")
    
    # Get final network stats
    print("\n" + "=" * 60)
    print("NETWORK STATISTICS")
    print("=" * 60)
    success, result = test_api_endpoint("GET", f"/api/network/{SITE}")
    if success:
        data = result.get("data", {})
        print(f"   Poles: {len(data.get('poles', []))}")
        print(f"   Connections: {len(data.get('connections', []))}")
        print(f"   Conductors: {len(data.get('conductors', []))}")
        print(f"   Transformers: {len(data.get('transformers', []))}")
    
    print("\n" + "=" * 60)
    print("TEST SUITE COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()
